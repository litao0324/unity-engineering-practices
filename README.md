# Unity Engineering Practices

可跨 Unity 项目复用的工程规范与协作工具。智能体入口为 [SKILL.md](SKILL.md)，规范目录见 [references/catalog.md](references/catalog.md)。

## 正式版本

- [发布说明](CHANGELOG.md)记录每个版本的变化与迁移影响。
- [GitHub Releases](https://github.com/litao0324/unity-engineering-practices/releases)提供已发布版本的标签和说明。
- 首个正式版本为 `v1.0.0`。版本以 Git 附注标签为准，不另维护容易失配的版本文件。
- `Unreleased` 只记录尚未发布的变化；发布后将对应内容归入带版本号和日期的独立条目。

版本号采用 `v主版本.次版本.修订版本`：

| 变化 | 版本递增 |
| --- | --- |
| 修正文案、链接或工具缺陷，保持已有规则与接口兼容 | 修订版本，例如 `v1.0.1` |
| 新增可选规范或兼容功能，不要求已有使用方改变流程 | 次版本，例如 `v1.1.0` |
| 新增、删除或收紧 MUST，改变已有使用方必须遵守的行为，或工具接口不兼容 | 主版本，例如 `v2.0.0` |

每个正式版本都要说明迁移影响。已发布的标签与说明不移动、不覆盖，修正通过后续版本发布。

## 查看项目使用的版本

在使用方项目根目录执行，以下路径按实际集成位置调整：

```sh
git -C .agents/skills/unity-engineering-practices fetch origin --tags
git submodule status -- .agents/skills/unity-engineering-practices
git -C .agents/skills/unity-engineering-practices describe --tags --exact-match HEAD
git -C .agents/skills/unity-engineering-practices status --short
```

精确匹配时会显示 `v1.0.0` 这样的版本号；匹配失败表示当前检出的提交不是正式发布版本。还需检查子仓库是否有未提交改动。`git submodule status` 前缀为 `+` 时表示工作区检出的提交与主项目记录不同，`-` 表示尚未初始化，`U` 表示有冲突，空格表示一致。

## 升级项目使用的版本

先阅读目标版本的发布说明并确认子仓库工作区干净，再显式选择版本。以下以 `v1.0.0` 为例：

```sh
git -C .agents/skills/unity-engineering-practices fetch origin --tags
git -C .agents/skills/unity-engineering-practices switch --detach v1.0.0
git diff --submodule=log -- .agents/skills/unity-engineering-practices
git add .agents/skills/unity-engineering-practices
git commit -m 'chore: 更新共享 Unity 工程规范至 v1.0.0'
```

主项目记录的是标签对应的提交，而非自动追踪分支。其他项目不会随共享库发布自动升级。使用方的验证排队和 Git 提交约束继续适用。

## 发布新版本

在共享库中完成以下操作：

1. 将 `Unreleased` 中已完成的内容移到 `## [版本号] - YYYY-MM-DD` 标题下，保留空的 `Unreleased` 区域。日期使用实际发布日期，说明变化和迁移影响。
2. 按变更范围完成自测并提交；确认工作区干净，待发布提交已进入远端 `main`。提交说明不使用英文或中文圆括号。
3. 为该提交创建附注标签并推送。以下为首个版本的示例，后续发布须替换版本号及说明：

```sh
git tag -a v1.0.0 -m 'release: 发布共享 Unity 工程规范 v1.0.0'
git push origin refs/tags/v1.0.0
```

4. 检查 GitHub Actions 的“发布正式版本”运行结果，以及对应的 GitHub Release。工作流会校验标签并从同一提交的 `CHANGELOG.md` 提取完整版本说明，使用仓库自带的令牌创建 Release，无需额外配置发布凭据。

标签推送成功不代表 Release 已生成；以工作流成功和 Release 页面可见为准。工作流失败时先查看原因：网络或权限问题解决后可重新运行；如标签中的说明或内容有误，应发布新的版本，不覆盖旧标签。
