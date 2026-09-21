# K2-B+C 验收记录

日期：2026-09-20。基线为开工时的本地 working tree；不是 Git HEAD，也没有恢复归档的 Context B/C/D。已阅读并按附件全部 handoff 文件实施。

## 实现与文件职责

| 文件 | 本轮职责 |
| --- | --- |
| `adjudication/term_claims.py` | occurrence 边界、候选 adoption/rejection、registry 内人工 composition、排除自身的候选重验证、语法 slot 的解释证据 |
| `domain_kernel/engine.py`、`output.schema.json`、`docs/domain-kernel/SCHEMA_REFERENCE.md` | K 候选接受局部边界，保留原候选、expression、child_ids、rules、provenance 和状态轴；全局 TERMS 未变 |
| `adjudication/anchors.py`、`decision_contracts.py`、`session.py`、`validation.py` | 稳定 input/output 地址、branch 约束、B/C action 与 facet 合约 |
| `adjudication/replay.py` | 原 replay 内合并互补 facets、检测同 facet/组合冲突、保持整条判断原子性、继承分支地址；排除 A 后可采用 B |
| `adjudication/quantity_targets.py` | 将稳定地址解析到已有 Program IR；配置 invocation-local 输入/输出 hook，接管但未解释时保持 unresolved |
| `adjudication/compiler.py` | 在原 reviewed compilation 内重建局部 grammar、安装 quantity hooks、应用 binding management，并在原图上验证 relation 后重新 lowering |
| `analysis_parser/scoped.py` | 数量在 operation 读取之前获得 reviewed semantics；identity alias 隔离一个消费者，原 producer 不被改写；接管空缺阻断执行 |
| `analysis_parser/program_ir.py` | 原 linker 处理 binding management；接管但无有效 binding 时不自动选回唯一 producer |
| `adjudication/reviewed_relations.py` | 有限的汉四分月→日关系验证：真实乘除事件、参数来源、调用、作用域、商余 sibling ports |
| `analysis_parser/pipeline.py` | 独立修复 remainder producer invariant：unknown 单位的真实余数仍是候选，不制造替代 missing input |
| `analysis_parser/ontology.py` | 注册本轮 action/diagnostic 的确定性标签；没有新增历史概念或全局词项 |
| `workbench/review_jobs.py` | 复用 ReviewJob/1，支持 facet/semantic target 与父分支管理继承、子分支释放 |
| `workbench/service.py` | decision+management 同次 trial compile、兼容性/失效检查后原子保存；manage-only/unmanage-only 重编译；当前 job exact execution 与 stale identity |
| `workbench/question_presenter.py` | 基于当前原文、schema/Kernel 和 reviewed graph 的英文问题与选项；不完整计数解释仍可补全；系统诊断不进入 scholar queue |
| `tools/parser_inspector/source_annotation.py` | 复用的 Unicode 字符拖选、精确 occurrence 标记与当前问题聚焦 |
| `tools/parser_inspector/review_panel.py` | source-first UI、局部组装、判断前预览、效果、历史/撤销、management、diagnostics、当前 reviewed execution |
| `tools/parser_inspector/readable.py` | 保留原 R1–R4 evidence/projection，放入 Inspection / Evidence；K 使用当前 effective source 与边界 |
| `tools/parser_inspector/README.md` | 更新实际 K2 工作流、管理/执行边界与验收入口 |

新增效果测试：`tests/adjudication/test_term_claims.py`、`test_quantity_targets.py`、`test_reviewed_relations.py`、`test_k2bc_adversarial.py`；`tests/workbench/test_question_presenter.py`、`test_review_k2bc.py`、`test_review_effects.py`；`tests/k2bc-review-browser.mjs`。

更新回归：`tests/workbench/test_review_jobs.py`、`tools/parser_inspector/test_review_panel.py`、`test_inspector.py`、`test_readable.py`。保留写盘失败、旧页面竞争、Context attach/retract、过时 scope unmanage、只读旧 job 的检查。

