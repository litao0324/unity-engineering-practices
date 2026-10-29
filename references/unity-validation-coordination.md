# 多对话协作与 Editor 独占

## Purpose

避免多个修复任务争用同一 Unity Editor，或由工程文件写入、重新编译、场景切换和共享测试状态使验证失效。实际功能验证与交付继续执行 [项目变更工作流](project-change-workflow.md)，存档和临时数据处理见 [测试数据与夹具](test-data-and-fixtures.md)。

## Applies When

- 多个对话、进程或 Worktree 需要使用同一 Unity Editor。
- 一个任务运行验证时，另一个任务可能修改该 Editor 对应工程的代码、资源或配置。
- 多个独立 Editor 仍共享测试存档、账号或外部可变状态。

## Does Not Apply When

- 单任务独占环境，且没有其他写入者。
- 纯源码阅读、独立目录文件修改或无共享状态的测试；不要求这些工作排队等待 Editor。

## Decision Process

1. 核对各任务实际工作目录、Editor 工程路径、MCP 实例和测试状态来源；同一分支名不能证明目录或环境相同。
2. 优先在独立 Worktree 内并行修改，共用验证工程按顺序合入和验证。是否新建 Worktree 按用户及项目约定决定，不自动搬迁已有任务。
3. 采用项目已有协调设施；缺少设施时可使用本库的占用工具。明确所有写入者及人工操作是否接入，不能只协调 Play 按钮。
4. 取得占用权后准备环境、复现、验证、记录证据、恢复本次改变的状态，再释放；排队时继续不依赖该环境的工作。

## MUST

- 多任务共享同一 Editor 时，必须协调其状态变更和对应工程文件写入；操作前核对真实工程路径与目标实例。不能把其他 Worktree 的源码检查或运行结果当作当前工程的验证。
- 使用占用机制时，必须原子申请，并覆盖完整验证周期；共用工程目录内的文件保存、资源生成与 Git 合入也纳入同一协调范围，避免“检查空闲后再操作”的竞态。
- 只有取得占用权的任务可以进行受保护操作；凭据只用于本任务取得的占用。恢复中断任务前重新检查，失效则停止操作并重新排队。
- 不因心跳过期自动抢占、删除锁文件或停止另一个任务的运行。异常回收必须先核实原任务及其已发出的 Editor 操作均已停止，记录原因；无人领取的排队项经确认后取消。
- 释放前恢复本次临时注入、场景及存档改动，不覆盖用户原有状态；需要保留现场时继续持有并说明原因。
- 明确协调机制的实际覆盖范围；仅有规则和占用脚本不能宣称已在 MCP 或 Editor 入口强制拦截。旧对话及旧 Worktree 须显式接入，不能假定自动生效。

## SHOULD

- 使用独立目录并行修复，尽量只保留一个验证工程；多修复合入后检查交叉影响。
- 每个修复提供可执行的验收记录，包括前置状态、真实入口、操作、预期结果、已验证及未验证项。
- 不再等待时取消排队，不让失联队首长期阻塞后续任务。

## Tool

提供 `../scripts/unity_validation.py`，适用于 macOS/Linux、Python 3.9 及以上、Git 管理的工程。使用标准库 `fcntl` 串行更新记录，按目标工程规范化路径区分占用，各 Worktree 共用目标仓库的 Git 管理目录。不能协调彼此独立的 Git 克隆或跨机器共享服务；这些情况需另行协调实际共享状态。

从使用方工作目录执行，`<skill>` 替换为实际 Skill 路径，`<project>` 为目标 Editor 的真实工程目录；每次命令均传入相同的 `--project`，位于子命令前：

```sh
python3 <skill>/scripts/unity_validation.py --project '<project>' status
python3 <skill>/scripts/unity_validation.py --project '<project>' acquire --owner '唯一对话ID' --purpose '本次用途'
python3 <skill>/scripts/unity_validation.py --project '<project>' acquire --ticket '排队ticket'
python3 <skill>/scripts/unity_validation.py --project '<project>' check --token '本任务token'
python3 <skill>/scripts/unity_validation.py --project '<project>' heartbeat --token '本任务token'
python3 <skill>/scripts/unity_validation.py --project '<project>' release --token '本任务token'
python3 <skill>/scripts/unity_validation.py --project '<project>' cancel --ticket '排队ticket'
```

- `acquire` 退出码为 `0` 且 `status=acquired` 才可操作；`2` 和 `queued` 表示仍在等待；`1` 表示失败，不可绕过。
- 队首主动凭 ticket 重试领取，不自动启动下一对话，也不创建后台定时任务。分段等待，避免频繁轮询；结束当前工作前领取或取消排队。
- `check` 同时更新心跳，每次受保护操作前执行；耗时工作期间建议至少每五分钟更新。十五分钟无心跳仅提示核实，不自动过期。
- 状态位于目标仓库共用 Git 管理目录的 `codex-unity-validation/` 中。不得删除永久 `guard` 文件；状态异常时保留现场，失败关闭。
- token 是协作凭据，不是对本机其他进程的安全隔离；本工具不拦截直接 MCP、手动 Editor 操作或普通文件写入。

确认原任务及未完成的 Editor 操作已停止后，才能人工回收：

```sh
python3 <skill>/scripts/unity_validation.py --project '<project>' recover --token '原占用token' --reason '已核实的回收原因' --confirm-owner-stopped
```

项目可保留只配置默认工程路径并转发到本工具的薄入口，不复制工具实现。更新时保留已有状态目录及格式，验证旧 token 仍然有效；旧副本未接入时不得宣称覆盖全部任务。

## Validation

- [ ] 已确认工作目录、目标工程、Editor 实例和共享测试状态。
- [ ] 相同目标的并发申请只有一个成功，后续按先到先得顺序领取。
- [ ] 工程写入与完整验证周期均受协调，独立目录工作无需等待。
- [ ] 中断恢复、旧 token、失联队首及状态异常不会造成隐式抢占。
- [ ] 已恢复本次测试状态，或明确说明保留现场及持有原因。
- [ ] 已披露工具平台、接入范围和未验证的实际 Editor 交接。

本库工具测试使用临时 Git 仓库和独立进程，不操作真实 Editor 或使用方排队记录：

```sh
python3 -B -m unittest discover -s <skill>/tests -p 'test_unity_validation.py' -v
```

## Validation Cases

- 正向：多个修复任务共用一个 Editor，一个任务验证时其他任务切场景或保存脚本。应协调工程写入和完整验证周期，不只为单次 Play 调用上锁。
- 反向：不同目录里的纯逻辑测试没有共享存档或服务。允许独立执行，不强制占用 Editor。
- 边界：原任务无心跳，但测试仍在执行。只能核实状态，不能按时间自动抢占；多个 Editor 共享存档时，按真实存档入口另行隔离或协调。
- 跨项目：Unity 工程可位于仓库根目录或任意子目录，且版本不同。以实际路径选择目标，通用工具不硬编码产品目录或 Unity 版本。
