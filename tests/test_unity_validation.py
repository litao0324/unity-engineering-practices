"""Exercise separate processes against disposable repositories, never the live Editor."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/unity_validation.py"


class ValidationQueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="unity-validation-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "main repo"
        self.root.mkdir()
        self.git("init")
        self.project = self.root / "Client/Game"
        (self.project / "Assets").mkdir(parents=True)
        (self.project / "Assets/.gitkeep").touch()
        (self.project / "ProjectSettings").mkdir()
        (self.project / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.62f2\n")
        (self.root / "tools").mkdir()
        self.script = self.root / "tools/unity_validation.py"
        shutil.copyfile(SOURCE, self.script)
        self.git("add", ".")
        self.git("-c", "user.name=Queue Test", "-c", "user.email=queue@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "test: temporary fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE, text=True)

    def command(self, *args, code=0, script=None, project=None, cwd=None):
        command = [sys.executable, "-B", str(script or self.script),
                   "--project", str(project if project is not None else self.project)]
        result = subprocess.run(command + list(args), capture_output=True, text=True, cwd=cwd)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout if code != 1 else result.stderr)

    def acquire(self, owner, **kwargs):
        return self.command("acquire", "--owner", owner, "--purpose", "测试用途", **kwargs)

    def make_worktree(self):
        path = Path(self.temporary.name) / "bug worktree"
        self.git("worktree", "add", "--detach", str(path), "HEAD")
        return path

    def test_lifecycle_and_wrong_token(self):
        first = self.acquire("chat-A")
        self.assertEqual(first["status"], "acquired")
        self.command("release", "--token", "wrong", code=1)
        status = self.command("status")
        self.assertEqual(status["holder"]["token"], first["token"])
        self.command("check", "--token", first["token"])
        self.command("heartbeat", "--token", first["token"])
        self.command("release", "--token", first["token"])
        self.assertEqual(self.command("status")["status"], "idle")
        self.command("check", "--token", first["token"], code=1)

    def test_fifo_no_new_arrival_can_jump_queue(self):
        first = self.acquire("chat-A")
        second = self.acquire("chat-B", code=2)
        self.command("release", "--token", first["token"])
        third = self.acquire("chat-C", code=2)
        self.assertEqual(third["position"], 2)
        self.command("acquire", "--ticket", third["ticket"], code=2)
        acquired = self.command("acquire", "--ticket", second["ticket"])
        self.assertEqual(acquired["owner"], "chat-B")
        self.command("release", "--token", acquired["token"])
        self.assertEqual(self.command("acquire", "--ticket", third["ticket"])["owner"], "chat-C")

    def test_repeated_initial_request_does_not_duplicate(self):
        first = self.acquire("chat-A")
        second = self.acquire("chat-B", code=2)
        again = self.acquire("chat-B", code=2)
        self.assertEqual(second["ticket"], again["ticket"])
        self.assertEqual(len(self.command("status")["queue"]), 1)
        self.acquire("chat-A", code=1)
        self.assertEqual(self.command("status")["holder"]["token"], first["token"])

    def test_cancel_does_not_release_holder(self):
        first = self.acquire("chat-A")
        second = self.acquire("chat-B", code=2)
        self.command("cancel", "--ticket", first["token"], code=1)
        self.command("cancel", "--ticket", second["ticket"])
        self.assertEqual(self.command("status")["queue"], [])
        self.command("acquire", "--ticket", second["ticket"], code=1)

    def test_stale_heartbeat_never_allows_takeover(self):
        first = self.acquire("chat-A")
        path = Path(first["state_file"])
        state = json.loads(path.read_text())
        state["holder"]["updated_at"] = 1
        path.write_text(json.dumps(state))
        self.assertTrue(self.command("status")["needs_owner_check"])
        self.acquire("chat-B", code=2)
        self.assertEqual(self.command("status")["holder"]["token"], first["token"])

    def test_recovery_requires_confirmation_and_invalidates_old_token(self):
        first = self.acquire("chat-A")
        second = self.acquire("chat-B", code=2)
        self.command("recover", "--token", first["token"], "--reason", "已核实", code=1)
        self.command("recover", "--token", first["token"], "--reason", " ",
                     "--confirm-owner-stopped", code=1)
        self.command("recover", "--token", first["token"], "--reason", "已核实原任务和 Editor 均停止",
                     "--confirm-owner-stopped")
        self.command("acquire", "--ticket", second["ticket"])
        for operation in ("check", "heartbeat", "release"):
            self.command(operation, "--token", first["token"], code=1)
        self.assertEqual(self.command("status")["last_recovery"]["owner"], "chat-A")

    def test_concurrent_processes_have_exactly_one_holder(self):
        processes = [subprocess.Popen(
            [sys.executable, "-B", str(self.script), "--project", str(self.project),
             "acquire", "--owner", f"chat-{index}",
             "--purpose", "并发申请"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) for index in range(12)]
        responses = []
        for process in processes:
            output, errors = process.communicate(timeout=30)
            self.assertIn(process.returncode, (0, 2), errors)
            responses.append(json.loads(output))
        self.assertEqual(sum(item["status"] == "acquired" for item in responses), 1)
        status = self.command("status")
        self.assertEqual(len(status["queue"]), 11)
        self.assertEqual(len({item["ticket"] for item in status["queue"]}), 11)

    def test_worktrees_share_queue_for_same_target_editor(self):
        worktree = self.make_worktree()
        first = self.acquire("chat-A")
        other = self.acquire("chat-B", script=worktree / "tools/unity_validation.py", code=2)
        self.assertEqual(other["holder"]["token"], first["token"])
        self.assertEqual(other["state_file"], first["state_file"])
        self.assertEqual(other["holder"]["workspace"], str(self.root.resolve()))

    def test_different_editor_projects_have_independent_queues(self):
        worktree = self.make_worktree()
        main = self.acquire("chat-A")
        other = self.acquire("chat-B", project=worktree / "Client/Game")
        self.assertEqual(other["status"], "acquired")
        self.assertNotEqual(main["state_file"], other["state_file"])
        self.assertEqual(self.command("status")["holder"]["owner"], "chat-A")

    def test_absolute_helper_records_calling_worktree(self):
        worktree = self.make_worktree()
        first = self.acquire("chat-A", cwd=worktree)
        self.assertEqual(first["workspace"], str(worktree.resolve()))
        self.assertEqual(first["project"], str(self.project.resolve()))

    def test_symlink_alias_cannot_bypass_lock(self):
        alias = Path(self.temporary.name) / "project alias"
        alias.symlink_to(self.project, target_is_directory=True)
        first = self.acquire("chat-A")
        other = self.acquire("chat-B", project=alias, code=2)
        self.assertEqual(first["state_file"], other["state_file"])

    def test_corrupt_state_fails_closed(self):
        first = self.acquire("chat-A")
        path = Path(first["state_file"])
        path.write_text("{broken")
        self.acquire("chat-B", code=1)
        self.assertEqual(path.read_text(), "{broken")

    def test_missing_parameters_and_invalid_projects_fail(self):
        self.command("acquire", code=1)
        self.command("status", project=self.root, code=1)
        self.command("acquire", "--ticket", "missing", code=1)
        self.assertIsNone(self.command("status")["holder"])

    def test_runtime_state_does_not_dirty_repository(self):
        self.acquire("chat-A")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_unity_project_at_repository_root_and_other_unity_version(self):
        (self.root / "Assets").mkdir()
        (self.root / "ProjectSettings").mkdir()
        (self.root / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.0.0f1\n")
        acquired = self.acquire("root-project", project=self.root)
        self.assertEqual(acquired["project"], str(self.root.resolve()))
        self.assertIn(str(self.root.resolve() / '.git'), acquired["state_file"])


if __name__ == "__main__":
    unittest.main()
