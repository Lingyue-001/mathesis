# K1 integration and evidence

本轮基点：`63ed5c2b12dbe6501f5f607ec7a062c9e7b50d46`。
当前实现范围：K0–K1、K1.1 关系分层修正、K1.5 只读候选展示。后端选项仍默认关闭；固定天正术 Inspector 开启展示。未进入 K2/K3，未修改人工决定、canonical data 或原 parser 语义。

下列 K1 接线及测试记录保留当时基线；K1.1/K1.5 的变更与验收记录见文末。K1 阶段的“HTML 不变／未修改 UI”和 registry 原字节描述不再代表 K1.5 的当前展示契约。

## 使用与结果

```python
from tools.parser_inspector.readable import compile_view

view = compile_view(packet, include_term_semantics=True)
bundles = view['term_semantics']  # doc_id -> TermSemanticCandidates/1
```

旧文件输出入口：

```python
from tools.parser_inspector.runner import run

result = run(packet, 'compile', include_term_semantics=True)
bundles = result['term_semantic_candidates.json']
```

两入口均调用 `domain_kernel.engine.suggest_packet_semantics`。`term_regions` 是 doc_id → SourceAnchor 列表，仅指明可作名词分析的原文跨度，不提供词义、单位或授权。裸词可直接通过 `suggest_term_semantics(doc, term_regions=...)` 分析；没有明确 region 时不推断名词性。

实际四分历 `sifen:section:39` 在两个入口生成同一推导：

```text
入蔀積月  C06 localized_quantity(scope.bu, accumulation(time.month))
├─ 入    LC12
├─ 蔀    LC14
└─ 積月  C01
   ├─ 積 LC06
   └─ 月 LC02
```

这只是保留多义的候选之一。`support_status=proposed`、`authorization_status=not_authorized`、`claim_authority=S`；局部类型相容不授予计算权限。未知中保留 semantic_expression，不推定 quantity 或 scope。C08 只提出 division_construction，所需技术语境保持 underdetermined，不输出数字 1。

## 文件职责与原生边界

| 文件 | 用途 |
|---|---|
| `domain_kernel/__init__.py` | 可选模块边界 |
| `domain_kernel/engine.py` | 只读 registry 投影、现有词法/句法适配、统一组合器、来源/推导校验、packet API |
| `domain_kernel/kernel.registry.json` | review2 原字节定义；只消费候选子集 |
| `domain_kernel/kernel.schema.json` | review2 原字节共享 schema；未冒充全部生产化 |
| `domain_kernel/output.schema.json` | 引用共享 Expression/SourceAnchor/SemanticCandidate 的 K1 封装 |
| `domain_kernel/consumer-manifest.json` | producer/validator/consumer/allowed_effect/effect_test/status |
| `domain_kernel/docs.py` | 复用交接包确定性 renderer，追加实际能力记录；唯一新增工具命令 |
| `tests/domain_kernel/test_engine.py` | 组合、来源、权限、schema、隔离与负例 |
| `tests/domain_kernel/test_docs.py` | 文档漂移与能力消费记录检查 |
| `tests/fixtures/domain_kernel/paper-probes.json` | review2 原字节人工预期，仅测试读取 |
| `tools/parser_inspector/test_term_semantics.py` | 两入口同源、开关、错误隔离及 native 非回归 |
| `docs/domain-kernel/SPEC.md`、`PAPER_PROBES.md` | 原规格和纸面预期，保留原身份 |
| `docs/domain-kernel/SCHEMA_REFERENCE.md` | 从 schema/registry/manifest 再生的参考说明 |
| 本文 | 实施证据、命令、限制 |

仅两个既有生产函数变化：

- `runner.run` 增加默认关闭的参数；每次清理自己唯一新增的候选文件；原生 artifact 完成后独立生成候选。候选失败单独报错，原生失败时标 blocked，旧 parser artifact 和 graph parent 不变。
- `readable.compile_view` 保留 automatic/new_session/reviewed 各一次；开启时追加两个顶层键；本函数外原字节、HTML 和 render 行为保持。

`validate_term_bundle(bundle, doc, *, registry=None)` 在规定的两参数接口上增加可选 keyword，用于显式验证自定义 registry，避免全局隐式缓存。运行时使用标准库校验来源、推导和权限；完整 JSON Schema 标准校验只在开发测试中运行，通过本地 registry 注册 `$id` 和文件引用，禁止联网解析。

候选 identity 包含 source/reading、运行知识视图、共享与输出 schema、engine、复用 parser 模块的指纹和选项。dict 键规范化，所有语义有序数组保留顺序。现有 freshness 只检查 corpus；本轮没有新增 kernel/code watcher。

## 实测范围

