# 资源与生成文件规范

## Purpose

保持 Unity 资源身份、序列化引用、导入设置和生成链路一致，避免出现 Missing Reference、错误资源、白图、粉色材质、重复定义或仅在 Editor 中可用的问题。

## Applies When

- 新增、复制、移动、重命名、删除或跨项目迁移 Unity 资源。
- 修改 Prefab、Scene、Material、Shader、动画、图集、音频或 ScriptableObject。
- 项目通过配置、表格、资源标记或 Editor 工具生成代码、索引、常量或绑定文件。

## Decision Process

1. 识别资源及其完整依赖闭包。
2. 确认项目以 GUID、直接序列化、Resources、Addressables、AssetBundle 或其他系统加载资源。
3. 找到生成源、生成器和生成结果之间的关系。
4. 使用项目既有编辑器或生成流程完成修改。
5. 验证 GUID、导入、索引、运行时加载和最终表现。

## MUST

- Unity 资源文件与对应 `.meta` 必须作为一个身份单元处理；移动、复制、删除和提交时保持成对。
- 修改或替换 GUID 前必须搜索冲突和反向引用，并验证所有序列化引用已经同步。
- 跨项目迁移必须带上完整依赖闭包，包括嵌套 Prefab、材质、Shader、贴图、动画、音频、字体和配置。
- 项目存在生成源和生成器时，必须修改生成源并重新生成；不要长期手改生成结果。
- 生成后必须检查重复定义、缺失条目、意外大范围改动和已经删除内容的残留引用。
- 动态加载资源必须使用项目既有的稳定标识来源，例如生成常量、配置 ID、AssetReference 或统一枚举；不要散落容易拼错的路径和名称字符串。
- 必须在项目实际使用的加载模式中验证资源；Editor 专用定位方式不能代替最终运行时加载方案。

## SHOULD

- 应该优先让 Unity Editor 或官方序列化 API 保存 Prefab、Scene 和复杂资源。
- 应该在修改前记录资源路径、GUID、导入设置、所属图集或资源组以及主要引用者。
- 应该沿用相邻资源的目录、命名、压缩、平台覆盖和打包分组方式。
- 应该把资源内容、`.meta`、生成索引和使用方作为同一组变更审查。
- 应该把第三方资源视为独立边界，除非任务明确要求，不直接修改其源文件。

## CONSIDER

- 目标项目已有同名或同功能资源时，考虑复用或合并，而不是直接覆盖。
- 保留源 GUID 能减少引用改写，但只有确认目标项目不存在冲突时才采用。
- 资源系统不支持新场景时，考虑扩展其生成源或配置模型，不在业务层建立第二套标识体系。

## AVOID

- 避免只复制可见主资源而遗漏不可见依赖。
- 避免手工拼接复杂 Prefab 或 Scene YAML；确实必须手改时，验证 fileID、父子关系、组件关系和外部 GUID 闭合。
- 避免通过隐藏错误节点、替换默认材质或增加 Editor fallback 掩盖缺失引用。
- 避免提交 `.csproj`、缓存或其他可重新生成文件，除非项目明确要求且差异必要。

## Prefab and Import Checks

以下是资源引用闭合的具体检查方式；普通资源改动不意味着必须手改 YAML：

- 优先在 Unity 中加载 Prefab contents、实例化嵌套对象、设置层级和引用、保存并卸载，再重新导入。
- 必须手改 YAML 时，核对 `m_SourcePrefab` GUID、唯一的本地 fileID、stripped 对象及组件引用、外层 `m_AddedGameObjects` 登记、`m_Modifications` 的源对象 target；检查 `m_Children` / `m_Father`、`m_GameObject` / `m_Component` 双向闭合，保持 Unity 原有空格缩进。只迁入半棵子树或残缺对象块不能通过检查。
- 本地 fileID 必须解析到对应对象块或明确的嵌套源对象。Broken PPtr 按缺失 fileID 去重后追源，不因根节点可打开就忽略错误。
- 修改 GUID 时检查全部反向引用、旧 GUID 残留和新 GUID 冲突，并回归目标项目原有使用者。
- Sprite 检查导入模式、Pixels Per Unit、Border、裁切、子 Sprite fileID、图集收录与打包依赖；材质检查 Shader、include、依赖 Shader 和贴图，动画检查 Clip/Controller 引用。
- 绑定检查字段名/类型、脚本 GUID、必填引用，以及 partial 中重复字段/生命周期方法；重新生成后字段不能丢失或重复。
- 新建或修改后检查最终加载出的节点（包括默认隐藏状态）、继承和覆盖；静态引用检查不替代运行表现验收。

## Validation Cases

- 正向：迁移嵌套 Prefab 子树，核对新增对象登记、源 fileID、绑定和完整依赖，再让 Unity 导入并验证最终实例。
- 反向：只改业务计算逻辑，没有序列化资源变化，不机械重写 GUID、Prefab 或图集。
- 边界：源资源含无法解析的引用，先记录缺口并追溯来源，不删除可见节点或套默认材质制造通过。

## Validation

- [ ] 资源文件与 `.meta` 成对存在，GUID 无冲突。
- [ ] 外部 GUID、嵌套 Prefab 和序列化字段都能解析。
- [ ] 导入设置、平台覆盖、图集或资源组符合项目约定。
- [ ] 已通过正确生成源重新生成索引、常量或绑定。
- [ ] 生成差异没有重复定义、缺失条目或无关内容。
- [ ] Editor 导入无新增 Missing、Broken PPtr 或 Shader 错误。
- [ ] 实际运行时加载模式能够取得正确资源。
- [ ] 目标界面或场景中的最终视觉和行为正确。

## Project Questions

- 项目使用哪种资源加载和打包系统？
- 哪些文件由 Editor 工具、表格或配置自动生成？
- 资源 GUID 是否允许跨项目保留？
- 是否存在必须验证的真机构建、AssetBundle 或 Addressables 模式？