上述清单仅归因于本轮。`.gitignore`、`AGENTS.md`、已有 K2-A/effective_packet 工作和其他开工前的未提交更改均未回滚。未提交、未 push，未改私有 NOTE/LOG。

## 真正的 before → decision → after

完整结构证据：[probe-effects.json](../.cache/k2bc/probe-effects.json)。它由临时 corpus → SourcePacket → 持久 ReviewJob → 同一 reviewed compiler → 现有 executor 生成，没有 compiler mock；合成材料只写在临时目录。

| Probe | Before → decision → after |
| --- | --- |
| B1 `以日率乘月率` | 原路径无 multiply → 确认本 occurrence 的 `日率`、`月率` 边界 → 同一 grammar 产生两个 operands 的 multiply。撤销有决定性作用的 `日率` 边界后恢复未解析状态。原本已经识别 `月率`，所以单独撤销它不应伪造 grammar 退化。全局 TERMS 字节/内容不变。 |
| B2 `日率` | 未解释 slot → 采用机器 canonical expression+snapshot → reviewed grammar 的对应 slot 带此解释与 decision provenance；撤销/排除后不保留它。人工 composition 标为 human_composition，只允许当前 registry 的概念/规则，不创造参数、producer 或换算。排除 A 与采用 B 可共存；排除已采用的同一解释则冲突。 |
| C1 `置入蔀年減一` | 旧路径的 year 不能证明人工解释生效 → 提交 ordinal、base=1、current_bu_start、start_of_current_year、step_unit=year → operation 读取的是 reviewed ordinal view；减一结果带 elapsed/year 与本次 decision refs。只保留一次减一。其他缺少的模型/参数仍诚实 unresolved。 |
| C2 `置甲量減一，名為乙量` | unmanaged 保持旧 year → manage-only 后 unknown/unresolved，依赖执行被阻断 → 五 facet 的 month ordinal 判断使输入 5 输出 4 elapsed months。撤销该解释后仍 managed、结果不再产生；显式 unmanage 才恢复旧 year 路径。 |
| C3 两次调用 | 一个 source producer 被两个 consumer 读取 → 只对 A 的 input/call 作 month ordinal 判断 → A 为 month，B 保持 year，producer metadata 不变；不是全局改单位。 |
| C4 §38/§39 | §39 的 `入蔀積月` 来源未由人工选定 → 接入 §38 并以稳定 definition/port 地址绑定真实 `積月` → 原 linked imports/formal_bindings 使用此 producer。撤销 binding 使依赖解释失效，撤销 context 使后代退出 effective。额外验证：binding 接管但未定/已撤销时，唯一自动 producer 也不能偷偷恢复。 |
| C5 月→日 | 同一真实 multiply/divmod 链，但数量换算关系未获批准 → 验证 §19 `蔀日=27759`、§14 `蔀月=940`、§38 月 producer、§39 call/scope/ports 后批准 → `12×27759=333108`，商 `354` whole days，余数 `348/940` day。真实余数 representation 的 denominator_id 指向当前 divisor value；没有 replacement arithmetic。 |
| C6 invariant | 独立复现 remainder_producer_corruption → 修复 unknown 余数候选过滤 → 使用真正的 divmod remainder producer。关系批准不能擦除 graph invariant；相关负向测试独立于 relation approval。 |
| C7 最后一题 | 实际只有一题 → 声明支持的外部 input → 题数 1→0；效果、历史/撤销、管理、执行、Inspection 仍存在。撤销后 0→1。 |
| C8 旧 job | 模拟旧 runtime identity → 只读、可导出、禁止执行 → 同 source_selection 新建 current job；旧文件字节与 identity locks 不变，无自动迁移。 |
| C9 执行 | 当前 revision/branch 的 reviewed graph → 原 executor 执行并记录 job/revision/branch/analysis identity/inputs/status → 任意判断变更使旧展示标为 STALE；重跑读取新图，managed unresolved 返回阻断而非旧成功结果。 |

