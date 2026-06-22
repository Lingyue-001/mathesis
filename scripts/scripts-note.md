你现在需要的全局图可以这样收束：**这个项目的本体不是 agent、不是网页、不是数据库，而是一个“面向历史科学文本的 evidence-grounded AI extraction pipeline”。** 也就是：

> **Cullen-grounded RAG + structured extraction + symbolic validation + procedure vectorization pipeline**

它的行业化版本不是“我做了一个古代历法小工具”，而是：

> **我构建了一个能把高专业门槛文献转化为可检索、可抽取、可验证、可比较结构数据的 AI 文档处理系统。**

这才是 portfolio 级别的定位。

---

# 一、整体目标：不是自动读懂历法，而是自动建立“可审计的理解结构”

最终目标不是让 AI 自己“懂”三统历、四分历、九执历，而是让系统做到：

```text
Cullen 作为权威解释层
+
原文作为 primary evidence
+
AI 负责候选抽取
+
validator 负责复算和证据检查
+
procedure vector 负责跨文本比较
```

换句话说，你要搭的是一个**可审计阅读机器**：

```text
原文一句话
→ 找到 Cullen 对应解释
→ 抽出 quantity / operation / procedure
→ 复算是否成立
→ 标出证据来源
→ 转成可比较向量
→ 生成 review queue
```

这套东西和 Writing Through Time 的高技术化思路是同构的：它不是只展示材料，而是把人文学对象拆成可记录、可建模、可量化分析的 features。Writing Through Time 明确把埃及手写文字演变放进 large-scale hieratic data、digital and biomechanical modeling、quantitative approach 的框架里；AKU 数字古文字项目也强调数据库、sign repertoire、ligatures、metadata 和 modular analysis。你的项目对应的对象不是字形，而是历算 procedure；对应的 features 不是笔画/字形，而是 quantity、operation、unit、cycle、correction、output、validation status。([Writing Through Time][1])

---

# 二、总架构：七层，而不是一个大 agent

现在应该按 layer 看，而不是按工具名看。

## Layer 0 — Raw source layer：原始材料层

已有：

```text
Cullen PDF
三统历原文
四分历原文
九执历原文
```

作用：保留原始证据，不直接改动。

当前 Codex 已经开始从三统/四分/九执原文生成 `source_spans` 和 `procedure_IR`，这一步没有跑偏。但 Cullen 现在还只是 PDF 文件，还没有真正变成机器可用的权威层。

---

## Layer 1 — Cullen Oracle layer：权威解释层

这是下一步的绝对核心。

目标是把 Cullen PDF 从“文件”变成：

```text
page-level text
→ chunk-level text
→ searchable index
→ CullenClaims
→ formula / term / procedure oracle
```

产物应该至少包括：

```text
cullen_pages.json
cullen_chunks.json
cullen_claims.json
cullen_terms.json
cullen_formulas.json
cullen_alignment_report.json
```

技术方案：

```text
PDF text extraction: PyMuPDF / pdfplumber
chunking: heading / section / paragraph / procedure-like markers
storage: JSONL / Parquet
search baseline: SQLite FTS5 / BM25 / ripgrep
```

这一层先不需要 embedding。先做 clean chunks + metadata。没有这个，后面的 RAG 会变成垃圾进垃圾出。

效果：系统以后不是“问 AI 你懂吗”，而是“这个 operation 有没有 Cullen evidence 支撑”。

---

## Layer 2 — Primary text segmentation layer：原文切片层

Codex 现在已经在做：

```text
三统历 / 四分历 / 九执历原文
→ source_spans
→ procedure candidates
```

这一层目标不是解释，而是**稳定定位**：

```json
{
  "span_id": "sifen_tianzheng_001",
  "calendar": "sifen",
  "procedure": "推天正朔日",
  "raw_text": "...",
  "line_start": "...",
  "line_end": "..."
}
```

技术方案：

```text
regex segmentation
rule-based heading detection
procedure markers: 推X术 / 推X章
```

效果：后面每条 quantity / operation 都能回到原文 span。

这一层可以继续用本地脚本，不需要 agent。

---

## Layer 3 — Retrieval grounding layer：证据检索层

这里才开始用 RAG。

RAG 的作用不是“让 AI 回答问题”，而是：

