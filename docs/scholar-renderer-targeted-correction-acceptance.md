# Scholar Renderer v0.1 定向修正验收

2026-09-20。以已有 renderer 为基线，仅修改展示与选择行为；本轮未修改 parser、compiler、Kernel、canonical projection 或来源正文。没有更新私人 NOTE/LOG。

## 本轮文件

| 文件 | 修正 |
| --- | --- |
| `workbench/scholar_renderer.py` | 单建议真实 gloss、精确 operation/role 映射、全对象标签索引、选择范围内的 canonical 关系与 source assistance |
| `tools/parser_inspector/source_annotation.py` | 沿用原组件入口，加载独立 CSS/JS 资源 |
| `tools/parser_inspector/source_annotation.mjs` | 原始 offset 折行、分层 geometry、跨行 fragment、原子 object/facet 点击状态 |
| `tools/parser_inspector/source_annotation.css` | 中文正文、注释、括号、操作 lane 的层次与密度 |
| `tools/parser_inspector/review_panel.py` | 70/30 布局、严格局部右栏、source facet 门控、移除旧左栏残留、保存后的 diff 高亮 |
| `tests/workbench/test_scholar_renderer.py` | suggestion、grounding、重复 operand、fallback、局部关系、C3、不可变性回归 |
| `tests/workbench/scholar-renderer-layout.test.mjs` | 原始 codepoint offset、Unicode、跨行统一 ID 测试 |
| `tests/workbench/scholar-renderer-browser.mjs` | 当前代码树启动独立服务，真实浏览器点击、保存、几何与截图验收 |
| 本文件 | 验收记录 |

## 展示路径

每行按实际 glyph cell 宽度累加，在可用列宽内优先选择标点断点；不含 Proc.38 硬编码断行。行保留原文半开区间 `row_start / row_end`，JavaScript 用 Unicode codepoint 数组与 Python offset 对齐。

glyph 层只包含原文字符；badge、gloss、construction rail、step token 位于独立层。测量只取 glyph bounding box。改变 gloss 宽度不会改变 rail 的 x 或 width；注释拥挤只增加注释层高度。

Construction 与行区间求交得到 visual fragment；保留原始 span 和同一个 canonical ID，后续片段标 continuation。重叠 rail 使用多个局部 lane，不拆 semantic object。

Step 对齐来自已登记 production、canonical slot spans、实际 operation 和 Construction↔Step 关系的有限映射。`置` 对应 load，value 对应 input，`減` 与 decrement 对应 subtract 1；乘法以 left/right 的各自 slot 为锚，操作标记在 `乘`，上游引用显示 prior/right。DivMod divisor 保持局部 anchor，quotient/remainder 用现有输出标签显示在右栏。

右栏读取所选对象的一跳 canonical links 及显式 Step inputs/outputs，不递归穿图找问题。隐藏于正文的 component Terms 也进入标签索引，因此显示 `積 + 月` 等文字。`積月` 只显示 composition、命名及 quotient 角色，无无关 Flow/search dump。

仅选中 `source_supply` 才查找来源帮助：现有问题的 bindable canonical producer options → 已登记参数 exact hits → 其他 exact occurrences。后两类明确为未链接的搜索提示，不产生绑定或人工 provenance。C3 只由该 Construction 的 context facet 展示原有 cause/missing_inputs 和问题。

facet 点击一次性提交 object ID、facet key、已有 question ID 与事件 nonce；点击裸对象会清掉旧 facet，组件 rerun 不会恢复过期选择。确认仍使用原 ReviewJob/service，随后读取 ScholarSourceDiff；只显示 graph 原有 decision_refs。

## 验证

- Python：64 项通过，覆盖 renderer、Scholar projection、full golden exact equality、§15 invariant、ScholarSourceDiff、annotation projection、reviewed syntax grounding。
- Streamlit AppTest：14 项通过，覆盖既有选择、确认、上下文、撤销及 diff 路径。
- Node layout：3 项通过。
- Playwright 实际浏览器：通过；使用当前树模块与隔离 ReviewJob 存储，保存不会修改用户既有判断。断言多行、无全局横向溢出、原文完整、glyph-only DOM、gloss 不改变 rail geometry、精确 operation cues、局部右栏、来源帮助门控、真实 decision 保存、不伪造 Step provenance、C3 独立及选择不会回跳。浏览器 pageerror 为零。
- `git diff --check` 通过；只输出已有文件的换行符提示。

复现命令：

```powershell
python -X utf8 -B -m unittest tests.workbench.test_scholar_renderer tests.workbench.test_scholar_source_projection tests.workbench.test_scholar_source_diff tests.workbench.test_annotation_projection tests.parser_v3.test_reviewed_syntax_grounding -q
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tools.parser_inspector.test_review_panel -q
node --test tests/workbench/scholar-renderer-layout.test.mjs
node tests/workbench/scholar-renderer-browser.mjs
```

## 七张截图

1. [Proc.38 多行总览](../tmp/scholar-renderer-correction/01-proc38-overview.png)
2. [入蔀年选择与候选](../tmp/scholar-renderer-correction/02-entry-year-selected.png)
3. [load / input / subtract 1](../tmp/scholar-renderer-correction/03-load-input-subtract.png)
4. [積月局部关系](../tmp/scholar-renderer-correction/04-accumulated-months-local.png)
5. [章法 source_supply](../tmp/scholar-renderer-correction/05-zhangfa-source-supply.png)
6. [DivMod C3 context](../tmp/scholar-renderer-correction/06-divmod-context.png)
7. [确认后 reviewed gloss 与 Last change](../tmp/scholar-renderer-correction/07-post-confirm.png)

[机器验收结果](../tmp/scholar-renderer-correction/acceptance.json)。截图使用 1450px 桌面宽度；step 近景是对应 source row 的裁图。

## 保留的能力边界

- 未登记或 grounding 不足的生产式不推测精确 cue；使用原 Step source span 作 broad 展示，在技术细节标记 unavailable。完全无局部 span 的值不伪造 glyph anchor。
- `count?` 的 canonical owner 是 Load Construction，因此位于对应括号旁；不会为仿照示意图将其冒充为入蔀年 Term facet。
- fixed expression 保持 suggested/read-only，没有新增直接人工 adjudication。
- canonical producer 区只列现有问题提供的可绑定候选。原始不兼容候选 evidence 仍保留在对象技术证据中；exact corpus hit 不等于可用 producer。
- 旧 `sifen-38` ReviewJob 的 analysis identity 已过期，保持只读；另建 `scholar-renderer-correction-20260920` 预览会话，没有迁移或覆盖旧决定。

当前树预览：[Proc.38 renderer](http://127.0.0.1:8506/?review_job=scholar-renderer-correction-20260920)。此为本机开发服务，关闭服务后链接失效。
