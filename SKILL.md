---
name: unity-engineering-practices
description: Apply shared Unity engineering practices when planning, implementing, reviewing, refactoring, debugging, profiling, migrating, or validating Unity projects. Use for Unity 架构设计、功能实现、代码审查、性能优化、问题修复、跨项目迁移，以及对象池、资源与 .meta、生成文件、UI/Prefab、本地化、动效生命周期、内存、渲染和项目结构等决策。 Also covers QFramework ResKit/QAssets 生成、StatusConfig/StatusUtil/ES3 状态持久化、UIKit 面板创建，以及本库规范维护。 Do not use for non-Unity work.
---

# Unity Engineering Practices

## Goal

在不同 Unity 项目中一致地应用可复用工程规范，同时保留项目约束、证据和合理例外。

## Workflow

1. 读取项目根目录及当前工作目录适用的 `AGENTS.md`；若不存在，继续执行，不要臆造项目规则。
2. 仅在任务需要时检查 Unity 版本、目标平台、渲染管线、包依赖和现有架构。
3. 阅读 [规范目录](references/catalog.md)，选择与当前任务直接相关的规范。
4. 阅读对应规范全文；不要仅根据标题或常识推断其中要求。
5. 区分 `MUST`、`SHOULD`、`CONSIDER` 和 `AVOID`，结合项目证据应用规则。
6. 修改或审查完成后，执行对应规范中的检查清单。
7. 简要报告适用的关键规则、验证结果，以及所有有意偏离和残余风险。

## Precedence

按以下优先级解决冲突：

1. 用户当前任务中的明确要求。
2. 项目 `AGENTS.md` 中的项目约束和例外。
3. 本库中的 `MUST` 规则。
4. 本库中的 `SHOULD`、`CONSIDER` 和 `AVOID` 指引。

不要静默忽略冲突。若高优先级要求导致偏离共享规范，说明偏离内容和影响。

## Requirement Levels

- `MUST`：默认必须遵守；只有更高优先级约束才能覆盖。
- `SHOULD`：默认遵守；偏离时给出与当前项目相关的理由。
- `CONSIDER`：根据频率、规模、平台、维护成本和测量结果判断。
- `AVOID`：默认视为反模式；采用时说明收益为何大于风险。

## Reference Routing

- 涉及仓库中的实际修改、重构、缺陷修复或变更审查时，阅读 [项目变更工作流](references/project-change-workflow.md)。
- 涉及对象创建/销毁频率、复用、预热、容量、状态重置、粒子、投射物、敌人或 UI 复用时，阅读 [对象池规范](references/object-pooling.md)。
- 涉及 Unity 资源、`.meta`、GUID、导入设置、资源索引或自动生成文件时，阅读 [资源与生成文件规范](references/assets-and-generated-files.md)。
- 项目使用 QFramework ResKit/QAssets，且涉及资源标记、常量缺失、资源新增/移动/重命名或动态加载时，阅读 [QAssets 生成](references/qframework-reskit-generation.md)。
- 项目使用 StatusConfig → StatusUtil 生成属性 → ES3 Cache 链路，且涉及新增、修改、审查或使用持久化状态时，阅读 [状态持久化](references/statusutil-es3-persistence.md)。
- 项目使用 QFramework UIKit，且涉及创建面板、弹窗、Prefab/Designer 配对或创建流程审查时，阅读 [UIKit 面板创建](references/qframework-uikit-panel-creation.md)。
- 涉及 UI 面板、弹窗、Prefab 层级、组件绑定、布局、交互或效果图复刻时，阅读 [UI 与 Prefab 规范](references/ui-and-prefab.md)，有明确效果图时执行其中的 100% 复刻与适配验收要求。
- 涉及 Tween、Animator、Animation、Spine、粒子、飞行动效或其他表现流程时，阅读 [动效生命周期规范](references/animation-and-effects.md)。
- 涉及玩家可见文本、语言 Key、翻译表、占位符、语言切换或 RTL 时，阅读 [本地化规范](references/localization.md)。
- 涉及在 Unity 项目之间复制、移植或重建功能时，阅读 [跨项目功能迁移规范](references/feature-migration.md)；涉及 UI 视觉时同时按 [UI 与 Prefab 规范](references/ui-and-prefab.md) 验收。
- 添加、拆分或修订本库规范时，阅读 [规范编写标准](references/practice-authoring.md)。

如果目录中没有覆盖当前主题的规范，使用一般 Unity 工程判断继续工作，并明确说明“共享规范库尚未覆盖该主题”；不要把临时判断伪装成本库规则。

## Guardrails

- 不要为了形式统一而替换已经可靠运行的项目方案。
- 不要在缺少测量或明确规模依据时声称某项优化一定必要。
- 不要一次加载无关规范；保持上下文聚焦于当前任务。
- 不要把示例、启发式建议或个人偏好提升为强制规则。
- 不要因项目缺少信息而停止全部工作；先执行安全且与缺失信息无关的部分，再列出会影响结论的未知项。

## Maintaining This Skill

修改规范库时：

1. 按 [规范编写标准](references/practice-authoring.md) 编写或修订规范。
2. 在本文件的 `Reference Routing` 中增加直接入口。
3. 在 [规范目录](references/catalog.md) 中登记主题和适用任务。
4. 检查新规则是否与现有规则、项目覆盖机制或优先级冲突。
5. 使用正向、反向和边界任务验证触发与执行效果。