## 新鲜测试结果与命令

在仓库根目录运行。下列 `PY` 表示 `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B`，不是另一个环境。

| 命令（`PY` 后的参数） | 结果 |
| --- | --- |
| `-m unittest discover -s tests/adjudication -p test*.py -q` | 127 passed |
| `-m unittest discover -s tests/workbench -p test*.py -q` | 61 passed |
| `-m unittest discover -s tools/parser_inspector -p test*.py -q` | 46 passed |
| `-m unittest discover -s tests/parser -q` | 61 passed |
| `-m unittest discover -s tests/parser_v3 -p test*.py -q` | 94 passed |
| `-m unittest discover -s tests/parser_rescue -q` | 78 passed |
| `-m unittest discover -s tests/domain_kernel -q` | 25 passed |
| `-m unittest discover -s tests/reconciliation -q` | 5 passed |
| `-m unittest discover -s tests -q` | 85 run，83 passed，2 个既有 frozen-input errors，见下文 |
| `-m tests.workbench.test_review_effects` | 7 passed，并生成 B1/B2/C1–C5/C7–C9 的实际效果 JSON |
| `-m unittest tests.workbench.test_question_presenter tools.parser_inspector.test_review_panel -q` | 最终选项文案调整后的针对性回归：12 passed |
| `node tests/k2bc-review-browser.mjs` | 13 个真实浏览器检查 passed，0 page errors；独立读取实际浏览器 job 的效果断言全部通过 |
| `git diff --check` | passed；只有仓库既有 LF/CRLF 提示 |

顶层未通过的两项是 `test_pattern_importer.ImporterTests.test_annotation_files_are_actually_opened_only_after_both_compiles` 与 `test_clean_processes_are_byte_identical_and_preserve_compiler_before_import`。都停在 `frozen_input_changed: analysis_parser/ontology.py`。冻结期望 SHA 为 `32882f02368476579164f8020c43ce48d5d39ffd76c5e854cc76d57cfdccb30a`，本轮开工前 working-tree 快照内的 SHA 已为 `80bc8a65fb2cdad190c5bb5fcfd9dbc85d9e454baa2028983c8dda5227c788f3`。未更新 frozen inputs，也未把冻结参考重跑当作 K4 evaluation。

## 浏览器证据

命令：`node tests/k2bc-review-browser.mjs`。使用真实 Chromium、真实 Streamlit 页面和独立临时 source/job store；通过实际拖选、radio、保存、撤销、management、执行控件操作。浏览器保存的 job 还会由独立 service 读取，验证实际 grammar/quantity/execution，而不是仅验证按钮或 revision。

完整结果：[result.json](../tmp/k2bc-review-tests/result.json)；实际浏览器作业的 compiler/execution：[browser-effects.json](../tmp/k2bc-review-tests/browser-effects.json)。已人工查看 B1、C2、C5、C7 截图，核对原文、结果单位、分母、历史和执行状态。

截图：

- [B1 拖选前](../tmp/k2bc-review-tests/B1-before.png)、[边界后真实 multiply](../tmp/k2bc-review-tests/B1-reviewed-multiply.png)
- [C1 判断预览](../tmp/k2bc-review-tests/C1-year-decision.png)、[reviewed elapsed years](../tmp/k2bc-review-tests/C1-reviewed-years.png)
- [C2 month 判断](../tmp/k2bc-review-tests/C2-month-decision.png)、[4 elapsed months](../tmp/k2bc-review-tests/C2-execution-months.png)、[撤销后 managed 阻断](../tmp/k2bc-review-tests/C2-retracted-managed-blocked.png)、[显式 unmanage](../tmp/k2bc-review-tests/C2-unmanage-legacy-restored.png)
- [C5 真实 348/940](../tmp/k2bc-review-tests/C5-fractional-day-execution.png)
- [C7 无题仍保留控件](../tmp/k2bc-review-tests/C7-no-question-controls.png)、[执行与历史](../tmp/k2bc-review-tests/C7-last-question-execution.png)、[撤销恢复问题且旧结果 stale](../tmp/k2bc-review-tests/C7-restored-question-stale.png)
- [C8 旧 job 只读](../tmp/k2bc-review-tests/C8-stale-job.png)

