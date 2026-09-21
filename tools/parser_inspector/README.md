# Parser Inspector

双击 `run.bat`，打开 <http://127.0.0.1:8501>。首次运行需要 Python 3.10+ 和网络；依赖安装到本目录 `.venv/`。关闭命令窗口或按 Ctrl+C 停止。

## Corpus Segmentation Review

侧栏选择 **Segmentation Review**，顶部 **Source** 选择 corpus，然后填写审阅者、选择 Auto unit。来源选项来自后端对根目录 `calendars-*.md` 的扫描与既有 `config/calendrical-ir-pipeline.json → inputs.source_texts` registry 的交集；界面不维护历法名单。当前支持四分历、三统历、九执历，分别使用 `sifen / santong / jiuzhi` 稳定 ID。

侧栏 **Corpus Full Text** 或 Review 的 Source 旁 **Full text** 按钮进入全文连读工作区。读取当前 `effective.json`，按 source offset 顺序完整显示所有分块，每段以同配色类型标签和节号开头；包含未审块，不另造数据或重新解析。来源已变更时明确显示 STALE。**返回 Review** 保留当前 corpus、选块与审阅者；有未保存草稿时不能跳转，先保存或放弃。

显示 Review progress、Modified、Accepted unchanged、Unreviewed 和 Revision。重新打开默认定位首个 UNREVIEWED，也可点 **Resume review**。左边保留机器原始文本、类型、detection、relations、review queue；右边是唯一的 Effective 编辑区，包含合拆／类型／关系控件。原文使用与输入色块一致的柔和底色：合并时标出移入当前块的文字，拆分时标出归入新块的文字，按精确 source offsets 比较，重复原句不混淆。类型／关系变化用普通文字说明，不给类型标签或整段原文染色；正文不改写。来源之间的文件、锁、revision、Undo 和页面编辑状态独立。

文本块选择器、关系目标选择器及邻块预览仅显示到首个标点前的正文，**不含标点**，保留节号／坐标区分重复首句。未审是默认状态，不加标记；仅显示「已审·原样接受／已审·已修改／待重审」。保存后保留当前选块，仅主动点击 Resume 才跳到首个未审块。Auto 和 Effective 卡片中的 alternative 关联原文完整显示；目标拆分后逐块显示并保留待复核提示。**上一块／下一块** 按 Auto 的原文顺序切换。类型、关系或拆分边界有未保存修改时提示先保存，并禁用块、来源、Resume 和工作区切换；可明确选择放弃草稿。保存一个面板不会丢弃其他面板的草稿；先保存类型／关系，再保存拆分。草稿不属于已经落盘的审阅决定，关闭浏览器不能依赖草稿恢复。

Auto／Effective 下拉选项带类型色签，与「分块类型说明」共用配色：术文及计算性说明为蓝色系，参数项／组为绿色系，参考数据／表格为暖黄色系，标题／论述为淡紫色系；同组以明暗区分，标签保留完整类型名。仅为显示分组，不改变 taxonomy。沿用原生搜索与键盘选择；色签通过当前固定 Streamlit 版本的 listbox／option 索引样式显示，浏览器回归检查搜索后类型对应及说明配色，升级 Streamlit 时需重跑。

