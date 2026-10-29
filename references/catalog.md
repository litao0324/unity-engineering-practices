# 规范目录

使用本目录选择规范。只加载与当前任务直接相关的文件。

| 主题 | 规范文件 | 适用任务 |
| --- | --- | --- |
| 埋点与分析数据 | [analytics-and-telemetry.md](analytics-and-telemetry.md) | 业务分析事件、参数、公共属性、用户属性；触发时机、累计与重置、归因、防重复、兼容及分层上报验证 |
| 项目变更 | [project-change-workflow.md](project-change-workflow.md) | 实际修改、重构、缺陷修复、代码或资源审查；功能影响确认、主动自测、证据记录、用户验收交付、提交前收口和 Git 提交信息 |
| 测试数据与夹具 | [test-data-and-fixtures.md](test-data-and-fixtures.md) | 临时测试数据、隔离实例、真实读取来源、新局/快照路径及测试后恢复 |
| 状态与表现隔离 | [state-and-presentation.md](state-and-presentation.md) | 逻辑/视觉集合、异步交互容量、随机外观、稳定身份及刷新/撤销/续关一致性 |
| 原生插件 | [native-plugin-integration.md](native-plugin-integration.md) | 含原生库的 SDK 接入、平台依赖与导入、二进制重建、完整构建和设备验证边界 |
| 对象池 | [object-pooling.md](object-pooling.md) | 判断是否池化；设计、实现或审查对象池；排查复用状态、容量、生命周期和性能问题 |
| 资源与生成文件 | [assets-and-generated-files.md](assets-and-generated-files.md) | 新增、移动、重命名、删除或迁移 Unity 资源；处理 `.meta`、GUID、资源索引和生成结果 |
| QAssets 生成 | [qframework-reskit-generation.md](qframework-reskit-generation.md) | 已使用 QFramework ResKit/QAssets 的项目：资源标记、资源名常量生成、常量缺失、动态加载和对象池资源 |
| 状态持久化 | [statusutil-es3-persistence.md](statusutil-es3-persistence.md) | 已使用 StatusConfig/StatusUtil/ES3 Cache 的项目：默认值、新增字段、生成属性、存档兼容和批量保存 |
| UIKit 面板创建 | [qframework-uikit-panel-creation.md](qframework-uikit-panel-creation.md) | 已使用 QFramework UIKit 的项目：面板/弹窗命名、设置窗口、创建 Prefab/脚本/Designer、绑定生成与验收 |
| UI 与 Prefab | [ui-and-prefab.md](ui-and-prefab.md) | 新增或修改面板、弹窗、Prefab 层级、绑定字段、布局、交互和复用组件；既有实现替换依据、迁入后的外观调整；效果图 100% 复刻、运行截图对照与适配验收 |
| 动效生命周期 | [animation-and-effects.md](animation-and-effects.md) | 接入或审查 Tween、Animator、Animation、Spine、粒子、循环特效和飞行动效 |
| 本地化 | [localization.md](localization.md) | 新增或修改玩家文本、语言 Key、翻译数据、占位符、Fallback、动态刷新和 RTL |
| 功能迁移 | [feature-migration.md](feature-migration.md) | 在两个 Unity 项目间迁移功能、资源、Prefab、配置、状态和验证链路及迁入后的实现调整；保持视觉基线与适配一致 |
| 规范维护 | [practice-authoring.md](practice-authoring.md) | 新增、拆分、合并或修订共享最佳实践 |

目录中未登记的主题代表本库尚未形成正式规范。此时可以使用一般 Unity 工程知识，但不要声称结论来自本库。