## 范围与限制

- 只完成有限 K2 schema/registry 内的解释，未实现 ontology learning、自由文本直接变成可执行本体、普遍历史换算发现或未见语料泛化。
- C1/C5 的局部运算得到证实，不宣称包含其他缺失输入/模型的整份古代历法已完全可执行；运行结果明确区分 partial/unresolved。
- bare occurrence 的旧管理记录没有明确 semantic input/output 时仍为 pending；只有精确、可解析的 semantic target 才能声明对应 consumer 已接管。
- annotation 主流程为英文；保留的 CH 切换只使用已有预写文案，不调用 LLM 翻译。
- R1–R4 原有分析与显式 projection 保留。自动路径只包含要求独立修复的 C6 invariant 修正；全局 legacy hardcode 保留，由局部 reviewed hook 控制接管处。
- **K3/K4 均未开始。没有恢复 Context B/C/D，没有第二套 parser/graph/executor/session/review-store。**

## K2 final hardening addendum

This addendum supersedes any earlier claim that the frozen ontology input was unchanged.

- `workbench/question_presenter.py` now offers a current-蔀 ordinal option only when the current K bundle has a compatible `localized_quantity(scope.bu, time.year)` candidate. The attested `入蔀年` candidate carries `S-C46`; neutral `置甲量減一` receives no 蔀/year/month option. It remains a generic counting-convention question, and the synthetic positive consumer probe supplies its month coordinate as a scripted decision.
- `adjudication/reviewed_relations.py`, `adjudication/compiler.py`, and `analysis_parser/scoped.py` now pass the validated month-to-day claim to the exact `divmod` operation before its legacy transition is selected. The reviewed hook sets `quantity_transition = reviewed_month_to_day_relation`, applies sibling port semantics before downstream consumption, and does not create any arithmetic.
- The isolation test removes only the Han Si-fen `蔀日/蔀月` legacy contextual-rate rule. Before approval, the actual §39 division is `unknown_quantity_use`; after approval, it is resolved, has no `execution_blocked`, and the existing executor returns quotient `354` and remainder `348` for the same `12 × 27759 / 940` graph operation.
- `tools/parser_inspector/review_panel.py` groups managed facets belonging to the same semantic target and emits all corresponding `unmanage` events in one `ReviewJob/1` transaction through **Release this interpretation takeover**. The C2 browser run changes revision 4 to 5 once, releases all five facets, and restores the legacy path only after that explicit release.
- `ReviewExecution/1` now returns `graph_status`; the execution panel shows `Graph: partial` separately from `Numerical check: executed for current closed region`.
- The human-composition test now uses `accumulation(rate_for(body.sun))` for `日率`. It validates against the existing registry and is explicitly absent from the K machine candidates. It supplies no value, producer, or conversion.

### Frozen ontology attribution

The K2-B+C active-working-tree snapshot stored in `.cache/k2bc/active-baseline.zip` has
`analysis_parser/ontology.py` SHA-256 `80bc8a65fb2cdad190c5bb5fcfd9dbc85d9e454baa2028983c8dda5227c788f3`.
The current file is
`a0e8fea7b4c17c3c220d7dd0ca5f933ddfad9cdfd4b706c797e08e3dfc4c0c06`.
`HEAD:analysis_parser/ontology.py` is
`8bfecf78d04ab0ca605f6c6247ec5b831dec981fd57a7b1c74dde597318a7729`.