- **Accept** 原样接受 auto 单元，只增加 `human_review`，不增加 override operation。
- **Change type / Edit relation** 使用表单修改当前 effective 块。关系按具体原文跨度绑定，重复原句不混用。`alternative_of*` 只允许属于 `alternative_procedure` 的块；将块改为 `procedure` 会同时清除不兼容的 alternative 关系。每条已有关系都有直接的「删除关系」按钮。
- **分块类型说明** 在 Change type 内解释全部九种类型及其边界；这些是文献分块类型，不是 parser operation 或完成度。
- **Edit relation** 仅提供固定 corpus 结构关系：`alternative_of_candidate`（待确认另一术法）与 `alternative_of`（人工确认另一术法）。可确认机器候选、改目标或删除；UI 无任意名称输入，后端重放也拒绝未登记关系。该关系不证明算法／数值等价。`followup` 属于合并块的 `member_roles`，用 Split/Merge 管理归属；dependency/data-flow 留给 parser/graph。本页不建立 context/binding 关系。
- **Merge ↑ / ↓** 仅合并相邻 effective 块的正文与边界，保留当前正在编辑块的类型和关系，不吸收邻块的 alternative 类型／关系；类型与术文关联分别由 Change type／Edit relation 决定。邻块原有判断仍保存在 Auto 和历史中。旧 merge 记录按原含义回放，不自动改写人工历史。**Split** 点击原文字后边界（可多选、再次点击取消），预览后保存。合并后仍能拆分，拆分后仍能合并。
- **Undo** 撤销当前 source 的最近一次操作；**Reset** 恢复当前块及与之通过合拆关联的区域；**退回最初** 恢复整个 corpus 到机器初始状态。三者都保留历史并可 Undo。审阅记录可对单个 revision 使用「撤销此更改」；若该 revision 后已有同区域修改，系统拒绝猜测，改用明确的「恢复到之前／之后」状态。其他来源／区域的独立审阅保留。
- 保存即时更新三个数据文件和 manifest，并自动刷新；关闭服务／浏览器后仍可恢复。无需最终 Submit。未确认的表单／拆分选择仍是草稿，点保存才成为决定。多页面同时打开时自动同步新状态，旧页面动作不自动重放，也不会覆盖新决定。
- **审阅记录 → View before / after** 显示每次操作的前后分块、类型、关系和审阅状态；记录人、身份、UTC 时间、revision、备注、替代／撤销关系。只有点选的记录才重放展示。

文件职责：

| 文件 | 职责 |
| --- | --- |
| `corpus-review/<source_id>/auto.json` | 机器字段保持原始结果，`human_review` 保存人工审阅记录；保留进 Git |
| `corpus-review/<source_id>/overrides.json` | 唯一 canonical 人工决定文件；`operations` 是当前规范化决定，`history` 永久保留 Accept／修改／Reset／Undo 的 before、after、revision、supersedes、reverts；保留进 Git |
| `corpus-review/<source_id>/effective.json` | 重放后的有效 corpus，adapter 从这里按已登记选择取文本；可重建，Git 忽略 |
| `corpus-review/<source_id>/manifest.json` | source_id、source_path、source_sha、auto_sha、override_sha、effective_sha、review_revision、review_status；保留进 Git |

manifest 的文件 SHA 对应实际 UTF-8 文件字节；revision 对应三个数据文件的组合 hash，不包含 manifest 自身，避免循环 hash。review_status 给出当前 source 的进度计数；它不是 parser 语义完整性或人工历史结论。文件混版、source SHA 变化均阻断写入和 adapter 读取。

`human_review: []` 为尚未审阅；记录含 `status: accepted / modified`、UTC `time`、`actor`、`override_ids`、可选 `note`；modified 同时记录本次关联区域的 `source_spans`。自动化测试使用 `scripted_test` / `automated_browser`，不记为真人审阅。

override schema **1.2** 保持四种有效操作，使用原始来源中半开区间 `[[start,end], ...]`：

| 操作 | payload |
| --- | --- |
| `set_type` | `target_spans`, `type`（已有分块类型列表） |
| `set_relations` | `target_spans`, `relations: [{kind, target_spans, ...}]` |
| `merge_units` | `targets: [source_spans, ...]`（相邻块） |
| `split_unit` | `target_spans`, `groups: [{source_spans, type, relations}, ...]`（完整且不重叠的分区） |

后端把 UI 的最终分块规范化为这些操作；派生 ID 不是编辑输入。旧 1.0 的 unit-ID / 整节 payload 仍可读取。关系目标被拆成多块时保留原始目标跨度并标 `needs_review`，不猜选新块。文本校读仍不在本流程中。

