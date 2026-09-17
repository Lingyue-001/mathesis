# MATHesis：方法与实现对应（一页）

核对基线：`17f48a3`；真实目标：`sifen-3-7-alternative`（四分历 §40），空 decision log。本页区分**规则推断**、**结构验证**与**学者判断**；有图、有数值或编译选中都不等于历史解释成立。

| 层 | 实际输入 → 输出 | 负责文件／入口 |
|---|---|---|
| Source | 已登记 corpus 章节、hash、背景范围 → `SourcePacket 3.0`，reading 与原件坐标 | [corpus.py](../source_adapters/corpus.py) `build_source_packet`；[workbench-procedures.json](../config/workbench-procedures.json) |
| Construction | 来源文档 → token 候选 → 有 span、typed slots、production 的 Syntax IR／构式候选 | [lexical.py](../analysis_parser/lexical.py) `tokenize_candidates`；[construction_ir.py](../analysis_parser/construction_ir.py) `parse_syntax` / `propose_constructions` |
| Program IR | 构式与背景声明 → procedure/query、def/use、formal inputs、return ports；链接产生 imports 与诊断 | [context_compiler.py](../analysis_parser/context_compiler.py) `compile_documents`；[program_ir.py](../analysis_parser/program_ir.py) `compile_frames` / `link_entry` |
| Event / value | 已链接的范围与构式 → 有 producer、reads/writes、unit/scale、来源证据的 event/value graph | [scoped.py](../analysis_parser/scoped.py) `lower_linked` / `lower_primitive`；[state.py](../analysis_parser/state.py) `Environment.event` |
| Adjudication | packet、session、branch → replay 的有效决定／冲突／stale；有效决定进入构式、范围、绑定、profile，再走正常降译 | [session.py](../adjudication/session.py)、[replay.py](../adjudication/replay.py)；[compiler.py](../adjudication/compiler.py) `compile_reviewed` |
| Validation | 当前 graph、来源、决定依赖 → audit、coverage ledger、review queue、重建 trace、完整导出资格 | [audit.py](../analysis_parser/audit.py)；[coverage.py](../adjudication/coverage.py)、[review_queue.py](../adjudication/review_queue.py)、[trace.py](../adjudication/trace.py)、[validation.py](../adjudication/validation.py)、[bundle.py](../adjudication/bundle.py) |
| Projection | graph + bundle → 来源—步骤—量的关联、阶段记录、人话 view model → 站内 Workbench | [service.py](../workbench/service.py) `_reviewed_response`；[projection.py](../workbench/projection.py) `project_graph`；[presentation.py](../workbench/presentation.py)；[procedure-view.js](../src/js/ui/procedure-view.js) |

上述是阅读层次，**adjudication 并不是在成品图之后补改语义**。实际 Workbench 请求经 `open_adjudication → _reviewed_response → compile_reviewed`：先 replay，再 `_prepare_packet → ScopedParser → _rebuild_program → link_entry → lower_linked`，然后 coverage／queue／bundle／projection。自动入口 `pipeline.parse_packet` 的 `3.x` 路由也使用 `ScopedParser`；reviewed 路径复用同一 IR 与 lowerer。浏览器只提交 typed decisions，不提交修改后的 graph。执行器是另行调用的辅助核算视图。

## 一次真实追踪：`以大周乘年`

1. **来源。** [calendars-四分历.md](../calendars-四分历.md) §40 全文为「一術，以大周乘年，周天乘減之，餘滿蔀日，則天正朔日也。」adapter 取得原件区间 `[2583,2610)`；其中该句是 `sifen:40 / reading sifen:40.e87280a32dae / [3,8)`，对应原件 `[2586,2591)`。坐标均为 Unicode code point、右端不含。
2. **规则推断。** `tokenize_candidates → parse_syntax` 匹配已有 grammar `以{left:a}乘{right:a}`，产生 `kind=multiply`、`left=大周`、`right=年`；来源仍为 `[3,8)`。本次候选为 `sifen:40:ast4`，production 为 `G_MULTIPLY_6`。这是词法／构式规则识别，并非研究者选择。
3. **范围与来源链接。** `compile_frames` 将其放入 `def-1f28e00309bf7b000809`；`compile_documents` 提供 §25 的背景声明「大周，三十四萬三千三百三十五」。`link_entry` 对「年」仍报告没有已声明 root input 或 source producer，不因字面有“年”就自动承认合法根输入。
4. **生成图。** `lower_linked → ScopedParser.lower → lower_primitive → get / binary → Environment.event` 生成 `e6:multiply`，读取 `left=v3`（`e3.result`，背景「大周」）和 `right=v5`（`e5.result`，未解决来源的「年」输入），写入 `result=v6`。节点保存同一原文 span、`syntax_node_id`、production、definition 与 `call-1`。`v3/v5` 的 unit 为 `opaque`，`v6` 为 `product`，数量语义均仍 `unknown`。
5. **结构验证与学者判断边界。** 当前 §40 为 `graph_status=partial`、13 个 review questions、`valid_for_complete_export=false`；`周天乘減之 [9,14)` 等构式仍未解释。生成相乘 event 不能消除这些问题。研究者若提供 binding／quantity semantics／profile 等决定，需保存 actor、anchor 与依据，经 replay 重建 IR 和图，并重新检查；本次追踪没有捏造任何 human decision。
6. **展示。** `project_graph` 由 `syntax_node_id` 与带 reading 的 source overlap 建立 step links，由 value producer/output port 与 event reads 建边；`build_presentation` 从现有 ontology 取标签。页面把相同地址显示为「大周、年 → 相乘 → 派生量」，点击回到 `[3,8)`。浏览器只安排位置、聚合同源待审提示及高亮；不补单位、不判候选合法性、不把末端输出当作已审定结果。

这里的 `ast4/e6/v3/v5/v6` 是本次编译的可检查地址，**不是跨版本稳定主键**。复查应使用 source/reading/span 与 producer/port 关系。浏览器验收见 [browser-smoke.mjs](../tests/workbench/browser-smoke.mjs)：两个真实目标的首屏、event/value 完整展示、相乘回原文、未决跨度和 Advanced；详细软件证据见 [m3-evidence.md](adjudication/m3-evidence.md)。