> 给每个原文 span 找 Cullen 里最相关的解释、术语、公式、procedure 说明。

工程顺序应该是：

```text
1. keyword / BM25 baseline
2. embedding index
3. hybrid retrieval
4. optional reranker
```

为什么不能一开始就 embedding？因为你的材料有大量专业术语，exact keyword / BM25 往往比纯语义检索更可靠。现在 production RAG 常见做法不是单纯 vector search，而是 hybrid retrieval + reranking + evaluation。GraphRAG 和高级 RAG 的工程文档也强调，检索层要结合结构、关系和重排序，而不是“扔进向量库就完事”。([Microsoft GitHub][2])

这一层的输出不是答案，而是：

```json
{
  "source_span_id": "sifen_tianzheng_001",
  "retrieved_cullen_chunks": [
    {
      "chunk_id": "cullen_sifen_new_moon_003",
      "score_bm25": 8.7,
      "score_embedding": 0.82,
      "rank_fused": 1
    }
  ]
}
```

效果：每个原文段落进入抽取前，已经带着 Cullen evidence。

---

## Layer 4 — Structured extraction / IR layer：结构化抽取层

这一层把原文 + Cullen evidence 转成 `ProcedureIR`。

不是让 AI 写解释，而是强制输出 schema：

```json
{
  "procedure_id": "jiuzhi_jiri_xiaoyu",
  "quantities": [],
  "operations": [],
  "source_span_id": "...",
  "cullen_evidence_ids": []
}
```

技术方案：

```text
OpenAI Structured Outputs / JSON schema
Pydantic schema validation
optional Instructor
regex pre-extractor for common formula patterns
```

这和近年的 structured extraction / document AI 趋势一致：不是让 LLM 自由总结，而是让它把非结构化文档转成符合 schema 的结构数据。DocETL 这类系统也正是把复杂文档处理看成 declarative LLM-powered pipeline，并通过 agentic rewriting / evaluation 优化复杂抽取任务。([arXiv][3])

效果：文本开始变成可计算对象，而不是摘要。

---

## Layer 5 — Validation / evaluation layer：验证层

这是可信度核心，比 agent 更重要。

验证分四类：

```text
1. Schema validation
   输出是否符合固定 schema。

2. Source grounding
   每个 claim 是否能回到原文 span。

3. Cullen grounding
   每个重要 operation 是否能找到 Cullen chunk / claim 支撑。

4. Arithmetic validation
   能算的关系是否能用 exact arithmetic 复算。
```

例如：

```text
闰法 19 × 日法 81 = 统法 1539 → PASS
积日 mod 60 → 甲子次 → TEXT_EXPLICIT / CHECK
积日 mod 7 → 七曜直日次 → TEXT_EXPLICIT / CHECK
```

技术方案：

```text
Pydantic
custom validators
Fraction / SymPy exact arithmetic
pytest
evaluation_report.json
```

这层要输出行业化指标：

```json
{
  "retrieval_top_k_coverage": "...",
  "schema_valid_rate": "...",
  "source_grounded_rate": "...",
  "cullen_grounded_rate": "...",
  "arithmetic_pass_rate": "...",
  "review_queue_rate": "..."
}
```

效果：项目从“AI 抽了东西”升级成“AI 抽取结果被系统化评估”。

这是 portfolio 里最重要的区别点。

---

## Layer 6 — Procedure vectorization layer：比较向量层

这里用的是第二种“向量化”：不是 embedding，而是**可解释 procedure vector**。

它从 validated IR 自动生成：

```json
{
  "procedure_id": "jiuzhi_jiri_xiaoyu",
  "uses_accumulated_days": true,
  "uses_quotient_remainder": true,
  "cycle_moduli": [60, 7],
  "operation_sequence": ["quotient_remainder", "mod_cycle", "mod_cycle"],
  "outputs": ["甲子次", "七曜直日次"]
}
```

技术方案：

```text
rule-based feature extraction from validated IR
pandas / Polars
similarity metrics:
  - Jaccard over binary features
  - cosine over one-hot operation vectors
  - later graph similarity
```

效果：三统历、四分历、九执历进入同一个比较体系。

这才是你论文/DH 项目的学术贡献核心：

```text
不是“AI 找到几个词”
而是“把历算 procedure 转成可比较、可验证、可迁移的结构向量”
```