旧 history 在下一次保存时按原顺序分配 revision；历史上被旧 Undo 删除的记录无法恢复，不补造。新 Undo 追加事件并恢复当前状态，永不 pop 原事件。Reset 清除当前区域的有效决定／review 标记，但原决定继续留在 history。未增加 round-complete 按钮：完成一轮是可选的 baseline 标记，不是保存的前置步骤。

现有模块的工作流：

```text
calendars-*.md ∩ 已登记 source_texts
  → corpus_index.list_review_sources() → UI Source 下拉
  → corpus_index.build_auto_index(root, source_id) → auto.json
  → 同一 Segmentation Review 页面 → corpus_review.apply(..., source_id)
  → 更新 human_review + 规范化 overrides
  → corpus_index.effective_from_auto() → effective.json
  → 四文件事务更新 manifest → Auto / Effective 与进度刷新
  → corpus.build_source_packet_from_units() 由调用方指定 effective unit 构造 SourcePacket
  → 原有 parser
```

`corpus_index.py` 复用原抽取和纯重放逻辑；`corpus_review.py` 负责每个 source 的持久化与迁移；同一个 `segmentation_review.py` 渲染所有来源。没有新增历法专用页面或 parser 规则。九执历跨卷重复节号保留 occurrence 与原始字符坐标，unit/document ID 不再冲突。

保存使用每 source 文件锁、原子替换和短期事务日志；日志仅用于中断恢复。旧四分历三文件由原抽取命令一次迁入，保存成功后清理旧位置；人工记录与 Undo 保留，不并行维护两套数据。

重新抽取仍用原命令：

```powershell
python -X utf8 -B scripts/corpus/extract_sifen_units.py
python -X utf8 -B scripts/corpus/extract_sifen_units.py --source-id santong
python -X utf8 -B scripts/corpus/extract_sifen_units.py --source-id jiuzhi
```

保留原命令文件名以兼容已有调用，通过 `--source-id` 复用，不另造三套命令。新增同格式的 `calendars-乾象历.md` 后，只需在同一 registry 登记唯一 ID/path，即出现在 Source 下拉；页面「生成 corpus index」初始化其工作区。

当前沿用编号正文抽取规则，不纳入文件前未编号的导言。新来源的 type/detection 是沿用规则的机器候选，未声称其识别精度已获人工验证；九执历 review 读取全份编号正文，不受旧编译 calibration 的 include_patterns 限制。

同一 source SHA 且机器单元未变时恢复已有 review；来源 SHA 或已审单元机器字段变化时阻断并保留旧文件。**auto 已包含人工审阅记录，不当作缓存忽略或删除**；新 clone 中缺少 effective 时，用上述命令或 UI 重新生成即可。

旧 Workbench preset 的正文/context 选择仍受 manifest 的 unit ID 和文本 SHA 约束。若合拆改变了它选择的单元，legacy preset 会明确报缺失／来源变化，不会偷偷退回 md 或采用猜测 context；本页不自动重写 preset manifest。

检查：

```powershell
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.test_segmentation_review tests.test_corpus_index tests.test_corpus_dependencies tools.parser_inspector.test_inspector tests.workbench.test_smoke
node tests/segmentation-review-browser.mjs
```

## 完整文件链与职责

