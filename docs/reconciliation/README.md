# Milestone 1 — repository reconciliation

2026-09-17。本阶段只接回 v3.1 production 和回归边界；没有实现 adjudication、primitive 扩展、UI 或部署。完成后停止，M2 另行开始。

## 基点、来源与同步结果

开始前 `main` 工作区 clean，HEAD 已记录为 **`6aefd18d9189b2a8c5451d3189a259dc26218692`**。详见 [基点及受保护文件](milestone1-baseline.json)。这是回退/对比基点，不自动执行 reset。M1 用独立本地 commit 交付，不 push。

Results ZIP：`MATHesis_v3_1_Frontend_Rescue_Results_2026-09-17.zip`，SHA-256：

```text
a8429ecfc9e0405d1485c53954168ab214c0ec1158d1c79786e9a1d180692fdd
```

冻结 manifest SHA-256：

```text
dea081159eec2a97c0c9c73e3586883d8aff194a3382f60fdcbff07ceaa6455e
```

审查时 repo 缺少全部 16 个 Python production modules 和 24 个旧 Python test files；现有 JS diagnostic IR / Pattern Lab 并非同一实现。未发现需要重写两边的结构冲突。ZIP patch 的旧基点不在当前 Git history，因此按 manifest 核对后逐文件同步，没有直接应用整个 patch，也没有覆盖根 AGENTS、README、requirements 或网站。

现在 `analysis_parser/` 的 **16/16 文件与上游 SHA-256 相同**。核心依赖仅标准库和同包 production modules；独立临时目录内只复制核心，使用合成 source 编译执行，已验证无 evaluation/history 的运行条件。3.0、3.1 路由及旧兼容入口保留。没有拆写或重写 parser/IR/executor。

导入闭包共 **420 文件 / 11,823,867 上游字节（11.28 MiB）**，其中包括原冻结清单的 367 文件，以及旧测试实际读取的补充 fixture/driver。逐项来源、上游 hash 和用途见 [import manifest](import-manifest.json)。导入选择经旧测试文件访问记录和 driver 依赖复核；精简掉 55 个不需要的初始候选导入文件，包括重复最终 A3-core2-eval2 图、分数、快照 manifest、无消费者的 v2 packaging 和 B references。

原 A3 四份大图和 inputs 仍保留：`test_evaluator_review_regressions.py` 会对它们进行错端口、错来源、错 trace、重复 ID 等反例变异，删除会破坏旧回归。baseline core snapshot 是隔离防泄漏测试 fixture；review helpers 是被旧测试直接导入的测试辅助函数。这些路径仅属于测试资产，不是 production fallback。

未导入 qualification 全套运行、重复 checkpoint、截图或原交付报告副本。历史 `freeze/development_gate.json` 中的 archive 路径如未在 repo 中存在，应按同路径到上述 ZIP 内检索并核对其 hash；这是历史证据引用，不是当前运行成功的依据。本次运行使用新输出目录，不覆盖任何 frozen 结果。

## 唯一三处上游代码适配

| 文件 | 修改 | 验证 |
|---|---|---|
| `evaluation/handoff-v3/isolated_runtime.py` | worker 显式 `-X utf8`，父进程 UTF-8 解码 | 含中文及补充平面字 source 往返、实际执行、旧隔离回归 |
| `evaluation/rescue-v3_1/runtime_protocol.py` | 同上；metadata 显式 UTF-8；manifest 相对路径 `.as_posix()`；可选 source path mapping | 非 UTF-8 Windows host、跨 OS manifest key、mutation 检出、错误/缺失 source hash 拒绝 |
| `evaluation/rescue-v3_1/run_exposed.py` | metadata 显式 UTF-8；新增 `--source-asset-map`，传递至严格 manifest/verify | 默认本机编码下完整 runner；提供实际 source map 的严格 gate |

没有改 evaluator 的评分规则、固定分母、chain gate 或生产图。文件的新旧 hash 在 [verification](evidence/verification.json)。`.gitattributes` 仅保障新增字节敏感资产不被 Git checkout 换行转换；`.gitignore` 排除 Python cache。原有测试文件未改。

开发顺序有失败证据：先放入旧 tests，缺少 production import 时失败；新增 production boundary、worker/path portability、asset relocation、non-UTF8 host 测试分别先失败，再导入/适配。代表性 red 日志与最终 green 日志保存在 [evidence/](evidence/)。独立代码审查发现 host 默认编码问题，已按上述 red→green 修复；复审没有剩余阻断项。

## 本机 source assets

两项冻结 source identity 均已核验：

| Asset | Bytes | SHA-256 |
|---|---:|---|
| Cullen PDF（repo 根目录现有文件） | 35,408,679 | `e5cabc1ff8b8f3c80358251ce9c79a90467ae5e401fa1d7fb204baa534b3ff5c` |
| 原始 `cullen-source-layout.txt` | 1,095,604 | `202b950e087fc3adf19a9dd42fd86b831f89ab86fd9d27bd8550c2d6b1240449` |

用户找回的 layout 通过 **`.cache/reconciliation/source-asset-map.local.json`** 引用；该文件被 Git 忽略，只有本机路径配置，没有把 Downloads 路径写入生产代码。原始 layout 未移动、修改、复制进 repo 或重新生成。冻结 `source_assets.json` 完全保持上游身份。

