# Scholar Renderer v0.2 — 去重与通用 eligibility 验收

2026-09-20。基于现有 v0.2 完成，没有重做 renderer。此前 golden 待决项已按用户批准的 interaction-contract revision 完成。

## 精确文件清单

- `workbench/question_presenter.py`：通用 exact Term eligibility，无词面/Proc 白名单。
- `workbench/scholar_renderer.py`：单一 Term hover 内容；沿用 ontology authored 定义与 Step 对齐。
- `tools/parser_inspector/source_annotation.mjs`：删除正文 gloss/占位宽度；Term 字形触发黑色 hover；不设置原生 title。
- `tools/parser_inspector/source_annotation.css`：删除 inline gloss 样式，保留 badges、source/rail/Step 与黑色 tooltip。
- `tools/parser_inspector/review_panel.py`：解释只在右栏展示一次；bare Term overview 与 exact question 分流，保留来源交互。
- `tests/workbench/test_question_presenter.py`：通用契约、grounding、重复 occurrence、adopt/reject 局部性、固定表达式及无白名单回归。
- `tests/workbench/test_scholar_renderer.py`：单/多/已审 Term hover 和 ontology fallback 回归。
- `tests/workbench/scholar-renderer-layout.test.mjs`：保留 offset、跨行 identity、Unicode 测试，删除已取消的 inline gloss 占位测试。
- `tests/workbench/scholar-renderer-browser.mjs`：去重、named-output badges、真实 interpretation 保存与 source attachment 浏览器验收。
- `tests/fixtures/scholar_source_projection/proc38-golden-projection.json`：仅两个新增 pending facet，count 7 → 9。
- `tests/fixtures/scholar_source_projection/proc38-section15-context-invariant.json`：仅 facet count 6 → 8。
- 本文件：最终报告，替换此前待决进度记录。

`source_annotation.py` 沿用原资源加载入口，无需修改。parser/adjudication/Kernel/projection 的 42 个受保护文件 SHA-256 与 v0.2 开始时一致，ontology 只读。没有修改 Program IR、executor、canonical source data 或私人 NOTE/LOG。

## 通用 eligibility 与契约

既有非 heading construction 中的 canonical slot 必须满足：native kind 为 Term；candidate 与该 slot 自身的 doc_id、reading_id、start、end、quote 全部相等；candidate compatible 且有实际 semantic expression。unknown opaque placeholder 不构成可采纳词义。父 construction 包含或相同词面不够。

不再排除 name/remainder_name。使用既有 adopt_term_candidate/reject_term_candidates 构造原 set_term_interpretation claim，按原 exact anchor/branch 处理决定。不新增 action；保留既有 heading 排除。compatible concept candidate 也仍须满足 canonical Term 条件。

先加失败测试，再实现。六项 generic contract tests 通过后才更新 fixture。合成术文「名為積日，不滿為日餘，名為積日」验证 naming 与 remainder naming；同词不同位置使用独立 exact anchor。adopt/reject 后另一 occurrence 的完整 question/options 不变，claims 和 decision_refs 仍为空。没有 compatible candidate 或自身 grounding 不生成机会。「實如法而一」的 fixed-expression Construction 没有 fake review facet/action。AST 检查 presenter 不含 named-output 词面或 Proc.38 白名单。

## Golden 精确变化

仅新增：

```json
{"object_id":"term:sifen:38:26-28","facet":"term_meaning","status":"pending"}
{"object_id":"term:sifen:38:32-34","facet":"term_meaning","status":"pending"}
```

no-context facets 7 → 9；§15-context facets 6 → 8。

写入前，将 actual 中仅这两个新增 facet 去除，与旧完整 expected 做 exact equality，确认没有其他漂移。更新后原 full golden exact equality 仍通过，没有 subset assertion。Terms、semantic candidates、Constructions、Steps、Flows、Links、§15 producer patch、diagnostics 均保持原预期。fixture 文本 diff 也仅有上述两条记录与 count。

## UI 去重与操作链

正文只留 Term 虚线下划线、小 facet badges、Construction rail、Step lane。删除英文 gloss DOM/CSS 及其插入空白。Term glyph 上唯一黑色自定义 hover 显示当前解释：单候选为真实解释，多候选为 N machine suggestions 并按已有顺序列出，已审为 reviewed interpretation。没有原生 title 属性。完整候选、composition、context 保留在右栏。

Construction hover 读取 ontology construction label/definition；Step hover 读取 operation label/definition。缺失时显示 No authored description registered，没有新增解释词典。badge hover 读取已有 QuestionPresenter title；已审 facet 显示原有状态/action。