```text
tools/parser_inspector/run.bat
  → app.py：选择 Segmentation Review / Parser stages

calendars-*.md + config/calendrical-ir-pipeline.json (source_texts registry)
  → scripts/corpus/extract_sifen_units.py --source-id <id>（CLI，UI 也可调用同一生成函数）
  → source_adapters/corpus_review.py: regenerate()
  → source_adapters/corpus_index.py: build_auto_index()
  → corpus-review/<id>/auto.json（机器结果 + 当前 human_review）

segmentation_review.py：显示 Auto，编辑右侧 Effective
  → corpus_review.apply()：检查 revision、来源 SHA、actor、source spans
  → corpus_index._apply_overrides() / normalize_operations()：生成规范化有效 deltas
  → overrides.json：operations 当前状态 + history 永久事件
  → corpus_index.effective_from_auto()：只重放 active operations
  → effective.json + manifest.json：有效素材与文件校验/审阅统计
  → 自动刷新页面（无手动 reload、无最终提交保存）

effective.json + 调用方指定的 source_id / unit IDs
  → source_adapters/corpus.py: build_source_packet_from_units()
     校验原 md 的 SHA/坐标；正文/context 取自有效 unit，不重新猜切分
  → SourcePacket 3.0（每个 document 携带 unit_id + unit_index_sha256）
  ├─ Inspector runner.py → analysis_parser.inputs.documents()
  │                     → analysis_parser.lexical.tokenize_candidates()
  │                     → analysis_parser.construction_ir.parse_syntax()
  │                     → analysis_parser.pipeline.parse_packet()
  │                     → tools/parser_inspector/output/current/*.json 原生输出
  └─ workbench/api.py → workbench/service.py
                       → parse_packet() / adjudication.compiler.compile_reviewed()
                       → workbench.projection / presentation → 站内研究页面
                       → analysis_parser.execution.execute()（辅助核验）

source_adapters/dependencies.py（两条运行路径共享，无 parser import）
  → unit_hash()：编译相关内容的 hash，不含 human_review/审阅者/时间
  → artifact()：parser → graph → execution；comparison 可引用多个 parent
  → validate()：逐 unit 对比，沿 artifact parent 递归判断 valid / stale
  → Inspector run.json / Workbench response、bundle 中的 artifacts
```

`dependencies.py` 是本轮唯一新增的生产模块：它独立负责跨 Inspector／Workbench 的结果依赖契约。放进 review store 会混合审阅事务与结果生命周期；放进任一 UI 则会造成另一 UI 复制。因此通过窄的 hash / artifact / validate 接口共享。

**失效检查是读取时进行，不是后台调度器。** Segmentation Review 保存后刷新 Inspector current 的 `run.json` freshness；进入 Parser stages 时也核对，原生 JSON 不改。Workbench 返回页面焦点、恢复可见或准备操作时调用同源 `/api/artifacts/status`，陈旧结果保留、禁止在旧结果上继续判断／执行，需重新分析。响应比当前页面旧时丢弃，不能覆盖新状态。

每个 artifact 记录 kind、内容 hash、parents 和实际正文/context 的 source_id、unit_id、effective hash；不依赖整个 corpus 的 review_revision。Accept unchanged 不导致失效。只改 §39，只有依赖它的 parser、后继 graph/execution 和多父 comparison stale；若 §40 的 context 确实引用 §39，它也应 stale。merge/split 后旧 unit 消失，同样视为依赖失效。重新编译范围是受影响 procedure；未实现编译器内部的 event 级增量重算。

`valid` 只表示输入仍匹配，不等于语义正确／人工审定／图闭合。外部直接改原始 md 仍触发已有来源 SHA 阻断，必须先重新核验来源；本轮没有放宽该保护。历史导出若没有 artifacts，不能追溯宣称已经有局部失效记录。当前 Inspector 仍只有一个 current；Workbench 浏览器持久化 session、重新打开重编译，没有另建 parser 历史结果库。comparison 的依赖传播契约已测，未新增比较算法或 M4 功能。

回归入口：`tests/test_segmentation_review.py`（保存、history、Undo、续审、并发）、`tests/test_corpus_dependencies.py`（局部/传递失效与真实运行路径/API）、`tests/test_corpus_index.py`（抽取与重放）、`tools/parser_inspector/test_inspector.py`（原生输出）、`tests/segmentation-review-browser.mjs`（实际浏览器）。

2026-09-18 本轮验证（基点 HEAD `52c7754`，未提交／未 push）：corpus index 8、依赖 6、segmentation review 15、Inspector 7、Workbench 27、adjudication 71、parser 61／94／78、reconciliation 5，共 372 项 Python 测试通过；CText 4 项、Eleventy build、Segmentation Review 浏览器及两套 Workbench 浏览器通过。包含旧有效性响应晚到不得解除 stale 的浏览器反例。测试身份为 scripted_test／automated_browser，真实 corpus 的人工审阅未被测试改写。原有测试仍会发出 Streamlit 裸测试上下文提示及一处旧 ResourceWarning，不影响通过结果。可选 round-complete 标记未添加；没有新增比较计算或 event 级增量编译。