`git diff -- analysis_parser/ontology.py` contains 27 added lines: the K2 action and cause labels. Therefore the two frozen-input failures cannot be cited as an ontology no-regression proof. Their frozen baseline remains untouched; this work neither updates it nor treats it as K4 evaluation.

### Final hardening verification

| Command | Result |
| --- | --- |
| `python -m unittest tests.workbench.test_question_presenter tests.adjudication.test_reviewed_relations tests.adjudication.test_term_claims tests.workbench.test_review_k2bc tests.workbench.test_review_effects` | 32 passed |
| `tools/parser_inspector/.venv/Scripts/python.exe -m unittest tools.parser_inspector.test_review_panel` | 8 passed |
| `tools/parser_inspector/.venv/Scripts/python.exe -m unittest discover -s tests -q` | 85 run, 83 passed; only the two frozen ontology-input errors described above |
| `node tests/k2bc-review-browser.mjs` | 14 Chromium checks, 0 page errors; includes C2 graph/numerical-status separation and one-click five-facet release |
| `git diff --check` | passed |

The earlier C2 machine-option screenshot is superseded: the production UI no longer offers a 蔀 month interpretation for neutral `甲量`. The current C2 browser evidence begins from the scripted neutral decision, then verifies its reviewed execution, retract-and-block behavior, and one-click release in the real UI.

### Scope limits retained after hardening

- Quantity semantics are consumer/definition-local under the current one-invocation-per-definition model. C3 proves distinct consumer definitions do not contaminate each other; it does not claim arbitrary multiple call-instance semantics for one definition.
- `CONCEPT_LABELS` and `CONSTRUCTOR_LABELS` remain a second presenter vocabulary in `question_presenter.py`. Consolidating that presentation source is deferred to K3 cleanup and was not started here.
- K3 global hardcode cleanup and K4 unseen-corpus evaluation remain out of scope and have not begun.

## ScholarSourceProjection contract 1.1 hardening — 2026-09-20

The user-approved scope is the existing `workbench/annotation_projection.py`, its tests and documentation. The final annotation renderer remains gated on human review of the actual JSON. The authored contract and both fixtures were copied byte-for-byte from `ScholarSourceProjection_v1_1.zip` after SHA-256 manifest verification; the full golden replaces the earlier subset fixture in its existing path.

### Implemented behavior

- Admit non-unknown Kernel occurrences, replayed term boundaries/interpretations, and selected non-Heading Term slots; retain canonical child occurrences. Heading slots remain in their construction without automatically becoming Terms. Unknown computational operands and reviewed Heading boundaries survive.
- Select the first primary document by default, or an effective-packet document through keyword-only `focus_doc_id`. Filter source objects and their references to that document/reading while retaining the complete graph for external producer provenance. Invalid focus raises `ValueError`.
- Omit mixed-document core events with `cross_document_step_not_projectable`; emit Flows only when they have projected consumer Steps. External producers remain in `producer_source`, never as dangling `producer_step_id` references.
- Merge canonical links by relation/from/to/role/ordinal, union evidence, and retain explicit over structurally-derived basis. Stable serialization sorts objects and strips volatile producer metadata; it does not deduplicate or suppress canonical objects.
- Preserve a no-composition alternative alongside a composition alternative without claiming a unique `children` tree. Semantic serialization order remains unranked.

### Acceptance evidence

The tests first reproduced seven failed assertions and two missing APIs. After the implementation, a separate composition counterexample failed before its correction. Focused projection tests now cover exact full-golden equality, complete §15 patched-golden equality, canonical uniqueness/evidence union, basis precedence, role/ordinal identity, unknown/reviewed admission and retraction, recursive components, alternate focus, mixed events, stable ordering and read-only behavior. A focused import with a missing native binding emits `flow_input_unlinked` while its empty Flow is omitted; ordinary out-of-focus imports remain omitted without spurious diagnostics.

| Case | Terms | Constructions | Steps | Flows | Facets | Canonical links | Diagnostics |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| §38, no context | 19 | 8 | 5 | 3 | 7 | 26 | 0 |
| §38, with §15 | 19 | 8 | 5 | 3 | 6 | 26 | 0 |