---

## Layer 7 — Agentic optimization layer：自动修复/优化层

这一层最后加，不是一开始加。

DeepAgent / LangGraph 的位置是：

```text
外层：DeepAgent / agentic workflow
内层：deterministic pipeline
```

Deep Agents 官方定位就是面向 long-running tasks，带 planning、context management、subagent orchestration、virtual filesystem 等能力；DSPy 则更适合在有 evaluation set 后优化 prompt / pipeline，而不是一开始替代 schema 和 validator。([LangChain Docs][4])

什么时候加 agent？

```text
当你已经有：
1. Cullen chunks
2. retrieval baseline
3. structured extractor
4. validator
5. evaluation metrics

但 review_queue 太大时
再加 agentic repair。
```

agent 做什么？

```text
FAIL_NO_CULLEN_EVIDENCE → 改 query 重新检索
FAIL_SCHEMA → 按 schema 重新生成
FAIL_ARITHMETIC → 检查数字解析/operation 类型
LOW_CONFIDENCE → 找更多 Cullen evidence
REPEATED_FAILURE → 提出 schema extension 或新 extractor
```

效果：减少你的人工校对，而不是取代 Cullen 和 validator。

---

# 三、分步实现路线

## Phase 1 — 已完成：本地 skeleton pipeline

当前状态：

```json
{
  "source_spans": 212,
  "procedures": 19,
  "validations": 7,
  "review_items": 2
}
```

产物：

```text
cullen_oracle.json
source_spans.json
procedure_IR.json
validation_report.json
review_queue.json
procedure_vectors.json
```

判断：**没有跑偏，但它只是 skeleton。**
偏弱点：Cullen 还没有真正接入，所以现在的 `cullen_oracle.json` 不能算 oracle，只能算占位。

---

## Phase 2 — 下一步：Cullen Oracle v0

只做 Cullen，不扩大历法范围。

目标：

```text
Cullen PDF → page text → chunks → search index → claims
```

技术：

```text
PyMuPDF / pdfplumber
JSONL / Parquet
SQLite FTS5 / BM25
regex + optional LLM structured extraction
```

输出：

```text
cullen_pages.json
cullen_chunks.json
cullen_claims.json
cullen_terms.json
cullen_formulas.json
```

成功标准：

```text
至少抽出 20–50 条 CullenClaims
覆盖：
- 三统历 constants
- 三统历推正月朔
- 四分历推天正朔日
- 四分历推没灭
```

warning：**不要直接把 Cullen 转成一个大 md 就完事。** 要保留 page number、chunk id、section metadata，否则后面没法做证据链。

---

## Phase 3 — Retrieval grounding v0

目标：让每个原文 span 自动找到 Cullen evidence。

技术：

```text
BM25 / FTS first
embedding second
hybrid retrieval third
```

输出：

```text
retrieved_evidence.json
retrieval_report.json
```

成功标准：

```text
给定 10 个已知测试 query，top-5 里能找到相关 Cullen chunk。
```

warning：**embedding 不要替代 exact search。** 你的术语非常硬，exact retrieval 是强 baseline。

---

## Phase 4 — Grounded IR extraction

目标：不是从原文裸抽，而是：

```text
source_span + retrieved Cullen evidence → ProcedureIR
```

技术：

```text
OpenAI Structured Outputs / schema-constrained extraction
Pydantic
regex pre-extraction
```

输出：

```text
candidate_ir.json
validated_ir.json
review_queue.json
```

成功标准：

```text
每个 operation 至少有：
- source_span_id
- source_phrase
- cullen_chunk_id 或 cullen_claim_id
- op_type
- inputs / output
```

warning：**没有 Cullen evidence 的抽取不能标成 validated。** 顶多是 candidate。

---

## Phase 5 — Validation + evaluation

目标：把“可信度”量化。

技术：

```text
exact arithmetic
schema validation
Cullen alignment validation
evaluation metrics
```

输出：

```text
validation_report.json
evaluation_report.json
```

指标：

```text
schema_valid_rate
source_grounded_rate
cullen_grounded_rate
arithmetic_pass_rate
review_queue_rate
```

成功标准：

```text
三统历 constants 中可算关系大部分 arithmetic PASS。
四分历和九执历相关 procedure 至少能 source-grounded + cullen/mak-grounded。
```