| Probe | 已验证的 K1 部分 | 未实施 |
|---|---|---|
| P01 | 积月叶节点与 C01；禁用 TERMS 后成立 | 执行语义 |
| P02 | 入蔀年 C06；保留原 grammar preview | ordinal/base/boundary 授权 |
| P03 | C01 → C06 递归、有序 children、独立 occurrence | producer 绑定与撤销恢复 |
| P04 | 蔀日/蔀月 C07、原句预览；忽略原 grammar 的空可选槽 | 月日模型、单位与数值执行 |
| P05 | 原 grammar multiply 两槽、日/月多义 | term 决定进入 compiler |
| P06 | 中法 opaque→C03、日法候选；42/32 reading 不合并 | reading 选择、32 参数输入、跨传统授权 |

六组 probe 都是公开开发样例；積日/積度/入紀日是公开合成替换测试。实际 source unit 38/39/41/40 和两个 legacy preset 验证接线及原生非回归，不能据此声称未见语料的解释准确率已经得到证明。

## 验证命令与证据

使用项目现有 `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B`：该环境已有 Streamlit 和 jsonschema；系统默认 Python 缺这两项依赖。没有安装或修改依赖清单。

```powershell
python -X utf8 -B -m unittest discover -s tests/parser -v
python -X utf8 -B -m unittest discover -s tests/parser_v3 -v
python -X utf8 -B -m unittest discover -s tests/parser_rescue -v
python -X utf8 -B -m unittest discover -s tests/adjudication -v
python -X utf8 -B -m unittest discover -s tests/reconciliation -v
python -X utf8 -B -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 -B -m unittest discover -s tests/workbench -v
python -X utf8 -B -m unittest discover -s tools/parser_inspector -p "test_inspector.py" -v
python -X utf8 -B -m unittest discover -s tools/parser_inspector -p "test_readable.py" -v
python -X utf8 -B -m unittest discover -s tests/domain_kernel -v
python -X utf8 -B -m unittest discover -s tools/parser_inspector -p "test_term_semantics.py" -v
python -X utf8 -B -m domain_kernel.docs --check
```

旧 `test_inspector.py` 会写固定 output/current，故在当前文件的临时副本中原样执行，保留其路径断言。新增接线测试全部使用 TemporaryDirectory。没有写用户的 output/current 或人工 corpus-review。

首轮 TDD：engine 15 项因模块不存在失败后通过；integration 因可选参数不存在失败后 9 项通过；docs 4 项因模块不存在失败后通过。

独立只读复核提出三项 Important，均已先复现失败再修复：固定表达的封闭字段/来源/替代组校验；region 对显式选择或真实语法预览的溯源；截断前二次方区间分配。负例重新计算 ID 后仍必须被语义校验拒绝，避免只测试到 checksum。独立调用 validator 会重算现有 grammar preview；生成器复用本次刚计算的 preview，不重复生成候选。1000 字、单候选上限的压力样例峰值约 2.53 MiB，截断后不再建立完整区间集合。

最终实际测试：

| 测试集合 | 修改前 | 最终 | 退出码 |
|---|---:|---:|---:|
| parser | 61 通过 | 61 通过 | 0 |
| parser_v3 | 94 通过 | 94 通过 | 0 |
| parser_rescue | 78 通过 | 78 通过 | 0 |
| adjudication | 79 通过 | 79 通过 | 0 |
| reconciliation | 5 通过 | 5 通过 | 0 |
| tests 根目录 | 83 通过、2 error | 83 通过、同样 2 error | 1 |
| workbench | 28 通过 | 28 通过 | 0 |
| Inspector | 6 通过 | 6 通过 | 0 |
| readable | 15 通过 | 15 通过 | 0 |
| 新 domain engine/docs | 尚未实现 | 24 通过 | 0 |
| 新 term semantics integration | 尚未实现 | 9 通过 | 0 |
| 文档 `--check` | 尚未实现 | 通过 | 0 |

合计 484 项测试：482 通过，2 项修改前已存在的 error；新增 33 项全部通过。四个真实单元的 bundle 另通过完整离线输出 schema；交接包原资料的 117 项设计检查也通过，单独记录，不混入产品测试计数。

基线已存在两个错误，修改前后均为 Pattern Reference 的冻结输入检查失败：

- `test_pattern_importer.ImporterTests.test_annotation_files_are_actually_opened_only_after_both_compiles`
- `test_pattern_importer.ImporterTests.test_clean_processes_are_byte_identical_and_preserve_compiler_before_import`

原因：`frozen_input_changed: analysis_parser/ontology.py`。本轮不修改 ontology、冻结记录或旧断言，不将失败改成 skip。

本机证据在 ignored `.cache/domain-kernel/`：before/after/final 测试日志与汇总、protected-before/after.json（904 个文件）、parser-hash-before.txt、RED/GREEN 记录、entrypoint-evidence.json（实际 unit 39 的两个入口产物）、limit-check.json、design-validation.json、progress.md。受保护文件核查仅允许两个函数所在文件变化；将两个函数还原后可精确重建各自起始字节 hash，包括 readable 原有混合换行；用户原有 AGENTS 修改等保持原字节。