Both stable results satisfy exact equality against the authored base fixture and its context patch, respectively. The context test compares the complete expected result, so unchanged flows and independent facets cannot silently change. Canonical link counts, evidence and diagnostics are checked independently of the stable view.

Fresh Python 3.11 verification uses `tools/parser_inspector/.venv/Scripts/python.exe`:

| Command suffix | Result |
| --- | --- |
| `-m unittest tests.workbench.test_scholar_source_projection tests.workbench.test_annotation_projection -q` | 26 passed |
| `-m unittest discover -s tests/workbench -p test*.py -q` | 91 passed |
| `-m unittest discover -s tools/parser_inspector -p test*.py -q` | 52 passed |
| `-m unittest discover -s tests/adjudication -p test*.py -q` | 128 passed |
| `-m unittest discover -s tests/parser -p test*.py -q` | 61 passed |
| `-m unittest discover -s tests/parser_v3 -p test*.py -q` | 94 passed |
| `-m unittest discover -s tests/parser_rescue -p test*.py -q` | 78 passed |
| `-m unittest discover -s tests/domain_kernel -p test*.py -q` | 25 passed |
| `-m unittest discover -s tests/reconciliation -p test*.py -q` | 5 passed |
| `-m unittest discover -s tests -q` | 87 run; 85 passed, 2 existing frozen-input errors |

The two errors remain `test_pattern_importer.ImporterTests.test_annotation_files_are_actually_opened_only_after_both_compiles` and `test_pattern_importer.ImporterTests.test_clean_processes_are_byte_identical_and_preserve_compiler_before_import`, caused by the previously documented `frozen_input_changed: analysis_parser/ontology.py`. This pass did not change the frozen baseline or semantic code: all 41 captured files under `analysis_parser/`, `adjudication/` and `domain_kernel/` match their start-of-turn SHA-256 hashes. Streamlit bare-mode and the existing parser-rescue unclosed-file warnings remain non-failing. No UI file changed; no browser/renderer acceptance is claimed in this pass.

Actual outputs reuse the existing audit paths:

- `.cache/scholar-source-projection/proc38.actual.json` — full canonical projection.
- `.cache/scholar-source-projection/proc38.stable.json` — exact semantic golden view.
- `.cache/scholar-source-projection/proc38.with-section15.actual.json` — full canonical projection with context.
- `.cache/scholar-source-projection/proc38.golden-diff.json` — equality and count report.

Independent read-only review compared the current implementation against the saved pre-change module and the 1.1 contract, reran the scholar projection tests, and found no remaining in-scope correctness blocker or dangling reference. A proposed unknown-parent counterexample was withdrawn after checking the native Kernel invariant: opaque unknown candidates cannot have children. The focused missing-binding diagnostic was verified by a direct probe.

This is a projection contract gate, not a historical gold judgment or approval of the final renderer. No parser/compiler/executor/Kernel semantics, source data, human records, NOTE/LOG, commits or pushes were changed by this pass.

## Scholar Interaction v1 — final pre-renderer pass

Spec: `docs/SCHOLAR_INTERACTION_CONTRACT.md`, imported byte-for-byte after verifying the supplied `ScholarInteraction_v1_and_projection_fixes.zip` manifest. The user authorized five bounded changes; the renderer is explicitly excluded.

### Files and responsibilities

- `workbench/annotation_projection.py`: the sole projector, existing facet bridge, explicit provenance reader, and pure `diff_scholar_source(before, after, *, trigger=None)` comparison.
- `tests/workbench/test_scholar_source_projection.py`: C5/C6 regressions, preserving all prior tests.
- `tests/workbench/test_scholar_source_diff.py`: C1–C4 and provenance, identity, ordering, source-change and repeated-occurrence tests.
- `docs/SCHOLAR_INTERACTION_CONTRACT.md`, this acceptance document and the existing `docs/superpowers/plans/2026-09-20-k2bc.md`: specification and execution record.