warning：**不要把 textual-algorithmic validation 和 modern astronomical accuracy 混在一起。** 现在验证的是“文本/算法内部一致性”，不是现代天文学真值。

---

## Phase 6 — Procedure vectorization

目标：从 validated IR 自动生成比较向量。

技术：

```text
feature extraction from IR
pandas / Polars
Jaccard / cosine / graph features
```

输出：

```text
procedure_vectors.csv
comparison_report.md
```

成功标准：

```text
能清楚显示：
三统历/四分历/九执历都可进入：
accumulated day
quotient-remainder
cycle modulus
operation sequence
outputs

九执历比四分历多出 cycle_moduli = [7]，即七曜直日。
```

warning：**procedure vector 必须来自 validated IR，不能从未验证 candidate 直接生成最终结论。**

---

## Phase 7 — Agentic repair / DeepAgent

目标：减少人工 review，不是替代 pipeline。

技术：

```text
DeepAgent / LangGraph / DSPy later
```

什么时候上：

```text
当 Phase 2–6 跑通后，review_queue 仍然太大。
```

效果：

```text
自动重检索
自动重抽取
自动修 prompt
自动提出 schema extension
自动重跑 validation
```

warning：**不要让 agent 自己写入 gold。** 它最多写入 candidate 或 repaired_candidate，最终还是看 validator 和 review policy。

---

# 四、我们之前局部讨论放在一起，有没有偏差？

有三处需要修正。

## 偏差 1：一开始太早讨论 agent

现在结论：**agent 不是核心，不是第一步。**

核心是：

```text
Cullen Oracle
+ retrieval grounding
+ structured IR
+ validation
+ procedure vector
```

Agent 是后置优化层。

---

## 偏差 2：把“向量化”说得太泛

现在要分清：

```text
embedding vectors：用于 Cullen retrieval
procedure vectors：用于历法比较
```

embedding 是工程工具；procedure vector 是研究成果。

---

## 偏差 3：Cullen 没有被放到足够中心

现在必须修正为：

```text
Cullen is not a reference note.
Cullen is the oracle layer.
```

没有 Cullen chunk / claim / alignment，整个工具不能自称可信。

---

# 五、最大的坑和提前 warning

## 坑 1：过早上 DeepAgent

会烧时间、烧 token、产生黑箱结果。
现在不做。

## 坑 2：过早做前端/可视化

会让项目又变成展示壳。
现在不做。

## 坑 3：Cullen PDF 粗暴转 md

会丢页码、证据链、chunk id。
必须 page/chunk 化。

## 坑 4：纯 embedding RAG

会漏掉专业术语和原文-翻译错位。
必须 BM25 + embedding hybrid。

## 坑 5：procedure vector 从未验证 IR 生成

会让错误结构进入比较结论。
必须标 provisional / validated。

## 坑 6：review_items 太少反而危险

早期如果 Cullen 没接入，很多东西应该是 `missing_cullen_grounding`。
review 少不代表准，可能是 validation 不够严格。

## 坑 7：把现代天文准确性混进第一版

这会爆炸。
第一版只验证 textual / algorithmic consistency。

---

# 六、最终全局路线一句话

现在全局路线应该定为：

```text
先把 Cullen 做成 machine-actionable oracle；
再用 hybrid RAG 把原文 span 绑定到 Cullen evidence；
再用 structured extraction 生成 procedure IR；
再用 symbolic validators 复算和检查证据；
再从 validated IR 生成 procedure vectors；
最后才用 agentic repair 降低人工 review。
```

这条线是收束的，没有偏离你的目标：**最大化利用 Cullen 降低你的天文学学习成本，同时做出一个真正有 AI/tech 工程含量的文档抽取与验证系统。**

[1]: https://writingthroughtime.github.io/?utm_source=chatgpt.com "Writing Through Time"
[2]: https://microsoft.github.io/graphrag/?utm_source=chatgpt.com "Welcome - GraphRAG"
[3]: https://arxiv.org/abs/2410.12189?utm_source=chatgpt.com "DocETL: Agentic Query Rewriting and Evaluation for Complex Document Processing"
[4]: https://docs.langchain.com/oss/python/deepagents/overview?utm_source=chatgpt.com "Deep Agents overview - Docs by LangChain"
