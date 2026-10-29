#!/usr/bin/env python3
"""Cooperative, cross-worktree Unity validation queue for macOS/Linux."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid


STALE_SECONDS = 900


def git(directory, *args):
    return subprocess.check_output(
        ["git", "-C", str(directory), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def common_directory(directory):
    result = Path(git(directory, "rev-parse", "--git-common-dir"))
    return (directory / result).resolve() if not result.is_absolute() else result.resolve()


def context(project):
    target = Path(project).expanduser().resolve()
    if not (target / "Assets").is_dir() or not (target / "ProjectSettings/ProjectVersion.txt").is_file():
        raise ValueError("目标必须是 Unity 工程目录，包含 Assets 和 ProjectSettings/ProjectVersion.txt")
    # Derive ownership from the target project, never from this skill's own repository.
    repository = Path(git(target, "rev-parse", "--show-toplevel")).resolve()
    common = common_directory(repository)
    workspace = repository
    try:
        current = Path.cwd()
        if common_directory(current) == common:
            workspace = Path(git(current, "rev-parse", "--show-toplevel")).resolve()
    except subprocess.CalledProcessError:
        pass
    key = hashlib.sha256(os.fsencode(target)).hexdigest()
    storage = common / "codex-unity-validation" / key
    return workspace, target, storage


@contextmanager
def locked_state(storage, project):
    storage.mkdir(parents=True, exist_ok=True)
    # This inode is permanent. Never unlink it: all processes must lock the same file.
    with (storage / "guard").open("a+") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        path = storage / "state.json"
        if path.exists():
            state = json.loads(path.read_text())
            if (state.get("version") != 1 or state.get("project") != str(project)
                    or not isinstance(state.get("queue"), list)
                    or not (state.get("holder") is None or isinstance(state.get("holder"), dict))):
                raise ValueError("占用记录格式异常；请保留文件并人工检查，不得删除后抢占")
        else:
            state = {"version": 1, "project": str(project), "holder": None, "queue": []}
        yield state
        # Atomic replacement protects the previous complete state if a process crashes.
        fd, temporary = tempfile.mkstemp(prefix="state-", suffix=".tmp", dir=storage)
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(state, output, ensure_ascii=False, indent=2)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def require_holder(state, token):
    if state["holder"] is None or state["holder"]["token"] != token:
        raise ValueError("token 与当前占用者不符；未改变占用状态")
    return state["holder"]


def operate(state, args, workspace):
    now = time.time()
    if args.command == "status":
        holder = state["holder"]
        age = max(0, int(now - holder["updated_at"])) if holder else None
        return 0, {"status": "occupied" if holder else "idle", **state,
                   "heartbeat_age_seconds": age,
                   "needs_owner_check": age is not None and age >= STALE_SECONDS}

    if args.command == "acquire":
        if args.ticket:
            entry = next((item for item in state["queue"] if item["ticket"] == args.ticket), None)
            if entry is None:
                raise ValueError("排队 ticket 不存在；若已取得占用权，请使用 token 执行 check 或 heartbeat")
        else:
            if not args.owner or not args.owner.strip() or not args.purpose or not args.purpose.strip():
                raise ValueError("首次申请必须填写 --owner 对话标识和 --purpose 用途")
            # Repeating an initial request does not create duplicate queue entries.
            entry = next((item for item in state["queue"]
                          if item["owner"] == args.owner and item["workspace"] == str(workspace)), None)
            if entry is None:
                if (state["holder"] and state["holder"]["owner"] == args.owner
                        and state["holder"]["workspace"] == str(workspace)):
                    raise ValueError("此对话已占用工程；请使用原 token，不要重复申请")
                entry = {"ticket": uuid.uuid4().hex, "owner": args.owner,
                         "purpose": args.purpose, "workspace": str(workspace), "requested_at": now}
                state["queue"].append(entry)
        if state["holder"] is None and state["queue"][0] is entry:
            state["queue"].pop(0)
            state["holder"] = {**entry, "token": entry["ticket"], "acquired_at": now, "updated_at": now}
            return 0, {"status": "acquired", "project": state["project"], **state["holder"]}
        return 2, {"status": "queued", "ticket": entry["ticket"],
                   "position": state["queue"].index(entry) + 1, "holder": state["holder"],
                   "message": "尚未取得占用权；保留 ticket，稍后 acquire --ticket 重试"}

    if args.command in ("check", "heartbeat"):
        holder = require_holder(state, args.token)
        holder["updated_at"] = now
        return 0, {"status": "owned", "project": state["project"], **holder}

    if args.command == "release":
        holder = require_holder(state, args.token)
        state["holder"] = None
        return 0, {"status": "released", "owner": holder["owner"], "next": state["queue"][:1]}

    if args.command == "cancel":
        entry = next((item for item in state["queue"] if item["ticket"] == args.ticket), None)
        if entry is None:
            raise ValueError("排队 ticket 不存在；cancel 不能释放正在使用的工程")
        state["queue"].remove(entry)
        return 0, {"status": "cancelled", "ticket": args.ticket}

    if args.command == "recover":
        holder = require_holder(state, args.token)
        if not args.confirm_owner_stopped or not args.reason.strip():
            raise ValueError("必须确认原对话和相关 Unity 操作均已停止，并提供 --reason")
        state["last_recovery"] = {"owner": holder["owner"], "token": holder["token"],
                                  "reason": args.reason, "recovered_at": now}
        state["holder"] = None
        return 0, {"status": "recovered", **state["last_recovery"], "next": state["queue"][:1]}
    raise ValueError("未知操作")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", required=True, help="目标 Editor 打开的 Unity 工程路径")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="查看占用者与先到先得的队列")
    acquire = commands.add_parser("acquire", help="申请占用权，排队时退出码为 2")
    acquire.add_argument("--owner", help="稳定且唯一的对话 ID，可附加 Bug 名称")
    acquire.add_argument("--purpose", help="本次写入或验证的用途")
    acquire.add_argument("--ticket", help="使用先前返回的排队 ticket 重试")
    for name in ("check", "heartbeat", "release"):
        command = commands.add_parser(name)
        command.add_argument("--token", required=True)
    cancel = commands.add_parser("cancel", help="退出等待队列")
    cancel.add_argument("--ticket", required=True)
    recover = commands.add_parser("recover", help="确认原任务停止后人工回收，绝不因超时自动抢占")
    recover.add_argument("--token", required=True)
    recover.add_argument("--reason", required=True)
    recover.add_argument("--confirm-owner-stopped", action="store_true")
    return result


def main():
    args = parser().parse_args()
    try:
        workspace, project, storage = context(args.project)
        with locked_state(storage, project) as state:
            code, response = operate(state, args, workspace)
        response["state_file"] = str(storage / "state.json")
        response["time_utc"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return code
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