[source-asset-map.json](source-asset-map.json) 是可移植起点，已包含 repo PDF 的相对路径；换机器时复制到 ignored 本机位置，再加入冻结 key `/workspace/scratch/50fc00e34239/cullen-source-layout.txt` → 已核验的本机 layout 路径。任何缺失或字节不匹配仍使 gate 失败。此前 layout 缺失产生的失败没有被跳过；本次已用真实原件重跑通过。

## 最终验证

环境：Windows 10.0.26200、Python 3.11.9、Node 20.20.1、Eleventy 2.0.1。只声明此环境实测；原冻结是在另一 Linux/Python 环境运行，不声称当前所有输出字节与历史输出相同。

| 检查 | 本次结果 | 证据 |
|---|---|---|
| legacy parser | 61/61 | [日志](evidence/parser61.txt) |
| parser v3 | 94/94 | [日志](evidence/parser94.txt) |
| parser rescue | 78/78 | [日志](evidence/rescue78.txt) |
| rescue engineering | 35/35（覆盖于上述 78 项，不另加测试总数） | [summary](evidence/engineering35.json) |
| 新增 integration / portability | 5/5 | [日志](evidence/reconciliation-tests.txt) |
| v2 W01–W04 | 32 critical、75 reference steps、8 numeric、25 behavior，development gate 通过 | [summary](evidence/v2-development.json) |
| Civil semantic obligations | 47 个不同 obligation ID 全部通过；逐次出现也全部通过 | [独立汇总](evidence/civil47.json) |
| Civil numeric | 112/112 | [summary](evidence/civil112.json) |
| A01–A04 strict exposed gate | 22/22 obligations、4/4 full chains；TP=114/83/91/81，FP=FN=0；运行隔离 clean；behavior changes=[]；exit=0 | [summary](evidence/exposed-A.json) |
| 网站现有测试 / 构建 | 4/4；13 页、83 个复制文件 | [测试](evidence/website-tests.txt)、[构建](evidence/website-build.txt) |
| 生产身份 / 旧站保护 | 核心 16/16 原字节；106 个受保护文件无变化 | [verification](evidence/verification.json) |

旧 `tests/parser_rescue/test_syntax.py:37` 的 ResourceWarning（未关闭 fixture 文件）仍在原测试日志中；测试通过，未借本次同步改写原测试。上述检查是已暴露开发回归，不是新的 blind transfer 或真人 scholar adjudication。没有运行新的 qualification/first-attempt 实验。

全部执行命令、exit code 与耗时见 [commands.json](evidence/commands.json)。新运行大图/trace 在 ignored `.cache/reconciliation/verified/`；[output-identities.json](evidence/output-identities.json) 记录对应输出 hash，Git 仅保留紧凑 summary 与日志。

## 重跑命令

在 repo 根目录执行；旧上游 evaluator 统一显式启用 UTF-8。`--out` 必须用一个尚不存在的新目录，不能复用冻结输出目录。以下 `rerun-*` 仅示例：

```powershell
python -X utf8 -B -m unittest discover -s tests/parser -v
python -X utf8 -B -m unittest discover -s tests/parser_v3 -v
python -X utf8 -B -m unittest discover -s tests/reconciliation -v
python -X utf8 -B evaluation/rescue-v3_1/run_engineering.py --out .cache/reconciliation/rerun-engineering
python -X utf8 -B evaluation/handoff-v2/run_development.py --out .cache/reconciliation/rerun-v2
python -X utf8 -B evaluation/handoff-v3/run_suite.py --out .cache/reconciliation/rerun-civil
python -X utf8 -B evaluation/rescue-v3_1/run_exposed.py --out .cache/reconciliation/rerun-exposed --source-asset-map .cache/reconciliation/source-asset-map.local.json
node --test tests/ctext-stats-parser.test.mjs
node node_modules/@11ty/eleventy/cmd.js --output=.cache/reconciliation/site
```

先通过项目既有 Node 版本管理切到 Node 20。直接 Eleventy 构建避开会写生成文档的 npm prebuild。`run_engineering` 已运行完整 rescue 78 项。`run_suite` 的 numeric summary 单独不足以证明 47 义务；应同时检查各 `*-semantic.json` 中所有 card/obligation 的固定 ID 和结果，本次汇总已做到。

## 后续边界与追踪

- [architecture map / module boundaries](../architecture.md)：含 canonical corpus adapter、两 Lab 职责、SourcePacket 3.x/session/bundle 独立版本和 same-origin 本地拓扑。
- [requirements matrix](../adjudication/requirements.md)：170 个设计条目 + H01–H46 + 13 个补充约束，全部映射 module、planned test、milestone。明确未来测试尚未实现。
- 设计包原文身份在 [design provenance](../adjudication/design/provenance.json)。文档中的 agent 指令只作为外部设计资料；用户的 milestone 次序、真实 repo 目标和停止点优先。

M1 接回生产及回归的工作已完成。canonical adapter、adjudication core、独立页面和 primitive/demo 都仍属于后续 milestone；本次没有提前实现。