The v1.1 authored fixtures were not edited. `test_annotation_projection.py` is unchanged and still validates the legacy adapter. QuestionPresenter, ReviewJob/service, parser/compiler/replay/Kernel/executor and UI files were not changed.

### Fixed expressions and Flow compatibility

The existing Kernel call is reused for both ordinary Term candidates and `fixed_expression_candidates`. Fixed candidates use their exact native span and a collision-safe `construction:<doc>:<start>-<end>:fixed_expression:<rule>` identity. They carry `origin=domain_kernel_fixed_expression`, `rule_id`, `proposal`, `parse_status=suggested`, and `public_kind=null`. Their absence of a syntax node is intentional, so it generates no missing-public-kind diagnostic. The Step builder continues to read native events only.

Flow status is `linked_source` when a selected definition exists; otherwise `ambiguous_source` only when the canonical linker reason is exactly `multiple source producers` (or `multiple compatible source producers`), or when more than one **distinct** `candidate_evidence.definition_id` has `compatible is True`. Otherwise it is `unresolved_source`. The existing linker's `multiple source producers` branch is emitted only for multiple viable producers. Named candidates and arbitrary prose are not compatibility evidence.

### Object/question identity and bridge

`facet_key` is `facet:` plus the first 24 hexadecimal characters of SHA-256 over compact, sorted-key UTF-8 JSON:

```text
[object_id, facet, branch_id, stable(normalized_semantic_target or semantic_key)]
```

Source addresses retain doc/reading/start/end/definition-kind identity and exclude quote/hash metadata. Source-supply targets use `{kind: source_supply, consumer: stable consumer anchor, formal, branch_id}`, replacing the opaque consumer definition ID even when a Flow cannot be projected. Term and quantity targets use the existing `normalize_decision_target`; invocation and branch scope are retained. Question wording, question IDs, UI state and decision IDs do not determine the facet key.

Each exact native input Term has a source-supply facet with its corresponding Flow in `related_object_ids`. Repeated uses of the same formal within one consumer refer to the same existing question from each occurrence. A Flow is primary when no exact Term exists. Reviewed facets retain their semantic key and explicit decision ID after the question disappears (`question_id=null`). Confirmed supply does not confirm term meaning. A linked source suppresses a stale supplied pending question. Related-object review badges are derived from this same bridge.

Quantity-Step and reviewed-relation/context related IDs are optional and left empty unless already proven; this pass does not guess invocation relationships or create another question lookup system. All required Term↔Flow relations are supported by native input references.

### Explicit decision provenance

Only named native fields are read: `decision_id`, `resegmentation_decision_id`, `decision_refs`, `adjudication_decision_refs`, and actual review IDs in `authorization_refs`. The reader visits owned `attributes`, `metadata`, `quantity_transition`, `reviewed_quantity`, and `reviewed_term_interpretations` containers; it never searches arbitrary source/evidence text. Authorization IDs must be present in the supplied decision/status collection. Known non-active references are excluded. Actions are taken from canonical decisions, the named resegmentation field, or the typed replay claim; otherwise action remains null.

Ownership is explicit:

- Term: exact replayed boundary/interpretation records and candidate authorization refs.
- Construction: its native candidate attributes (including reviewed term interpretations) or fixed candidate.
- Step: its native event and actually read/written values carrying explicit reviewed IDs.
- Flow: native import evidence plus replayed binding/runtime-parameter records matched to the exact consumer/formal/scope.

The real B1 boundary does not annotate its newly available Multiply candidate/event with the boundary ID. Therefore its Construction and Step have empty `decision_refs`; the changed Term has the boundary claim's explicit ID. `diff.trigger` reports the caller-provided observed transition and is never copied into object provenance. Real quantity decisions are retained exactly where native event/value metadata carries them; this is not a claim of sole authorship.