浏览器验收使用三份真实 corpus 的临时副本和 Unicode 坐标夹具，验证来源切换、进度及 Undo 隔离，不写入当前 corpus 的人工记录。报告与截图位于忽略目录 `tmp/segmentation-review-tests/`。

## Parser stages

未选择审阅作业时保留只读研究视图；在 **Current review** 创建或恢复持久作业，选择现有 effective corpus units 作为 Primary，即进入 K2 的 source-first annotation 工作流。

### K2 持久审阅与 annotation

默认英文、中文原文不改。左侧阅读原文并点击待审标记，右侧一次显示一个当前问题。开启 **Adjust term span** 后直接拖选字符、**Queue selected term**，再 **Confirm term spans and re-run**。边界只进入当前 occurrence 的词法输入，复用原 grammar，不改全局 TERMS。词义可采用机器候选、排除候选，或用现有 registry 概念和规则局部组装。**Why these options?** 保留候选推导树、规则、provenance 和三轴状态；R1–R4/K 完整 evidence 在 **Inspection / Evidence**。问题与选项全部来自确定性代码与预写文案，没有运行时 LLM。

标记与拖选按 `doc_id / reading_id / Unicode [start,end) / quote` 定位 Primary 或 Context。来源问题可附加 Context、绑定真实 producer/port 或声明外部输入；Context 附件不等于批准解释。Context target 与 payload 地址记录 attachment 依赖，撤销附件传播失效；过时管理范围仍可在 **Management → unmanage** 释放。最后一个问题消失后，效果、历史、撤销、管理、诊断和证据继续显示。

每个作业写入 **`.local/review-jobs/<job_id>.json`**，格式为 **`ReviewJob/1`**。该目录精确 Git 忽略，属于持久研究记录，**不是缓存**。备份使用同页「导出 ReviewJob/1」；导入保留原 ID，拒绝覆盖现有文件。关闭页面或停止服务后，重开选择相同作业即可恢复；URL 的 `review_job` 参数可直接重开。

Envelope 仅保存 `job_id / revision / source_selection / base_packet_identity / analysis_inputs_digest / session / branch_id / management_events / created_at / updated_at`。`session` 仍为现有 `AdjudicationSession`，不保存另一份编译模型。`source_selection` 明确包含来源、Primary/初始 Context unit IDs、provided scope 和 selected profiles；当前 UI 新建 scope/profiles 为空，不隐式批准背景。analysis digest 覆盖 packet 和 active review 代码，session 原有 runtime locks 保留；来源或代码发生变化时作业变为只读，保留历史和导出，不自动迁移。

提交在每个作业的文件锁内核对**页面此前显示的** revision 和 digest，将 decisions 与 management 同时放入副本，trial compile 至失效集合稳定、检查同 facet 冲突与组合兼容性后再原子保存。manage-only / unmanage-only 也重编译。旧页面、非法 payload、编译异常和写盘失败不覆盖旧作业。合法 partial graph 可保存。retract 追加历史，重新验证前提；不会解除接管。

`management_events` 是独立的 append-only 接管记录，含 action（manage/unmanage）、完整 source target、facet、branch、actor、时间、理由、依赖及可选 `semantic_target`。后者复用现有 `normalize_decision_target` 地址，明确输入或输出角色/端口，独立于 decision ID；只有原文跨度而未限定输入/输出时保守保持 pending。证据跨度或 producer 地址不能替代真正的语义目标。撤销解释不删除管理范围；显式退出必须引用已记录 scope，仍有有效语义依赖则拒绝。

数量解释在运算读取之前进入 invocation-local hook。精确目标被接管但没有有效解释时保持 unresolved，抑制对应 fallback 并阻断依赖执行；只有显式 unmanage 才恢复旧路径。绑定接管也在原 linker 中抑制自动 producer 选择。**Run current reviewed model** 复用现有 executor，记录 job/revision/branch/analysis identity/inputs；判断改变后旧结果明确 STALE，重跑读取当前 reviewed graph。月→日关系验证实际 multiply/divmod/参数来源/调用和 sibling ports，分数显示为 `348/940`，不把余数当作 348 天。