Step 主层为 load/input/subtract 1；operand/multiply/previous result；divide with remainder/divisor/quotient cue。threshold 只有一个 Step，显示 [35,37] lower bound / [37,39] test ≥，Judgment 下没有第二个 operation marker。supporting constructions 调换顺序也保持对齐。多重或缺失精确 cue 继续显示 broad/unavailable。

裸 Term 点击只给 review overview，不自动选 question；Review/badge 才进入原 exact facet/question。count/context ownership 不移动。原始 port/code 留在 Evidence，右栏采用已有 ontology 标签。

来源帮助仅在 source_supply 下展示 canonical producer candidates、registered hits、other exact occurrences；后两类明确标 Search hints — not yet linked。Inspect 显示完整 native unit 文本与精确命中。仅当前问题有 attach_context、adapter 可生成完整 document 且尚未加入时，提供 Add as context & re-run。

```text
Inspect → Add as context & re-run
→ _option_submission → service.review_decision(action=attach_context)
→ _submit → apply_review_job_changes → backend recompile
```

没有 bind_value 决定，不从 search hint 自动制造 producer。已加入或不支持附加的命中保持 Inspect 只读。

## 验证结果

- 84 项定向 Python 回归通过，覆盖 QuestionPresenter、renderer、full golden、§15 invariant、diff、annotation projection、reviewed syntax grounding。
- 14 项 Streamlit AppTest 通过。
- 3 项 Node layout 测试通过。
- 当前代码树、隔离 ReviewJob 存储的 Playwright 浏览器验收通过，pageerror 为零。覆盖无正文 gloss/原生 tooltip、黑色 hover、原始 offset、无横向溢出、glyph rail geometry、overview/exact question、ontology hover、单 threshold、两个真实 named-output meaning badges、真实 interpretation 保存及局部性、diff/provenance、Inspect 与仅 attach_context 的重编译。
- git diff --check 通过；42 个受保护文件逐字节 hash 不变。

扩大运行 unittest discover -s tests/workbench -q：137 项中 135 通过，2 项旧 presentation 路径 error：syntax:ReviewedCandidate、cause:ReviewedSlotMissingExactGrounding。两者都因 ontology 未登记该 code；独立进程换回修改前 QuestionPresenter 后同样复现，未由本轮 eligibility 引入。遵守边界，本轮未补 ontology 定义或修改旧 presentation；不声称整个 Workbench 全量回归全绿。[复现记录](../tmp/scholar-renderer-v02/preexisting-workbench-errors.json)。

## 更新截图

1. [Term 多候选黑色 hover](../tmp/scholar-renderer-v02/00-term-machine-hover.png)
2. [Proc.38 总览](../tmp/scholar-renderer-v02/01-proc38-overview.png)
3. [章法 review overview](../tmp/scholar-renderer-v02/02-zhangfa-review-overview.png)
4. [章法 exact meaning question](../tmp/scholar-renderer-v02/03-zhangfa-exact-meaning.png)
5. [source_supply / Inspect / context action](../tmp/scholar-renderer-v02/04-zhangfa-source-supply.png)
6. [積月 suggestions 与 meaning?](../tmp/scholar-renderer-v02/05-accumulated-months-local.png)
7. [閏餘 exact meaning question](../tmp/scholar-renderer-v02/05-named-remainder-meaning.png)
8. [load / input / subtract](../tmp/scholar-renderer-v02/06-load-input-subtract.png)
9. [multiply](../tmp/scholar-renderer-v02/07-multiply.png)
10. [lower bound / test ≥](../tmp/scholar-renderer-v02/08-threshold.png)
11. [Construction authored hover](../tmp/scholar-renderer-v02/09-construction-hover.png)
12. [Operation authored hover](../tmp/scholar-renderer-v02/09-step-hover.png)
13. [确认与 diff](../tmp/scholar-renderer-v02/10-post-confirm.png)
14. [Reviewed Term hover](../tmp/scholar-renderer-v02/10-reviewed-term-hover.png)
15. [独立 C3](../tmp/scholar-renderer-v02/11-divmod-context.png)
16. [context 附加后](../tmp/scholar-renderer-v02/12-context-attached.png)

[浏览器断言结果](../tmp/scholar-renderer-v02/acceptance.json)。自动化保存只写隔离存储，不覆盖人工研究决定。

[当前 renderer 预览](http://127.0.0.1:8506/?review_job=scholar-renderer-correction-20260920)