### ScholarSourceDiff/1

The diff reads two already-built snapshots, extending the existing stable golden view only with interaction facts. It does not invoke a compiler, parser, Kernel, question generator, or persistence path. It rejects changes to source_id/unit_id/doc_id/reading_id/text with `scholar_diff_source_changed`.

The result has `schema`, stable `source`, caller-supplied `trigger` (or null), six `layers` (`terms`, `constructions`, `steps`, `flows`, `review_facets`, `links`) and `summary.semantic_change_count`. Each layer has `added`, `removed`, `changed`; changed objects expose `id` or canonical `key` plus `changed_fields` entries containing `path`, `before`, `after`. The count is the number of added/removed/changed objects, not changed scalar fields. Duplicate comparison identities are rejected rather than hidden.

Object IDs identify object layers; facets use `facet_key`; links use relation/from/to/role/ordinal. The comparison retains composition order, candidate meanings/status/rule, reviewed claim meanings (including rejected expressions), explicit refs, Step operations/references/ports/labels/quantity-kind, Flow supply and stable producer identity, facet state and question presence, and link basis. Role/port/slot/consumer ordering is canonicalized. Actual question IDs remain live references in snapshots; diff compares their presence as `has_question`.

Ignored: native value/event/call IDs, opaque definition IDs, source/cache hashes and paths, verbose evidence and its ordering, candidate snapshot/cache IDs, question wording and opaque question-ID renumbering. Trigger modes are restricted to trial/saved/retracted/management/context. Input snapshots and trigger are not mutated.

### C1–C6 results and actual JSON

| Case | Verified result |
| --- | --- |
| C1 | Adding §15 changes only 章法 Flow and removes its pending source-supply facet: 2 changed/removed objects; no Term/Construction/Step/link churn. |
| C2 | With the right boundary already present, applying the left boundary exposes the real Multiply Construction/Step and native additional objects. 日率 Term already existed, so it is changed rather than falsely counted as newly added. Empty Multiply provenance remains empty; trigger names the left-boundary transition. |
| C3 | 章法 Flow changes unresolved→runtime-value-permitted; its source-supply facet keeps the same key and changes pending→reviewed, with no fabricated historical producer. |
| C4 | All three §38 supply Terms directly bridge to their Flow and the existing question; repeated same-consumer occurrences and Flow-primary fallback also pass. |
| C5 | C08 `實如法而一` appears as a suggested fixed-expression Construction. Removing only the Kernel suggestion leaves Step output identical. |
| C6 | Three named candidates with 0/1 compatible producers remain unresolved; two compatible producers are ambiguous. §15 linked-source behavior remains unchanged. |

C3 also exposes one **real existing QuestionPresenter** pending `context_material` facet at the divide Construction after runtime permission. The diff retains that additional question instead of suppressing it to produce an artificially minimal result; no question or historical interpretation was invented by this projector.

The existing `.cache/scholar-source-projection/proc38.actual.json`, `proc38.stable.json`, `proc38.with-section15.actual.json` and `proc38.golden-diff.json` are refreshed. The new standalone `.cache/scholar-source-projection/interaction-acceptance.json` holds C1–C6 actual projection/diff evidence. It is an audit artifact, not another store or semantic truth.

Final focused tests: 42 passed. Existing no-context full golden and full §15 patched golden equality pass with the authored fixtures unchanged. Independent read-only review found no remaining in-scope defect after the repeated-occurrence bridge and ordering controls; adversarial order-only changes produce a zero-change diff.

Broader regression: Workbench 107, Inspector 52, adjudication 128, parser 61, parser-v3 94, rescue 78, Kernel 25 and reconciliation 5 pass. Top-level discovery runs 87 tests, with the same two documented `test_pattern_importer` frozen-ontology errors (85 pass); their frozen input was not changed. No renderer, browser acceptance claim, source edits, private NOTE/LOG changes, commit or push in this pass.