Parser 指纹保持 `5d1b5401c27f62f08241fb50e1acfc4178719ab3fa107ad18c7e4926e5696f58`。五份原字节交接资料核对一致。没有提交、推送或部署。

## 下一阶段的清理条件

K1 没有修复既有 heading→unit、置X減一→year、profile/contextual rate 适用范围等硬编码。后续 K2 复用现有 adjudication/session/replay/compiler，K3 在统一适用性检查后逐项替换并删除旧消费分支；不可长期保留竞争的执行路径。新增候选不能直接参与 lowering。

现有 grammar 对极长无标点串仍可能递归失败；K1 未修改受保护的 parser，其候选分支失败通过独立 error 状态报告。候选数量上限不等于原生 grammar 的时间上限。历史解释正确性和未见语料泛化仍需独立研究验收。

## K1.1 / K1.5 — 2026-09-19

K1.1 仅将 `accumulation.relation_kind` 从 `has_part` 改为 `associated_with`。所有 constructor 的关系提示现在属于 semantic layer；`child_ids → has_part` 仍只表达有序构词成分。共享 schema、engine 和表达式不变。运行 registry hash 从 `14e77fcaab5f265a67076ed995988629772e38548d3c538071c3b96000ca76ec` 变为 `87f95981b45ad1bdee3a4b1254238d55d19d0912dbcf650daae8028d180a94ac`，候选 ID 重新生成；旧产物不做 ID 迁移。新增关系分层测试先失败再通过，并比较变更前后含义与构词树。

K1.5 只在 `readable.py` 消费已有 `view['term_semantics']`。固定 §39 页面开启原有可选参数，在 R2 后、R3 前新增不编号区块；`compile_view` 和 `runner.run` 的默认参数不变。没有新增 generator、人工操作、session、编译路径或 R4 关联。

- 每个文档／reading 的 occurrence 依 source span 分组；组间按原文顺序、组内按 bundle 顺序保留全部候选，不推选最佳解释。默认显示最长完整组合；内部组合、词素和 opaque 成分折叠但不删除。
- Meaning 保留原始 expression；固定表达只显示其已有 `proposes`，不补造 expression。树和推导规则链完全来自 `child_ids`，顺序与嵌套不变。
- 原文高亮复用现有 `_evidence` 与脚本。cue、rule、provenance 分开解释；只在 registry hash 匹配时读取对应记录，不匹配或读取失败则保留原 ID、明确提示来源信息不可用。
- 分别显示 support、local constraints、authorization，具体未决前提及 suggestion-only 声明。`grammar_candidate` 明确只是 Domain Kernel 预览来源。截断时提示替代解释未穷尽。
- 生成失败、缺失 child、循环引用、来源身份不符等仅使新区块不可用。渲染不调用 generator、bundle validator（会重算 grammar preview）或 compiler。

验收使用实际 `sifen:section:39`：90 个候选、其中 24 个 composition；`入蔀積月` 的三种月义候选全部显示。逐项比较全部候选的 expression、来源与嵌套 child 结构，除 ID 重新生成外含义与推导不变。修改前后 automatic report、reviewed compilation/graph、session、R1–R4 projection 和 diff 完全相同；删除新增区块后，整个 HTML 与修改前完全相同。engine、analysis_parser、adjudication、runner、evaluation 和 canonical source 文件通过前后字节 hash 核验。

本轮完整回归共 493 项：491 通过，2 项仍为上文已记录的 Pattern importer 冻结输入错误；无新增失败。新增 1 项 engine 分层测试、8 项 presentation 测试；旧集成测试改为比较排除新区块后的完整 HTML，原生报告与输出文件比较未放松。文档生成与 `--check` 通过。旧 Inspector 写盘测试仍在独立副本执行。

Streamlit AppTest 验证固定页面实际开启展示、中英文切换、无新增操作按钮及不写 output/current。当前环境没有可连接的浏览器，未完成真实浏览器截图／点击高亮验收；高亮复用原脚本，已验证输出的准确跨度链接。可在本地 Inspector 的 Parser stages 页面人工查看。

本轮证据：ignored `.cache/domain-kernel/k1-5/` 中的 before/after view、HTML、文件 hash 与 `acceptance.json`；完整测试日志和汇总为 `.cache/domain-kernel/k1-5-*.log`、`k1-5-results.json`。实现停在 K1.5，没有进入 K2，没有新增人工裁决入口，也不宣称本次展示提高了识别率或解释准确率。

独立只读代码复核未发现阻断缺陷；提出补强 K1.1 精确关系值断言，已增加 `accumulation.relation_kind == associated_with` 的回归保护并重跑 engine 测试。