回归入口：`tests/adjudication/test_term_claims.py`、`test_quantity_targets.py`、`test_reviewed_relations.py`、`test_k2bc_adversarial.py`，`tests/workbench/test_review_effects.py` 和 `tools/parser_inspector/test_review_panel.py`。浏览器运行 `node tests/k2bc-review-browser.mjs`，临时 corpus/job 与当前研究记录隔离，证据在 `tmp/k2bc-review-tests/`。不恢复 Context B/C/D；不进入 K3 全局 hardcode 清理或 K4 未见语料 evaluation。

`readable.compile_view()` 每次读取分别调用一次 `parse_packet(packet)` 和
`compile_reviewed(packet, new_session(...))`。后者返回 bundle；
`bundle['graph']` 是原生 report，可直接使用同一个
`evaluation.semantic_regression.project_report()`。
不重跑 tokenize、syntax 或 link，不写 baseline、session、审阅记录或 output/current。

页面持续显示原文，点击对象的原文证据按 Unicode code-point offsets 高亮。
R1–R4 仅在 presentation 按原文位置排序，canonical snapshot 不变。
R1 是 Lexical candidates，类型表示 parser edge，不等于确认词性；Syntax 默认折叠，
“查看全部 parser edges”保留全部记录及原文顺序。
R2 通过同一 canonical projector 将候选关联回 report，读取 production_id，
从既有 GRAMMAR 表取精确 pattern；syntax slots 只显示后端记录的跨度。
report 没有保存 slot 使用的完整 lexical edge 路径，明确显示 provenance unavailable。
操作只通过 event.syntax_node_id 关联，逐项显示 reads/writes，未推断 slot → port。
量角色只引用 call formal_bindings/return_ports 或明确的 value.role；不将未返回量猜成 intermediate。
R3 按 Program IR.parent 嵌套；无 parent 的 MethodSlice 独立显示，已有调用关系单独标注。
R4 按 formal 聚合，保留每个定义的使用位置、候选及连接状态。诊断只通过显式名称或
formal binding 的 value/labels 加精确使用跨度关联；不确定的诊断独立保留。
ontology 的 definition/methodology 可展开，selected 文案为“机器编译采用；未经人工确认”。

默认阅读层采用 progressive disclosure：每层只说明一次研究问题与 parser 模块来源。
R2 以原文计算表达为单位，直接显示运算、参与量的端口角色、结果和后续使用；
后续关系只读取相同 value ID 的 reads、显式 alias 与返回记录，不按同名量拼接。
除法保留 dividend/divisor/quotient/remainder，缺失端口显示“尚未确定”。
方法引用显示复用片段、传入角色、返回量和后续使用。
R3 使用“过程／计算段／可复用计算片段”，合并需要接入的量，展示已有承接关系；
正常的 parent=null 不报缺失。R4 分开显示当前来源和预期端口，将相关诊断收在同一量下面。
grammar、完整 slots、ontology、event/port、原始 provenance 保留在“查看机器依据／技术详情”，
无 slots 的记录不提示 slot provenance unavailable。缺失来源和未知数量关系仍在默认层提示。

页面空 session 时只显示一份 machine result；实际比较相等才写
**reviewed = automatic / no human decisions**。
即使 session 为空，也不假设结果相等。若有差异，显示“编译路径差异”并提供折叠详情；
若 reviewed graph 不可用，显示 replay 状态，不将其当作空结果或成功。
当前无人工决定，不能把差异解释成人工修改或阶段确认。

原有 `runner.py` 保留供原始 parser 输出测试和诊断调用，不是另一套 UI 工作流。
检查：

```powershell
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tools.parser_inspector.test_readable tools.parser_inspector.test_inspector tests.test_semantic_regression
```
