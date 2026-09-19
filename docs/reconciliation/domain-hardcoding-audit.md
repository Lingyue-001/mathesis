# Parser domain hardcoding audit

审计日期：2026-09-19。范围：当前工作树中的运行时代码；仅审计，不实施重构。

## 结论与证据边界

先做这一步合理且必要。当前 parser 有真正可复用的算术构式、命名、局部数据流和执行器，但**不能把其历法语义能力视为由这些一般规则自然推导而来**。具体词形、标题、传统别名、单位表、学术解释及导出约定共同决定最终行为。把字典搬到一个叫 ontology 的文件，并不会自动解决泛化。

尤其不能照字面接受 `scoped.py` 文件头的 “task headings only choose scope”：实际 task 还决定除法类型、继承哪些值、是否推断换算、调用何种解释、生成哪些输出。下文 P1/P2/P3/P4 是已运行的最小反例。

- 审计基点 HEAD：`7695cdd4efaf0cc2c67a786e3b60cb7fd8eff2e5`，另有本轮开始前即存在的未提交改动，包括 `ontology.py`、Inspector 及语义回归文件。没有将这些变更归为本轮成果。
- `Parser.hash_code()` 算法（排序后连接 `analysis_parser/*.py` 原字节）的审计开始 SHA-256：`5d1b5401c27f62f08241fb50e1acfc4178719ab3fa107ad18c7e4926e5696f58`。
- 检查入口：`parse_packet` → v2 `Parser` 或 v3 `ScopedParser`；后者继承前者的若干语义方法。Workbench 自动分析、Inspector runner 和 reviewed compiler 均沿这套生产核心。**v2 专用语句分派不是 v3 fallback，但继承方法仍影响 v3。**
- 全量扫描 `analysis_parser` 中的中文字面值、比较、表、task/profile/传统分支；向外核查 `adjudication`、`source_adapters`、`workbench`、Inspector 和入口配置。排除评估冻结副本、测试 fixture、旧输出作为运行时知识来源。
- 本报告记录代码中已有的 Cullen/Liu `basis`，未重新核对原著页码或认证这些解释的学术正确性。E 表示“代码声称／记录了校准依据”，不表示本次完成学术审定。
- 未修改 parser、UI、canonical data、人工记录、NOTE/LOG、anchors、claims 或评价标准；未创建 ontology、发现器或新的 CLI。

## 分类口径

| 类 | 判定 | 候选归属（尚未实施） |
|---|---|---|
| A. generic computational grammar | 操作符、槽位、代词、组合结构、数据流、一般算术 | 保留 parser grammar / IR / executor |
| B. reusable calendrical domain knowledge | 可跨具体历法复用的量种、周期、计数／表示概念 | 小型、显式的 domain knowledge；数值率仍需条件与证据 |
| C. tradition-specific knowledge | 当前实现绑定到三统、四分或木星参数体系的角色、别名、率 | tradition/profile 中的有作用域规则 |
| D. exact-source / exact-heading specialization | 标题、整句或指定名字直接开启语义路径、例外、吞并注释 | 来源适配或 suggestion；不能默认充当一般推理 |
| E. scholarly calibrated interpretation | 包含／不包含、历元、转换、边界、补全等校准解释 | 有来源、明确选择、可撤销的 interpretation profile |

这些类别不是互斥本体：例如“三统木星换算”同时是 C 和 E；把它挂到某个 exact phrase 又带 D。以下标主类和必要附类。C 不断言某个汉语词在其他传统中不存在，只描述本实现的知识绑定。

## 规模与地图

| 项目 | 实际数量 | 直接后果 |
|---|---:|---|
| `TERMS` | 67 | 预先允许整词成为 Term，跨过一般分词边界 |
| `TASKS` | 13 个标题 → 7 个 task | 定义域标签、继承、单位、解释、输出 |
| `UNITS` | 31 个有效 key | 缺失值／参数／命名结果的默认单位；源码 `月元餘` 重复一次，同值覆盖 |
| `INPUT_NAMES` / `CURRENT_REQUIRED` | 6 / 4 | 区分根输入／上游缺失／参数，并限制参数回退 |
| `ROLE_ALIASES` | 2 个传统各 1 个映射 | 改变名称解析与链接 |
| `GRAMMAR` | 127 条展开后规则 | 80 条基础表规则 + `EXACT` 47 条短语 |
| `PROFILES` | 13 | 7 个基础 profile + 6 个 `SOURCE_PROFILES`，生效程度不一 |
| `CONTEXTUAL_RATES` / `PLANETARY_RATES` | 5 / 6 | 年→月、月→日及木星相关量的转换 |

同一词在不同阶段可能承担不同作用：`小餘` 的词法登记、余数绑定类型、query 自动进位和输出名称，不能合并成一个笼统“已识别概念”。

## 1. 词项、单位和绑定

以下路径相对仓库根；省略目录的 Python 文件均在 `analysis_parser/`。行号对应审计时工作树；附录保留机器枚举的位置。

| ID / 类 | 位置 | 硬编码及作用 | 影响、边界与候选处理 |
|---|---|---|---|
| L01 A | `inputs.py:7–26` | 数字表 `零〇一二三四五六七八九十百千萬万兩两` + 阿拉伯数字；十／百／千／万进位 | 保留数字语法；不支持所有历史数词，不能把 corpus 分类器认识的 `億/兆/半` 当 parser 已能计算 |
| L02 B/C | `lexical.py:4,9,23` | 67 个 `TERMS`，完整逐词列表见附录 | 增加整词 edge，不直接提供概念或数值；有些词虽无 semantic rule，仍使其可解析 |
| L03 A+B | `lexical.py:6,11–12,27–31` | `BOUNDARY` 含算术字、`日/分`、数词；声明名字排除 `置加盈推求以得除乘為分之` | 陌生词可作为 opaque Term，但含边界字的陌生词可能被拆坏；声明可补整词候选。应分清词法候选与已确认概念，不继续靠标题补丁 |
| L04 B/C | `pipeline.py:13,39,84,232`; `scoped.py:87` | `UNITS` 全表见下表 | 词名可给 missing/parameter/alias 强制赋单位；并非从上下文证明的量种。适宜改为条件化知识事实，不能一律全局化 |
| L05 C | `pipeline.py:14,35–39` | `INPUT_NAMES = 入統歲數、入蔀年、定見復數、積合、統首日、所入蔀名` | 缺失时直接 `external_input`；同时排除 parameter 标记。v3 linker 仍可能报告 missing_import，不能理解为全过程无条件允许输入 |
| L06 A（启发式） | `pipeline.py:35–36` | 任意单字 `len(name)==1` 也当 external_input | 与历法词表无关，却造成“年”和两字新量名的根输入待遇不同；候选降为建议，根输入最终应由 contract 确认 |
| L07 C | `pipeline.py:15,58–65` | `CURRENT_REQUIRED = 積中、中餘、積月、入蔀積月` | 强制找当前产出，不能拿同名参数替代；应把“当前结果”抽成使用角色，不以名字白名单表达 |
| L08 C | `pipeline.py:16,50–52`; `scoped.py:34` | 三统 `閏分→見閏分`；四分 `入蔀積月→積月` | 名称解析、程序链接均生效；三统映射未限定 planet，范围比木星 profile 更宽 |
| L09 C/D | `scoped.py:119–121` | 无条件别名 `元→元法、統→統法、蔀名→所入蔀名、入蔀年數→入蔀年` | 不要求 tradition/profile；未来移入有范围的别名资源，不能当所有术文的同义词 |
| L10 B/C | `pipeline.py:65` | 名字以 `法` 结尾或属于 `章閏、章歲、章月、蔀月、蔀日` → parameter 倾向 | 这是已有的极小词素启发式，不是 morpheme→concept 系统；决定缺失类型和参数绑定。候选降级为角色 suggestion |
| L11 B/C | `pipeline.py:178–194` | 除数标签 `章歲/章法/見月法→month`；`月法→day`（有 planet 则 month）；`日法/蔀月→day`；`見中法→medial`；`章月→intercalary_month` | v2 直接生效；v3 先调用它，再用 contextual rate 等重判。前序 day_denominator 等副作用仍可能保留，不可把 v2 表视为完全失效 |
| L12 B/C | `pipeline.py:203–233` | `小餘→day_fraction、中餘→medial_fraction、月餘→month_fraction` 过滤未领取余数；其他使用 UNITS；命名再写单位 | 名字影响 producer 选择，不只是显示。其余数选择框架属 A，类型知识属 B/C；未知与不兼容须继续区分 |
| L13 A | `pipeline.py:43–48`; `context_compiler.py:48–50`; `program_ir.py:95–96` | `之、其餘、所得、空串` 取 focus；去前缀 `其`；方法内 `餘` 取 remainder；静态接口忽略 `法` 等 | 保留代词/省略语法，但不同层支持集合不完全相同 |

`UNITS` 完整有效表（所有项共享 L04 的影响，不是只列示例）：

| 单位 | 具体词 |
|---|---|
| station | 積次、定次 |
| station_fraction | 次餘 |
| month | 月元餘、積月、合積月、入蔀積月、小積、入紀月、入歲月數、入章月數、章月、元月、紀月、蔀月 |
| medial | 積中、中元餘、入章中數、星見中次、章中、元中 |
| day | 積日、大餘、蔀日 |
| year | 入統歲數、章歲、章法 |
| year_ordinal | 入蔀年 |
| planet_event | 定見復數、積合 |
| intercalary_month | 閏 |

## 2. TASKS 与标题相关行为

`scoped.py:16` 完整映射；主类 D，历法解释部分兼 C/E：

| exact target | task | 下游规则 |
|---|---|---|
| 日月元統、入蔀術曰 | era_entry | T02、T04、E01–E04 |
| 天正、天正術、正月朔、天正朔日 | new_moon | T02、T05、T06、T09 |
| 冬至、二十四氣術曰 | winter | T02、T05、T07–T09 |
| 閏餘所在、閏月所在 | intercalation | T02、T04、T06、E05 |
| 八節 | nodes | T02、T05、T07–T09 |
| 中部二十四氣 | qi | T02、T03、T05、T07–T09 |
| 五行 | declarations | T01；mixed duration 也会直接向 declarations 导出，不依赖此标题 |

| ID / 类 | 位置 | 行为／影响 |
|---|---|---|
| T01 D | `program_ir.py:17–49`; `scoped.py:581–603` | 标题查表赋 domain_label；`推` 创建独立过程，后续 `求` 通常创建 query。未登记标题仍能建 definition，但失去已知 task 的语义待遇 |
| T02 D/C | `scoped.py:129–152` | 所有新 task 默认继承 era_entry；intercalation 额外继承 new_moon 的 `閏餘/積月`；nodes/qi 继承 winter snapshot 与分母。标题选择实际数据依赖 |
| T03 D | `program_ir.py:31–33`; `scoped.py:596,605–608` | `中部二十四氣` 可当后置标题 annotation；遇 numeral predicate 向后搜这一目标与分母声明，切 qi scope。非相同标题无此特例 |
| T04 D/C | `scoped.py:188–190,204–206,257–264` | era_entry 除法直接给 quotient integer、remainder year；允许统长减法；intercalation 特许分母余数补数和无法按率判型时的 integer division |
| T05 D/B | `scoped.py:269–273` | winter/nodes/qi 任一 resolved division 均重写 day/day_fraction 并记分母；new_moon 只在 quotient 已为 day 时记分母。P1 复现标题越权 |
| T06 D/B | `scoped.py:275–300,411–415` | new_moon 命名导出 `積月→months、閏餘→intercalation_remainder、積日→whole_days、小餘→small_remainder、大餘→day_offset`；winter `大餘→winter_whole_residual、小餘→winter_remainder` 并附分母后缀；计日导出 new_moon_day/winter_day；`歲有閏/其歲有閏/其月大` 控制特定布尔输出 |
| T07 D/B | `scoped.py:346–350,401–405,483–489,625–629` | query 名含 `氣` 可切 qi；`其次月/後月朔` 才有 next_moon exports；nodes/qi 特定余数归一化及 first_node/first_qi 输出；方法引用也按 task 选择归一化路径 |
| T08 D/E | `scoped.py:534–547,586–587,604–621,721–725,818–820` | intercalation 乘法可额外输出／rescale lag；winter 无名 numeral 段继承前态；qi 分母重标与专门导出；结束时保存 winter/new_moon base。数值缩放验证属 A，激活与日分假设是 D/E |
| T09 E+D | `scoped.py:726–775` | 从 era_entry/winter 的特定导出建立 epoch、加 `360×elapsed_years`；nodes/qi 绝对时间要求找 receiver `大餘` 和 R11 carry；构造 15 个朔事件、29 个气事件、stride 1/2，进入边界模型。不是任意术文自动发现的时间结构 |
| T10 A | `scoped.py:131` | `self.task==task` 是避免重复切 scope 的工程判断，本身不含具体领域知识；附录仍保留以覆盖用户要求的所有比较 |

**候选决策：** 保留 source-local definition/query 身份；标题到“可能目标概念”可成为 suggestion。类型、继承、method 与 export 应由显式角色及依赖决定。不能只扩大 TASKS 来修复陌生标题。

## 3. 构式、exact phrases 与方法识别

附录逐条列出全部 127 条 grammar（包含全部 47 条 EXACT）。下表解释每类如何影响语义，而不是将所有中文匹配一律视为问题。

| ID / 类 | 位置 | 具体项及影响 |
|---|---|---|
| G01 A | `construction_ir.py:11–58,60–65,67–75`; `pipeline.py:374–460` | `以…乘…、以…減…、置…、盈/滿…得一、除去之、名曰/為、從/上加/并、加…、倍…、亦如之、因為…、分之` 等槽位构式是一般文言计算语法；保留。中文终结符不等于领域硬编码 |
| G02 D+B | `construction_ir.py:59,66,76–81` | `中央各…日`、`置上元/太極上元以來`、`除去上元`、`天/地/人統…以來年數`、`滿…以上亦得一筭之數` 把具体历法表达固定成特定节点。通用槽位与具体解释应分开 |
| G03 A/D | `construction_ir.py:84–94` | EXACT 先生成 grammar，再进入普通选择，不是旁路 whole-program template；但每个短语影响是否识别、是否视为 annotation。逐条分类／目标见附录 |
| G04 C/D | `construction_ir.py:135–136,163–164` | heading marker 仅 `推/求`；branch 仅 `天統/地統/人統`；无 `加` 的数值 pair 只接受 `大餘/小餘`，同时把这两词排除普通 declaration。相同“词+数字”随名字改变 AST |
| G05 A+D | `control_ir.py:17–27` | `加N得一` + 后续 loop_threshold + exact `數所得` 才构建 Repeat，post-test，counter 从 0、每次 +1；gt/ge 来自 profile。结构可复用，寻找结果节点仍绑整句 |
| G06 D/B | `context_compiler.py:114–143` | 仅 `積日/大餘/積度` + 数字 cycle + `統首日/所入蔀名/蔀名/角首` 才抽 cycle/count method；積度赋 du，其他 day；day 优先返回 `大餘`。原点 formal 仍写 day_index，需后续检查角首适配边界 |
| G07 D/B | `context_compiler.py:204–244` | schedule 结构虽由源 AST 抽取，结尾 origin 必须 exact `天正`；free input 固定 month；表行 `{年}歲{數}閏` 与普通／闰年长度形成 year_scan。其它月份原点不会生成同类方法 |
| G08 C/D | `program_ir.py:93,105–106,150–153`; `scoped.py:653–656` | count origin 只有三种名字算依赖；concordance_select 固定定义 `統首日/入統歲數`；method_value_reference 固定依赖統首日，并把任意引用 value alias 为大餘；initial profile 改写大餘/小餘 inputs。这些不是通用 def/use |
| G09 B/C/E | `pipeline.py:241–293`; `scoped.py:301–352` | 通用 count 仍默认 month_ordinal、origin=1；统首日/蔀名成计日方法；civil 月名 modulo 12；大餘+小餘 query 自动推断进位、carry、recall。v3 有 method body 与来源校验，但调用器仍偏日历角色 |
| G10 D | `pipeline.py:301–463`（v2 only） | exact 忽略 `則朔日也、則前年天正十一月朔日也、則星所見中次也、則星所見月也、星合所在之月也`；`入章/至有閏之歲` 驱动 schedule；`閏或進退/以朔制之` 驱动外部约束；`中數/次數` 指定 medial/station ordinal；`大餘` 特别接收更新。完整 literal 位置见附录 |
| G11 D/E | `pipeline.py:385–391`; `scoped.py:551–555` | 通用 `置X減N` 无论 X 类型都标 `ordinal_to_elapsed` 并强制 year；P3 复现。这不能作为一般 load 语法的语义，应等待实际计年角色 |
| G12 D | `construction_ir.py:94`; `scoped.py:463,502,674` | annotation 白名单（含 `筭上/筭外/閏月也/不滿紀法者…`）被当作 accounted，通常不产生运算／判断。已覆盖文本不等于解释了文本；v2 一些 count convention 会更新，v3 annotation 则直接返回 True |
| G13 D/C | `scoped.py:638,675` | `冬至後` 记录 temporal anchor；三统 `中央` mixed_compact 在该 anchor 下加 `中央/water_before_central` 角色备选。此处是解释备选 metadata，不是新算术分支 |

## 4. profiles、rates 与校准解释

### 4.1 全部 13 个 profile

定义都在 `resources.py:3–11,28–36`。下表“生效”根据实际 consumer，而非 profile 名字推断。

| profile / 类 | 内容与代码声明的 basis | consumer 与实际生效程度 |
|---|---|---|
| `ST_elapsed` E/C | elapsed；输入 epoch_elapsed_years；C2017 §173 / L2003 pp.23–24 | `lower_entry:420–426` 取首个有 input 的选中 profile；但 `外所求年` 的 435–436 直接使用全局 ST_elapsed basis，不要求选中此 profile |
| `SF_Liu_inclusive` E/C | inclusive；E=Y−1、U=localE+1；C2017/L2003 与项目 I03 | 初始输入减一由选中 profile 驱动；obscuration_index 的 local+1 和 basis（475–477）直接硬编码，不在此处再检查 profile |
| `ST_intercalation_Cullen_Liu_GT` E/C | stop=gt；C2017 p.93 / L2003 eq2.9 | `scoped.py:57–58` 只有恰一 stop profile 才给 control operator；repeat 真正使用 > |
| `ST_intercalation_GE_contrast` E | stop=ge；诊断对照 | 同路径真正使用 ≥；应保留为显式模型比较，不变成历史真值 |
| `SF_completed_four` E/C | threshold=ge；C2017 §50 / L2003 p.70 | 没有读取该 threshold 字段的 semantic consumer；conditional_count 直接写 lower_inclusive=True，executor threshold 直接 ≥。登记和 hash 有效，切换语义开关未实现 |
| `instant_lunation` E/B | 瞬时月界；C2017 pp.93–95 | `boundary_view` 选唯一 profile；`operations.py:104–117` / `control_ir.py:34–41` 使用精确有理数半开区间 |
| `civil_whole_day` E/B | 整日月界；C2017 pp.94–96 / L2003 p.70 | 相同路径将朔时刻向下取整；不是 parser 从字面自行推断 |
| `C2017_ST_Jupiter_parameter_roles_v1` E/C | 见下文四个 aliases、interval roles；§§22,25–28,186,190,197 | aliases 初始化检查 tradition+planet；context interval metadata、bridge、update、planetary rates 多处只检查 profile/planet，未统一检查 tradition |
| `C2017_ST_local_year_count_v1` E/C | `外所求年:0、盡所求年:1`；§§173,186,202 | `盡所求年` 要求选中后硬编码 +1；`local_counts` 字典本身没有被读取消费，`外所求年` 走独立 ST_elapsed 路径 |
| `C2017_ST_Jupiter_station_rate_v1` E/C | 145/144 year→station；星紀=1/12、丙子=13/60；§202 等 | `divide:230–239` 检查数值操作数；`count_origin:704–708` 查 origin；别名歲數→歲星歲數。planet 检查存在，分支未统一检查 tradition |
| `C2017_ST_Section_four_Rules_conditional_v1` E/C | Section=four Rules；queries independent；§§265–266 | 无读取 interpretation 的 lowering consumer。选中会进入 provenance/resource identity，但未发现改变计算路径 |
| `C2017_ST_origin_month_day_frame_v1` E/C | Origin；origin_day=1；元月；记录 §195 Concordance Head 冲突读法 | `__init__:40–44` 优先选带 origin frame 的 producer；`divide:208–211` 标历元；`recall:323–329` 建甲子 origin。改变链接及时间框架，不能当普通词典 |
| `C2017_ST_concordance_midnight_frame_v1` E/C | query_initial_rule_ordinal=0；Concordance Head midnight | `program_ir.py:150–153` + `scoped.py:832–845,869–876` 建共享 query base 与自动进位；`operations.py:48–51` 强制 ordinal=0。`initial_value` 字段本身不是通用消费接口 |

跨 profile 边界：选择集合不存在一个统一的 tradition/planet 适用性校验；`validate_profile()`（`adjudication/registry.py:68`）只检查 ID 是否存在。不能因为资源有 `tradition` 字段就宣称所有 consumer 自动遵守。多个 input profile 同时选中时，lower_entry 取首个，而 stop/boundary 采用“唯一一个”策略，冲突处理也不一致。

### 4.2 rates 全表

`CONTEXTUAL_RATES`：`resources.py:18–24`；消费者 `scoped.py:213–251`。主类 E，兼 C/B。

| 传统 / 声明 task | numerator / denominator | 转换 | basis |
|---|---|---|---|
| 三统、四分 / new_moon | 章月 / 章歲或章法 | year→month | C2017 §§174,46；L2003 eq2.6,3.7 |
| 三统 / new_moon | 月法 / 日法 | month→day | §175；eq2.7 |
| 四分 / new_moon | 蔀日 / 蔀月 | month→day | §47；eq3.8 |
| 三统 / winter | 策餘 / 統法 | year→day，annual_residual | §177；eq2.10 |
| 四分 / winter | 日餘 / 中法 | year→day，annual_residual | §49；eq3.12 |

实际触发检查 factor/divisor 为参数、精确标签、operand unit、tradition，**不检查表中 tasks，也不要求 selected_profile**。P2 已证实在陌生 task 下仍生效。这可能是希望跨术复用同一率，也可能是漏 gate；当前声明与实现不一致，应先决定适用条件，不能机械补 gate 或机械迁移字段。

`PLANETARY_RATES`：`resources.py:37–46`；消费者 `scoped.py:163–173,225–229`。六项均写三统、Jupiter、`C2017_ST_Jupiter_parameter_roles_v1`，basis 为 §§186,188,190,193,195：

| numerator / denominator | 转换 |
|---|---|
| 見中法 / 歲星歲數 | year→planet_event |
| 見中分 / 見中法 | planet_event→medial |
| 見閏分 / 見月法 | planet_event→month |
| 章歲 / 見月法 | medial_fraction→month |
| 月法 / 見月日法 | month_fraction→day |
| 見月法 / 見月日法 | day_fraction→day |

这里先在 multiply 上保存 rate_denominator/target/evidence，再在 divide 上消费；不是仅靠除数名赋单位。实际 gate 检查 profile+planet+参数标签+单位+唯一分母，但此分支没有读取 rate.traditions。

Jupiter role profile 四个 aliases：`見復數→見中法、歲數→歲星歲數、閏分→見閏分、後月餘→月餘`；`後月餘` 强制 parameter use；`積月→month、月餘→month_fraction` 是 interval parameters；月餘 scale 取唯一 `見月法`。这些会影响 namespace/linker/类型/加法操作数来源。

### 4.3 资源之外仍嵌入代码的解释

| ID / 类 | 位置 | 内容、触发与后果 |
|---|---|---|
| E01 E/C | `pipeline.py:122–175`; `scoped.py:156–166` | R15 medial↔month bridge：三统+存在 planet、章歲=19、章月=235、12-medial cycle、見月法；profile 路径另外接受 Jupiter+見中法 division 与两项参数。支持 month+medial、章歲×medial_fraction；有 evidence，但并非通用量纲算术 |
| E02 B/E | `resources.py:12–13`; `scoped.py:448–458,726–735`; `audit.py:58–64` | SEXAGENARY 干支组合生成 60 标签，一基循环；WINTER_LIFT=360 用于补回全年日数。前者可作 B 资源，后者是 E 模型，不是泛用历法常数；audit/executor 还要求此精确模型 |
| E03 C/E | `scoped.py:439–481` | 天/地/人統选择、固定統法、輸出入統歲數/統首日；天紀/地紀/人紀列序；查表必须有 `蔀首日` 列；row+1、local+1；年名用 60 cycle。表值来自 context，列语义与归一化预置于代码 |
| E04 E/C | `scoped.py:104–108` | context_supplied_values 作为 scholarly parameter 输入；支持跨度只筛 `章月/章法` | 数值由 packet 提供，但其证据连接方式仍是标签专用；不能当原文声明 |
| E05 E/C/D | `scoped.py:490–528` | intercalation Repeat、条件计数；origin 含 `十一月` 或 exact `起冬至` 激活 nominal；slot=count+1、闰月复前月名、民用月原点=11、cycle=12 | 算术来自实现；含学术 basis 的解释应保留可选／可撤销，别推广为未知 procedure 的默认结论 |
| E06 E/B | `operations.py:27–34,48–60,87–119`; `control_ir.py:34–41` | 一基循环计数、零 ordinal 初始夜半、day epoch、calendar table lookup、bounded moon/qi membership | executor 没有中文 exact 判断，但存在历法专门 operation；应区分通用执行机制和此类 operation contract |
| E07 B/C/D | `audit.py:40–45` | source quote 以 `不盈/不滿/不盡/其餘/餘` 开头即查 remainder producer；只有 receiver `積中/積月` 查 full accumulation corruption | 诊断也影响 reviewed coverage/closure；建议未来按 AST role 扩展，不能当所有类似量都受同等保护 |
| E08 B | `quantity_semantics.py:11–24,65–71`; `adjudication/registry.py:27–34` | 有限 unit→quantity_kind；day/year→du 需要 model rate；review 允许有限 units | 是真实有限 domain type system；不是可组合历史词义体系，也不是无限开放 ontology |

## 5. 外围边界与避免误判

| 位置 | 分类／作用 | 本轮判断 |
|---|---|---|
| `source_adapters/corpus_index.py:16–22,87–90,123–135,171` | A/B/C/D；`推/步術/求/一術`、操作 cue、尾缀与 `木火土金水` + PLANET_LABELS 分块／分类 | 会影响可选 source unit 的边界，是 parser 前置条件；并不自动给执行器提供参数值。PLANET_LABELS 完整为 周率、日率、合積月、月餘、月法、大餘、小餘、虛分、入月日、日餘、日度法、積度、度餘；`晨伏/夕伏` 另触发参考数据分类 |
| `source_adapters/corpus.py:120–170`; `config/workbench-procedures.json` | C/D；入口显式选 primary/context、tradition、input contract | scope 与选材预先提供，不能算 parser 从文本发现。属于任务配置，不能混成领域语义推理 |
| `adjudication/compiler.py`; `adjudication/registry.py` | A/E；人工候选、绑定、scope、profile、单位约束进入正常编译 | “人工确认的解释”不是规则自动能力；本轮不更改 decisions 或人工字段 |
| `analysis_parser/ontology.py`; `workbench/presentation.py`; Inspector readable | 展示层 registry 与语言说明 | 名叫 ontology，但这里描述 code 的人类可读语言，不授权／执行语义。不能把它算成已有 domain ontology，也不应为这次审计修改用户正在做的 UI 改动 |
| `evaluation/**`、`handoff_v3/reference/**`、冻结 snapshot | 评估/例子 | 不计入生产 parser 的已知知识；已有测试通过是对暴露材料的回归，不是盲泛化成绩 |

## 6. 已运行的最小对照

统一使用直接 `parse_packet`、schema 3.0；不经过 Inspector 写文件接口，不改变 corpus/session。只描述结构与类型，未将这些合成例子作为历史算法正确性证据。

| Probe | 输入／控制变量 | 实测结果 | 归因 |
|---|---|---|---|
| P1 | `推雜算。置六。滿三得一。為甲量。`；仅依次换标题为天正、冬至、日月元統 | 雜算/天正 divmod=`integer,integer`；冬至=`day,day_fraction`；日月元統=`integer,year` | T04/T05：标题直接改类型，无需传统或 profile |
| P2 | 三统 scope，context `章月二百三十五。章歲十九。`，primary `推雜算。以章月乘入統歲數。滿章歲得一。為積月。` | task 是 source-local def-ID，仍 `rate_conversion/resolved`，rate 声明 tasks=[new_moon]，无 execution_blocked | CONTEXTUAL_RATES consumer 不检查 tasks |
| P3 | `置甲量。` 对比 `置甲量減一。` | 前者 load opaque；后者 subtract 输出 year，quantity_kind 仍 unknown | G11；不是从甲量的意义推导出年 |
| P4 | `以甲量乘乙量。` 对比 `以日率乘月率。` | 前者 multiply selected（值仍 opaque/product）；后者 unclassified/unresolved | 日是 BOUNDARY，日率未在 TERMS；识别构式与知道单位是两件事 |
| P5 | `筭上。` | annotation selected，0 values，0 unparsed spans | G12：覆盖不等于已解释计数约定 |
| P6 | `其月大。` | judgment unresolved | 只有短语命中还不够，需先有 pending threshold；这里保留了有用的上下文约束 |
| P7 | 从 SF_CIVIL_CORE 选中配置移除 SF_completed_four；从 ST_CIVIL_CORE 的选中配置移除 Section_four_Rules profile | 两组各自的 events、value_instances、bindings、task_exports 全部相等 | 与“没有 semantic consumer”的静态发现一致；仍会改变 selected_profiles 等 provenance，不意味着 session 身份不变 |
| P8 | Han_Si_fen_li + Jupiter scope，却选三统 Jupiter_parameter_roles profile；context `見中法二十三。歲星歲數十二。`，primary `推雜算。以見中法乘入統歲數。滿歲星歲數得一。` | multiply 的 rate_numerator 与 divmod 的 source_rate_division 都 resolved | profile/rate 的 tradition 元数据没有统一成为执行 gate；不是只读显示问题 |

P1 另暴露元数据一致性：integer/day/day_fraction 的 divmod 产物 `quantity_kind` 仍可为 unknown，因为部分路径直接写 unit 而未重新 finalize。此问题会混淆“类型已解决”的显示与判定，应单独列为后续修复候选，本轮未修。

复现核心（仓库根运行 Python；Windows 使用 UTF-8 模式，避免 shell 管道把中文替换为问号）：

```python
from analysis_parser.pipeline import parse_packet

def probe(text, context='', scope=None):
    packet = {'schema_version': '3.0',
              'primary_documents': [{'doc_id': 'probe', 'text': text}],
              'context_documents': [{'doc_id': 'ctx', 'text': context}] if context else [],
              'provided_scope': scope or {}}
    report = parse_packet(packet)
    return {
        'syntax': [(c['kind'], c['text'], c['status'])
                   for c in report['construction_candidates']],
        'values': [(v['unit'], v['quantity_kind'], v['labels'])
                   for v in report['value_instances']],
        'division': [(e['scope'].get('task'), e['attributes'].get('quantity_transition'))
                     for e in report['events'] if e['kind'] == 'divmod'],
    }

for heading in ('雜算', '天正', '冬至', '日月元統'):
    print(heading, probe(f'推{heading}。置六。滿三得一。為甲量。'))
print(probe('推雜算。以章月乘入統歲數。滿章歲得一。為積月。',
            '章月二百三十五。章歲十九。', {'tradition': 'San_tong_li'}))
for text in ('置甲量。', '置甲量減一。', '以甲量乘乙量。', '以日率乘月率。', '筭上。', '其月大。'):
    print(text, probe(text))
```

P7 使用 `handoff_v3/runtime_inputs/SF_CIVIL_CORE.json` 的 selected_profiles=`[SF_Liu_inclusive, SF_completed_four]`，以及 ST 对应文件的 `[ST_elapsed, ST_intercalation_Cullen_Liu_GT, C2017_ST_Section_four_Rules_conditional_v1]`；分别编译移除前后并直接比较上述四个字段。P8 使用表中完整合成输入和 selected_profiles=`[C2017_ST_Jupiter_parameter_roles_v1]`，读取两个事件的 quantity_transition。

## 7. 下一步候选边界，不是本轮实施计划

| 优先级 | 候选决策 | 判断依据 |
|---|---|---|
| P0 | 先明确 task 能否授权单位／继承／解释；去掉通用 load 的无条件 year 推断 | P1/P3；否则迁词典会保留同样的越权 |
| P0 | rates/profile 的声明条件与实际 gate 对齐；区分 active、metadata-only、部分消费 | P2；SF_completed_four、Section profile、local_counts 的消费缺口 |
| P1 | 把“参数／当前产出／输入／余数／原点”等角色从特定 label 解耦 | INPUT_NAMES、CURRENT_REQUIRED、方法签名和 UNITS 都依赖名字 |
| P1 | B 只收少量明确概念及条件化关系；C 收传统角色／别名／率；E 保留证据与选择 | 不能把有争议读法升级为 universal concept，也不能丢掉既有校准出处 |
| P1 | D 中 heading、annotation、来源特例先变为受约束的建议；无 consumer 的 profile 字段先核实用途再删／实现 | 不直接删除仍承载有效校准或可回放身份的资源 |
| P2 | 然后试一个窄的 morpheme→concept→compositional suggestion 闭环 | 可从“積／餘／法／日／月／年”的局部角色候选入手，但组合只产建议，不能看到“餘”就确认同一量种或分母 |

泛化验收应增加同构改名、标题移除／替换、未知传统、profile 消融、不同词形与相同字形不同角色的对照。评分分开记录：构式识别、依赖、类型／表示、可执行性、解释依据。现有 corpus regression 留作防退化，不应单独用于证明新材料泛化。

## 8. 验证记录

已运行：静态 `rg` + AST 枚举、P1–P8 内存对照、三组既有测试。未新增回归测试或修改旧测试。

```powershell
$env:PYTHONUTF8='1'
python -B -m unittest discover -s tests/parser -q
python -B -m unittest discover -s tests/parser_v3 -q
python -B -m unittest discover -s tests/parser_rescue -q
```

结果：61/61、94/94、78/78。rescue 有既有未关闭 fixture 文件的 ResourceWarning，无失败。最初未启用 PYTHONUTF8 时，旧测试无 encoding 的 read_text 被 Windows GBK 解码阻断；修正运行环境后重跑通过，没有改代码掩盖错误。最初 shell 中文探针被管道编码替换为问号，该轮结果已作废，上表只采用显式 UTF-8 管道重跑结果。

这些回归证明现有样本稳定，不反驳 P1–P4 的泛化问题。当前仍未测量陌生 corpus 的准确率，也未为每条 C/E 规则重审学术依据。

审计结束时重新计算 parser SHA-256，与开头完全相同；`git status` 对比本轮开始，仅多出本报告。`git diff --check` 通过（现有工作树文件有 Git 换行提示）。

<!-- GENERATED-INVENTORY -->

## 附录 A：67 个 TERMS 逐词位置与作用

所有词均定义于 `analysis_parser/lexical.py:4`，由 :23–24 加入整词候选。下列附加行为仅描述表命中；其它使用位置见正文及附录 C。B/C 分类是当前知识绑定，不是词义排他声明。

| 词 | 类 | 除词法外的表驱动行为 |
|---|---|---|
| 入統歲數 | C | L04 unit=year；L05 缺失时外部输入 |
| 入蔀積月 | C | L04 unit=month；L07 必须当前产出 |
| 入蔀年 | C | L04 unit=year_ordinal；L05 缺失时外部输入 |
| 統首日 | C | L05 缺失时外部输入 |
| 所入蔀名 | C | L05 缺失时外部输入 |
| 章閏數 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 章歲 | C | L04 unit=year |
| 章法 | C | L04 unit=year |
| 章月 | C | L04 unit=month |
| 章中 | C | L04 unit=medial |
| 統法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 元法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 紀法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 蔀法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 日法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 月法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 蔀日 | C | L04 unit=day |
| 蔀月 | C | L04 unit=month |
| 中法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 日餘 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 策餘 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 大餘 | B | L04 unit=day |
| 小餘 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 閏餘 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 積月 | B | L04 unit=month；L07 必须当前产出 |
| 積日 | B | L04 unit=day |
| 太極上元 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 上元 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 冬至 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 中央 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 蔀名 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 天統 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 地統 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 人統 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見復數 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 歲數 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 歲星歲數 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 定見復數 | C | L04 unit=planet_event；L05 缺失时外部输入 |
| 見復餘 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見中分 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見中法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 積中 | C | L04 unit=medial；L07 必须当前产出 |
| 中餘 | C | L07 必须当前产出 |
| 元中 | C | L04 unit=medial |
| 中元餘 | C | L04 unit=medial |
| 入章中數 | C | L04 unit=medial |
| 星見中次 | C | L04 unit=medial |
| 閏分 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見閏分 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見月法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見月日法 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 月餘 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 後月餘 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 月元餘 | C | L04 unit=month |
| 入章月數 | C | L04 unit=month |
| 入月日數 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 積次 | C | L04 unit=station |
| 次餘 | C | L04 unit=station_fraction |
| 定次 | C | L04 unit=station |
| 統首 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 太歲日 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 星所見月 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 後見月 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見日 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 所在次 | B | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 星見月朔日 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |
| 見數 | C | L02 只由 TERMS 添加整词 edge；不因此获得单位或数值 |

## 附录 B：全部构式与 EXACT 的展开清单

每项由 `construction_ir.parse_syntax` 选择 AST，再按 kind 进入 lowerer；“语法可匹配”不保证 selected 或可执行。固定短语来自 EXACT 的行已标“exact”。G01 等指正文规则组，语义特例另列 consumer。

| 源行 | 类／规则组 | kind | 完整 pattern / exact phrase |
|---|---|---|---|
| construction_ir.py:12 | A / G01 | `task_marker` | `{marker:k}{target:h}` |
| construction_ir.py:13 | A / G01 | `query_marker` | `欲知{target:h}` |
| construction_ir.py:14 | A / G01 | `update_count` | `加{increment:n}得一` |
| construction_ir.py:15 | A / G01 | `numeral_predicate` | `{factor:n}其{value:t}` |
| construction_ir.py:16 | A / G01 | `denominator_declaration` | `皆以{denominator:a}為法` |
| construction_ir.py:17 | A / G01 | `denominator_declaration` | `以{denominator:a}為法` |
| construction_ir.py:18 | A / G01 | `multiply` | `以{left:a}乘{right:a}` |
| construction_ir.py:19 | A / G01 | `multiply` | `又以{left:a}乘{right:a}` |
| construction_ir.py:20 | A / G01 | `multiply` | `每以{left:a}乘{right:a}` |
| construction_ir.py:21 | A / G01 | `multiply` | `餘以{left:a}乘{right:a}` |
| construction_ir.py:22 | A / G01 | `subtract` | `以{right:a}減{left:a}` |
| construction_ir.py:23 | A / G01 | `update` | `加{amount:a}於{receiver:t}` |
| construction_ir.py:24 | A / G01 | `pair_increment` | `加{receiver:t}{amount:n}` |
| construction_ir.py:25 | A / G01 | `pair_increment` | `{receiver:t}{amount:n}` |
| construction_ir.py:26 | A（consumer 有 D/E）/ G11 | `load` | `置{value:a}減{decrement:n}` |
| construction_ir.py:27 | A / G01 | `load` | `置{value:a}` |
| construction_ir.py:28 | A / G01 | `divide` | `{value:o}盈{divisor:a}得一` |
| construction_ir.py:29 | A / G01 | `divide` | `{value:o}滿{divisor:a}得一` |
| construction_ir.py:30 | A / G01 | `cycle_divide` | `{value:a}以{divisor:a}除去之` |
| construction_ir.py:31 | A / G01 | `cycle_divide` | `{value:a}以{divisor:a}去之` |
| construction_ir.py:32 | A / G01 | `cycle_divide` | `{value:a}盈{divisor:a}除去之` |
| construction_ir.py:33 | A / G01 | `cycle_divide` | `{value:a}滿{divisor:a}除去之` |
| construction_ir.py:34 | A / G01 | `divide_by` | `以{divisor:a}除{value:a}` |
| construction_ir.py:35 | A / G01 | `pending_cycle` | `{value:a}盈{divisor:a}` |
| construction_ir.py:36 | A / G01 | `pending_cycle` | `{value:a}滿{divisor:a}` |
| construction_ir.py:37 | A / G01 | `loop_threshold` | `盈{threshold:a}` |
| construction_ir.py:38 | A / G01 | `remainder_name` | `不盈者名曰{label:t}` |
| construction_ir.py:39 | A / G01 | `remainder_name` | `不盈者為{label:t}` |
| construction_ir.py:40 | A / G01 | `remainder_name` | `不滿為{label:t}` |
| construction_ir.py:41 | A / G01 | `remainder_name` | `不盡為{label:t}` |
| construction_ir.py:42 | A / G01 | `remainder_name` | `其餘為{label:t}` |
| construction_ir.py:43 | A / G01 | `remainder_name` | `餘為{label:t}` |
| construction_ir.py:44 | A / G01 | `remainder_name` | `餘則{label:t}` |
| construction_ir.py:45 | A / G01 | `name` | `名曰{label:t}` |
| construction_ir.py:45 | A / G01 | `name` | `名為{label:t}` |
| construction_ir.py:45 | A / G01 | `name` | `為{label:t}` |
| construction_ir.py:46 | A / G01 | `receiver_add` | `從{receiver:a}` |
| construction_ir.py:46 | A / G01 | `receiver_add` | `上加{receiver:a}` |
| construction_ir.py:46 | A / G01 | `receiver_add` | `并{receiver:a}` |
| construction_ir.py:47 | A+B（consumer 有 D）/ G06–G09 | `count_origin` | `從{origin:h}起` |
| construction_ir.py:47 | A+B（consumer 有 D）/ G06–G09 | `count_origin` | `數從{origin:h}起` |
| construction_ir.py:48 | A+B（consumer 有 D）/ G06–G09 | `count_origin` | `中數從{origin:h}起` |
| construction_ir.py:48 | A+B（consumer 有 D）/ G06–G09 | `count_origin` | `次數從{origin:h}起` |
| construction_ir.py:49 | A+B（consumer 有 D）/ G06–G09 | `count_command` | `以{origin:a}命之` |
| construction_ir.py:49 | A+B（consumer 有 D）/ G06–G09 | `count_command` | `其餘以{origin:a}命之` |
| construction_ir.py:50 | A / G01 | `threshold` | `{value:o}{lower:n}以上` |
| construction_ir.py:50 | A / G01 | `threshold` | `{value:o}滿{lower:n}以上` |
| construction_ir.py:51 | A / G01 | `add` | `加{amount:a}` |
| construction_ir.py:51 | A / G01 | `recur_increment` | `又加{receiver:t}{amount:n}` |
| construction_ir.py:52 | A / G01 | `double_interval` | `倍{target:h}` |
| construction_ir.py:53 | B+A / G01、G07 | `mixed_compact` | `{label:t}{whole:n}日{numerator:n}分` |
| construction_ir.py:54 | A / G01 | `declaration` | `{label:t}{value:n}` |
| construction_ir.py:55 | A / G01 | `declaration` | `{label:t}，{value:n}` |
| construction_ir.py:56 | A / G01 | `parameter_alias` | `因為{label:t}` |
| construction_ir.py:57 | B+A / G01、G07 | `mixed_duration` | `{whole:n}日，{denominator:a}分之{numerator:n}` |
| construction_ir.py:58 | B+A / G01、G07 | `mixed_duration` | `其{subject:h}各{whole:n}日，{denominator:a}分之{numerator:n}` |
| construction_ir.py:59 | D+B / G02 | `mixed_duration` | `中央各{whole:n}日，{denominator:a}分之{numerator:n}` |
| construction_ir.py:60 | A / G01 | `name` | `則{label:t}也` |
| construction_ir.py:61 | A / G01 | `remainder_name` | `餘名曰{label:t}` |
| construction_ir.py:62 | A / G01 | `remainder_name` | `餘則{label:t}也` |
| construction_ir.py:63 | A / G01 | `multiply_focus` | `乘{factor:a}` |
| construction_ir.py:64 | A / G01 | `reuse_operation` | `{receiver:t}亦如之` |
| construction_ir.py:65 | A / G01 | `multiply` | `不盈者以{left:a}乘{right:a}` |
| construction_ir.py:66 | C+D / G02、E03 | `epoch_load` | `置上元以來` |
| construction_ir.py:67 | A / G01 | `pair_increment` | `{receiver:t}加{amount:n}` |
| construction_ir.py:68 | A / G01 | `recur_increment` | `當加{receiver:t}{amount:n}` |
| construction_ir.py:69 | A / G01 | `receiver_add` | `并之{receiver:t}` |
| construction_ir.py:70 | A+D / G08 | `method_value_reference` | `數除{value:t}如法` |
| construction_ir.py:71 | A+B（consumer 有 D）/ G06–G09 | `count_remainder` | `不盈者數起於{origin:h}` |
| construction_ir.py:72 | A / G01 | `scalar_value` | `為{value:n}` |
| construction_ir.py:73 | A / G01 | `scalar_name` | `是為{label:t}` |
| construction_ir.py:74 | B+A / G01、G07 | `schedule_row` | `{year:n}歲{count:n}閏` |
| construction_ir.py:75 | B+A / G01、G07 | `scan_length` | `除{months:n}` |
| construction_ir.py:76 | C+D / G02、E03 | `epoch_load` | `置太極上元以來` |
| construction_ir.py:76 | C+D / G02、E03 | `epoch_divide` | `以{divisor:a}除去上元` |
| construction_ir.py:77 | C+D / G02、E03 | `entry_cycle` | `盈{divisor:a}除之` |
| construction_ir.py:78 | C+D / G02、E03 | `entry_remainder_divide` | `其餘以{divisor:a}除之` |
| construction_ir.py:79 | C+D / G02、E03 | `concordance_case` | `則{branch:b}{head:t}以來年數也` |
| construction_ir.py:80 | C+D / G02、E03 | `concordance_case` | `餘則{branch:b}{head:t}以來年數也` |
| construction_ir.py:81 | E+D / E05 | `conditional_count` | `滿{lower:n}以上亦得一筭之數` |
| construction_ir.py:84 | A+B（consumer 有 D）/ G06–G09 | `method_reference` | **exact** `除數如法` |
| construction_ir.py:84 | A+B（consumer 有 D）/ G06–G09 | `method_reference` | **exact** `數除如法` |
| construction_ir.py:84 | A+B（consumer 有 D）/ G06–G09 | `method_reference` | **exact** `除命之如前` |
| construction_ir.py:84 | A+B（consumer 有 D）/ G06–G09 | `method_reference` | **exact** `命之如前` |
| construction_ir.py:85 | A / G01 | `use_denominator` | **exact** `如法得一` |
| construction_ir.py:85 | A / G01 | `complete_cycle` | **exact** `除之` |
| construction_ir.py:85 | A / G01 | `complete_cycle` | **exact** `除去之` |
| construction_ir.py:87 | B+D / T06、G13 | `judgment` | **exact** `歲有閏` |
| construction_ir.py:87 | B+D / T06、G13 | `judgment` | **exact** `其歲有閏` |
| construction_ir.py:87 | B+D / T06、G13 | `judgment` | **exact** `其月大` |
| construction_ir.py:88 | E+C+D / profiles | `epoch_inclusive` | **exact** `盡所求年` |
| construction_ir.py:88 | E+C+D / profiles | `epoch_elapsed` | **exact** `外所求年` |
| construction_ir.py:88 | C+D / G02、E03 | `concordance_remainder` | **exact** `餘不盈統者` |
| construction_ir.py:89 | C+D / G02、E03 | `concordance_pending` | **exact** `盈統` |
| construction_ir.py:89 | C+D / G02、E03 | `concordance_pending` | **exact** `又盈統` |
| construction_ir.py:89 | C+D / G02、E03 | `concordance_select` | **exact** `各以其統首日為紀` |
| construction_ir.py:90 | C+D / G02、E03 | `era_index` | **exact** `所得數從天紀` |
| construction_ir.py:90 | C+D / G02、E03 | `obscuration_index` | **exact** `所得數從甲子蔀起` |
| construction_ir.py:91 | C+D / G02、E03 | `year_name` | **exact** `即所求年太歲所在` |
| construction_ir.py:91 | E+D / E05 | `nominal` | **exact** `起冬至` |
| construction_ir.py:92 | A+D / G05 | `loop_result` | **exact** `數所得` |
| construction_ir.py:92 | B+D / T06、G13 | `temporal_anchor` | **exact** `冬至後` |
| construction_ir.py:93 | E+D / E05 | `boundary` | **exact** `中氣在朔若二日` |
| construction_ir.py:93 | E+D / E05 | `boundary` | **exact** `或進退` |
| construction_ir.py:93 | E+D / E05 | `boundary` | **exact** `以中氣定之` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `算盡之外` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `餘不盈者` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `至有閏之歲` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `入章` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `月大` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `算外` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則中至終閏盈` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則前月閏也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `閏月也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `筭盡之外` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則所求冬至日也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則前年冬至之日也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `小寒日也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則朔日也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `則前年天正十一月朔日也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `筭外則所入紀也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `不滿紀法者` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `入紀年數也` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `筭外` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `筭上` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `所入蔀也不滿蔀法者` |
| construction_ir.py:94 | D / G12 | `annotation` | **exact** `所入蔀也不滿蔀法者入蔀年數也各以所入蔀歲名命之` |

## 附录 C：其它中文字面值所在代码行（AST 扫描）

覆盖核心所有非 docstring 的中文字符串常量；已完整列出的 TERMS、UNITS/INPUT/CURRENT/ROLE、TASKS、GRAMMAR/EXACT 和 resources 表不在此重复。保留 regex、比较、membership、get/alias/export 参数及诊断触发字面值，防止只搜 `==` 漏项。类与影响按所属函数列出；一行可含多个用法，应与正文的具体 gate 合读。展示语言 registry ontology.py 已明确排除。

| 位置／函数 | 分类与作用（正文索引） | 代码原文 |
|---|---|---|
| audit.py:40 `audit` | A+B+C+D / E07；诊断触发及结构审核 | `if e['kind']=='alias' and e.get('rule_id')!='V3_DIFFERENCE' and any(s['quote'].startswith(('不盈','不滿','不盡','其餘','餘')) for s in e['source_spans'][:1]):` |
| audit.py:43 `audit` | A+B+C+D / E07；诊断触发及结构审核 | `if e['kind']=='add' and e.get('attributes',{}).get('receiver_label') in ('積中','積月'):` |
| construction_ir.py:135 `walk` | A+D / G04；槽位限制、语法去歧义及组合 | `elif typ=='k':good=t['text'] in ('推','求')` |
| construction_ir.py:136 `walk` | A+D / G04；槽位限制、语法去歧义及组合 | `elif typ=='b':good=t['text'] in ('天統','地統','人統')` |
| construction_ir.py:141 `walk` | A+D / G04；槽位限制、语法去歧义及组合 | `if typ not in ('n','k','b') and not (t['kind']=='Anaphor' and t['text']=='之'):yield from walk(t['end'],new)` |
| construction_ir.py:163 `matches` | A+D / G04；槽位限制、语法去歧义及组合 | `if k=='pair_increment' and text[start:start+1]!='加' and '加' not in text[start:end] and text[s['receiver'][0]:s['receiver'][1]] not in ('大餘','小餘'):continue` |
| construction_ir.py:164 `matches` | A+D / G04；槽位限制、语法去歧义及组合 | `if k=='declaration' and text[s['label'][0]:s['label'][1]] in ('大餘','小餘'):continue` |
| construction_ir.py:179 `build` | A+D / G04；槽位限制、语法去歧义及组合 | `return node(public,a,b,ids,list(ids.values()),'G_'+kind.upper()+'_'+str(GRAMMAR.index((kind,public,pattern))),lowering_kind=kind,attributes={'continuation':pattern.startswith('餘以')})` |
| construction_ir.py:201 `parse_syntax` | A+D / G04；槽位限制、语法去歧义及组合 | `for suffix in ('并之','從之'):` |
| context_compiler.py:48 `operand` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `name=slot.get('text','').removeprefix('其')` |
| context_compiler.py:49 `operand` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if name in ('','之','所得'):return self.focus` |
| context_compiler.py:50 `operand` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if name=='餘':return self.remainder` |
| context_compiler.py:76 `accept_outputs` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `elif k=='divide_by' and s.get('value',{}).get('text')=='大餘':receiver='大餘';port='remainder'` |
| context_compiler.py:77 `accept_outputs` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if receiver and receiver not in ('之','其餘','所得') and port in out:` |
| context_compiler.py:78 `accept_outputs` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `self.bind(c,receiver.removeprefix('其'),out[port],'receiver_update')` |
| context_compiler.py:120 `compile_cycle_slices` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if k in ('pending_cycle','cycle_divide') and s.get('value',{}).get('text') in ('積日','大餘','積度') and s.get('divisor',{}).get('kind')=='Number':` |
| context_compiler.py:123 `compile_cycle_slices` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `start=i;cycle=s['divisor']['value'];unit='du' if s['value']['text']=='積度' else 'day'` |
| context_compiler.py:124 `compile_cycle_slices` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if start is None or k not in ('count_origin','count_command') or s.get('origin',{}).get('text') not in ('統首日','所入蔀名','蔀名','角首'):continue` |
| context_compiler.py:136 `compile_cycle_slices` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if unit=='day' and '大餘' in builder.names:return_label='大餘'` |
| context_compiler.py:241 `compile_schedule_slices` | A+B+D / G06–G07；方法识别／绑定及语义类型 | `if origin!='天正':continue` |
| control_ir.py:23 `resolve_control` | A+D / G05；Repeat 构造 | `count=next((x for x in tail if x['text']=='數所得'),None)` |
| inputs.py:7 `<module>` | A / L01；输入数词解析 | `NUMERALS = '零〇一二三四五六七八九十百千萬万兩两'` |
| inputs.py:13 `number` | A / L01；输入数词解析 | `digits = dict(zip('零一二三四五六七八九', range(10)))` |
| inputs.py:14 `number` | A / L01；输入数词解析 | `digits.update({'〇':0, '兩':2, '两':2})` |
| inputs.py:19 `number` | A / L01；输入数词解析 | `elif char in '十百千':` |
| inputs.py:20 `number` | A / L01；输入数词解析 | `section += (digit or 1) * {'十':10, '百':100, '千':1000}[char]` |
| inputs.py:22 `number` | A / L01；输入数词解析 | `elif char in '萬万':` |
| lexical.py:6 `<module>` | A+B / L03；边界与整词声明筛选 | `BOUNDARY=set('不者則也命各來以乘減加於于并從上置盈滿得為名曰除去起求推其之亦又每皆倍，,；;．。：:日分零〇一二三四五六七八九十百千萬万0123456789')` |
| lexical.py:11 `tokenize_candidates` | A+B / L03；边界与整词声明筛选 | `for m in re.finditer(r'(?:^\|[，,．。；;])([^，,．。；;\s零〇一二三四五六七八九十百千萬万0123456789]+?)('+NUMBER+r')(?=[，,．。；;]\|$)',text):` |
| lexical.py:12 `tokenize_candidates` | A+B / L03；边界与整词声明筛选 | `if not any(x in m.group(1) for x in ('置','加','盈','推','求','以','得','除','乘','為','分之')):terms.add(m.group(1))` |
| lexical.py:27 `tokenize_candidates` | A+B / L03；边界与整词声明筛选 | `if ch in BOUNDARY:add(i,i+1,'Anaphor' if ch in '其之' else 'Syntax')` |
| pipeline.py:43 `get` | A+C / L07–L10、L13；名称及参数绑定 | `if name in ('之','其餘','所得',''):` |
| pipeline.py:48 `get` | A+C / L07–L10、L13；名称及参数绑定 | `if name.startswith('其'):name=name[1:]` |
| pipeline.py:65 `get` | A+C / L07–L10、L13；名称及参数绑定 | `is_parameter=parameter or name.endswith('法') or name in ('章閏','章歲','章月','蔀月','蔀日')` |
| pipeline.py:72 `context` | A+C / L04；源声明／别名与单位 | `declaration_pattern = r'(?:^\|[，,．。；;])\s*([^，,．。；;\s' + '零〇一二三四五六七八九十百千萬万0-9' + r']{1,12})[，,]?\s*(' + NUMBER + r')(?=[，,．。；;]\|$)'` |
| pipeline.py:78 `context` | A+C / L04；源声明／别名与单位 | `items += [(m.start(),'alias',m) for m in re.finditer(r'因為([^，,．。；;]+)',context_text)]` |
| pipeline.py:83 `context` | A+C / L04；源声明／别名与单位 | `if any(x in label for x in ('推','乘','減','滿','得','除','以')):continue` |
| pipeline.py:102 `prescan` | B+D / G10；历法 schedule | `for m in re.finditer('('+NUMBER+')歲('+NUMBER+')閏',d['analysis_text']):` |
| pipeline.py:127 `medial_month_bridge` | E+C / E01；跨量种桥接及证据 | `for label,expected in (('章歲',19),('章月',235)):` |
| pipeline.py:146 `medial_month_bridge` | E+C / E01；跨量种桥接及证据 | `if '見月法' not in divisor['labels']:return None` |
| pipeline.py:159 `binary` | A+E+C / E01；量运算／桥接 | `if kind=='multiply' and ('章歲' in lv['labels'] and rv['unit']=='medial_fraction'):` |
| pipeline.py:182 `divide` | B+C / L11；除数名驱动单位及分母 | `if labels & {'章歲','章法','見月法','月法'}:unit='month' if labels & {'章歲','章法','見月法'} or self.env.scope.get('planet') else 'day'` |
| pipeline.py:183 `divide` | B+C / L11；除数名驱动单位及分母 | `elif labels & {'日法','蔀月'}:unit='day'` |
| pipeline.py:184 `divide` | B+C / L11；除数名驱动单位及分母 | `elif '見中法' in labels:unit='medial'` |
| pipeline.py:185 `divide` | B+C / L11；除数名驱动单位及分母 | `elif '章月' in labels:unit='intercalary_month'` |
| pipeline.py:198 `abandon_pending_cycle` | A / G01；缺失除之的诊断 | `self.env.issue('incomplete_construction',spans,['除之'],reason=reason)` |
| pipeline.py:199 `abandon_pending_cycle` | A / G01；缺失除之的诊断 | `diagnostic={'kind':'incomplete_construction','message':reason,'source_spans':spans,'missing_continuation':'除之'}` |
| pipeline.py:207 `remainder` | B+C / L12；余数类型筛选 | `expected={'小餘':'day_fraction','中餘':'medial_fraction','月餘':'month_fraction'}.get(label,UNITS.get(label))` |
| pipeline.py:241 `count` | B+E / G09；原点／计数／日历循环 | `def count(self,offset,origin_name,spans,role=None,convention='算外'):` |
| pipeline.py:244 `count` | B+E / G09；原点／计数／日历循环 | `if origin_name in ('統首日','所入蔀名'):` |
| pipeline.py:255 `count` | B+E / G09；原点／计数／日历循环 | `civil=re.search('('+NUMBER+')月',origin_name)` |
| pipeline.py:262 `count` | B+E / G09；原点／计数／日历循环 | `if origin_name in ('統首日','所入蔀名'):` |
| pipeline.py:270 `recall` | B+D / G09；计日方法调用 | `big=self.get('大餘',spans)` |
| pipeline.py:271 `recall` | B+D / G09；计日方法调用 | `call=self.env.event('method_call',{'offset':big,'origin':method['origin'],'cycle':method['cycle']},['remainder','result'],spans,'R12',{'target':method['event_id'],'method':'cycle_and_count','convention':method['convention'],'inferred':inferred},{'remainder':{'role':'remainder','unit':'day'},'result':{'role':'day_index','unit':'ordinal','labels':['朔日']}})` |
| pipeline.py:272 `recall` | B+D / G09；计日方法调用 | `self.env.alias(call['writes']['remainder'],'大餘',spans,'R12')` |
| pipeline.py:276 `finish_query` | B+E+D / G09；大餘小餘隐式进位 | `if not {'大餘','小餘'} <= set(self.branch_additions):return` |
| pipeline.py:283 `finish_query` | B+E+D / G09；大餘小餘隐式进位 | `small=self.get('小餘',spans);big=self.get('大餘',spans)` |
| pipeline.py:286 `finish_query` | B+E+D / G09；大餘小餘隐式进位 | `self.env.alias(d['writes']['remainder'],'小餘',spans,'R12')` |
| pipeline.py:288 `finish_query` | B+E+D / G09；大餘小餘隐式进位 | `self.env.alias(carry,'大餘',spans,'R11')` |
| pipeline.py:304 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.startswith('求'):` |
| pipeline.py:306 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.startswith('推'):` |
| pipeline.py:308 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `return bool(text[1:]) and not any(operator in text[1:] for operator in ('乘','減','得一','除之','去之'))` |
| pipeline.py:309 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text in ('算外','筭外','筭盡之外'):` |
| pipeline.py:312 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text in ('則朔日也','則前年天正十一月朔日也','則星所見中次也','則星所見月也','星合所在之月也'):` |
| pipeline.py:315 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text=='入章' or re.fullmatch('('+NUMBER+')歲('+NUMBER+')閏',text):` |
| pipeline.py:317 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text=='至有閏之歲':` |
| pipeline.py:319 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if re.fullmatch('除('+NUMBER+')',text) and self.scan_event is not None:` |
| pipeline.py:322 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(?:其)?(.*?)(?:滿)?('+NUMBER+r')以上(?:至('+NUMBER+r')(.+))?',text)` |
| pipeline.py:324 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `name=m.group(1).removesuffix('滿');x=self.get(name,sp) if name else self.env.focus` |
| pipeline.py:329 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text in ('歲有閏','其歲有閏','其月大'):` |
| pipeline.py:333 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text=='閏或進退':` |
| pipeline.py:335 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text=='以朔制之':` |
| pipeline.py:343 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text in ('數除如法','命之如前'):` |
| pipeline.py:346 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(中數\|次數\|數)?從(.+)起',text)` |
| pipeline.py:348 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `role={'中數':'medial_ordinal','次數':'station_ordinal'}.get(m.group(1))` |
| pipeline.py:351 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if m.group(2)=='統首日':offset=self.get('大餘',sp);role='day_index'` |
| pipeline.py:353 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'不盈者數起[於于](.+)',text)` |
| pipeline.py:357 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'以(.+)命之',text)` |
| pipeline.py:359 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `self.count(self.get('大餘',sp),m.group(1),sp,'day_index','筭盡之外');return True` |
| pipeline.py:360 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.startswith('倍'):` |
| pipeline.py:364 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `two=self.literal('二',sp)` |
| pipeline.py:366 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `self.env.events[self.env.values[two]['producer']]['attributes']['basis']='semantic multiplier of 倍'` |
| pipeline.py:374 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.startswith('所得'):` |
| pipeline.py:378 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(不盈者\|不滿\|不盡\|其餘\|餘)(?:名曰\|名為\|為\|則)(.+?)(?:也)?',text)` |
| pipeline.py:381 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(?:名曰\|名為\|為\|則)(.+?)(?:也)?',text)` |
| pipeline.py:385 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'置(.+?)(?:減('+NUMBER+'))?',text)` |
| pipeline.py:394 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'((?:又\|每)?以.+?乘.+?)(從之\|為.+\|名曰.+)',text)` |
| pipeline.py:397 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(.*?(?:盈\|滿).+?得一)(為.+\|名曰.+)',text)` |
| pipeline.py:400 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'((?:從\|上加).+?)(為.+)',text)` |
| pipeline.py:403 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(?:又\|每)?以(.+?)乘(.+)',text)` |
| pipeline.py:407 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `self.binary('multiply',left,right,sp,attrs={'word_order':[m.group(1),m.group(2)],'quantifier':'each' if text.startswith('每') else None});return True` |
| pipeline.py:408 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'以(.+?)減(.+)',text)` |
| pipeline.py:411 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(.*?)(?:盈\|滿)(?:其)?(.+?)得一',text)` |
| pipeline.py:419 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'以(.+?)除(.+)',text)` |
| pipeline.py:422 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if self.schedule and self.env.values[x]['unit']=='month' and re.fullmatch(NUMBER,m.group(1)) and m.group(2)=='之' and '至有閏之歲' in re.sub(r'\s+','',self.doc['text'][indices[-1]+1:]):` |
| pipeline.py:427 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(.+?)(?:盈\|滿)(.+?)(?:去之)?',text)` |
| pipeline.py:428 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if m and '以上' not in text:` |
| pipeline.py:430 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.endswith('去之'):self.divide(x,d,sp,True)` |
| pipeline.py:433 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text=='除之' and self.pending_cycle:` |
| pipeline.py:435 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(.+?)以(.+?)(?:除去之\|去之)',text)` |
| pipeline.py:438 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(?:并\|從\|上加)(.+)',text)` |
| pipeline.py:441 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if name=='之':` |
| pipeline.py:444 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `self.env.bind('之',self.env.products[:-1],left,sp,'R03')` |
| pipeline.py:447 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if text.startswith(('從','上加')):` |
| pipeline.py:449 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `result=self.binary('add',left,right,sp,'R11' if text.startswith(('從','上加')) else 'R03',{'receiver_label':name})` |
| pipeline.py:450 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `if name=='大餘':self.env.alias(result,name,sp)` |
| pipeline.py:452 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'加(.*?)('+NUMBER+')',text)` |
| pipeline.py:457 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'(小餘\|大餘)('+NUMBER+')',text)` |
| pipeline.py:460 `parse_clause` | A+B+C+D+E / G01、G10–G11；v2 语句分派；整句特例与通用构式并存 | `m=re.fullmatch(r'加(.+)',text)` |
| pipeline.py:473 `run` | A / G01；不完整周期阻断 | `if self.pending_cycle is not None and text!='除之':` |
| pipeline.py:474 `run` | A / G01；不完整周期阻断 | `self.abandon_pending_cycle('pending cycle reduction was interrupted before 除之',[original_span])` |
| pipeline.py:481 `run` | A / G01；不完整周期阻断 | `self.abandon_pending_cycle('pending cycle reduction reached end of document before 除之')` |
| program_ir.py:31 `compile_frames` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `if is_head and not independent and owner is not None and target=='中部二十四氣':` |
| program_ir.py:34 `compile_frames` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `if is_head and (independent or owner is None or slots.get('marker',{}).get('text')=='推'):` |
| program_ir.py:56 `compile_frames` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `label=v.get('text','').removeprefix('其')` |
| program_ir.py:93 `static_interface` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `if kind=='count_origin' and slot=='origin' and v['text'] not in ('統首日','所入蔀名','蔀名'):continue` |
| program_ir.py:95 `static_interface` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `label=v.get('text','').removeprefix('其')` |
| program_ir.py:96 `static_interface` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `if label in ('','之','所得','餘','法'):continue` |
| program_ir.py:105 `static_interface` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `for label,port in [('統首日','head'),('入統歲數','local')]:defined[label]={'node_id':nid,'port':port}` |
| program_ir.py:106 `static_interface` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `if kind=='method_value_reference':uses.setdefault('統首日',{'uses':[],'roles':[]})['uses'].append(nid);uses['統首日']['roles'].append('origin')` |
| program_ir.py:152 `require` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `for receiver in ('大餘','小餘'):uses.pop(receiver,None)` |
| program_ir.py:153 `require` | A+C+D / T01、T03、G08；定义边界及静态依赖 | `uses['統首日']={'uses':[c['node_id'] for c in body],'roles':['origin']}` |
| scoped.py:103 `context` | B+C+E / L04、E04、profiles；参数类型／尺度／学术补入 | `if unit=='month_fraction' and len(self.env.parameters.get('見月法',[]))==1:` |
| scoped.py:104 `context` | B+C+E / L04、E04、profiles；参数类型／尺度／学术补入 | `self.env.reconcile_value(vid, {'scale': {'denominator':self.env.parameters['見月法'][0]}})` |
| scoped.py:111 `context` | B+C+E / L04、E04、profiles；参数类型／尺度／学术补入 | `supports=[s for x in self.context_ir['declarations'] for s in x['source_spans'] if x['label'] in ('章月','章法')]` |
| scoped.py:119 `get` | C+D / L09；名称归一化 | `aliases={'元':'元法','統':'統法','蔀名':'所入蔀名','入蔀年數':'入蔀年'}` |
| scoped.py:147 `switch` | D+C / T02；task 继承状态 | `if task=='intercalation':inherited.update({k:v for k,v in self.states.get('new_moon',{}).items() if k in ('閏餘','積月')})` |
| scoped.py:161 `medial_month_bridge` | E+C / E01；木星量种桥接 | `if frame['kind']=='divmod' and '見中法' in self.env.values[frame['reads']['divisor']]['labels']:` |
| scoped.py:162 `medial_month_bridge` | E+C / E01；木星量种桥接 | `values=[v for label in ('章歲','章月') for v in self.env.parameters.get(label,[])]` |
| scoped.py:190 `binary` | A+C+E / T04、rates；率与算术兼容性 | `elif self.task=='intercalation' and kind=='subtract' and ('章法' in lv.get('labels',[]) or '章歲' in lv.get('labels',[])) and isinstance(rv.get('scale'),dict) and rv['scale'].get('denominator')==left:` |
| scoped.py:282 `name` | D+B / T06；label 专用输出 | `ports={'new_moon':{'積月':'months','閏餘':'intercalation_remainder','積日':'whole_days','小餘':'small_remainder','大餘':'day_offset'},'winter':{'大餘':'winter_whole_residual','小餘':'winter_remainder'}}` |
| scoped.py:285 `name` | D+B / T06；label 专用输出 | `if self.task=='winter' and label=='小餘':` |
| scoped.py:293 `count` | D+B / T06；别名及输出 | `def count(self,offset,origin_name,spans,role=None,convention='算外'):` |
| scoped.py:294 `count` | D+B / T06；别名及输出 | `origin_name={'蔀名':'所入蔀名'}.get(origin_name,origin_name)` |
| scoped.py:312 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `signatures={(m['cycle_value'],{'蔀名':'所入蔀名'}.get(m['origin_label'],m['origin_label'])) for m in methods}` |
| scoped.py:319 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `big=self.get('大餘',spans)` |
| scoped.py:327 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `first=self.inferred_value('literal',{},spans,'RESCUE_ORIGIN_DAY',{'value':frame['origin_day'],'source_label':'甲子'},{'unit':'day_index'},frame['basis'])` |
| scoped.py:332 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `small=self.env.active.get('小餘')` |
| scoped.py:345 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `self.env.alias(e['writes']['remainder'],'大餘',spans,'V3_CALL');self.branch_finalized=True` |
| scoped.py:347 `recall` | D+B+E / G09、profiles、T07；计日方法选择／历元／query 导出 | `elif current=='new_moon' and self.env.query in ('其次月','後月朔'):` |
| scoped.py:401 `start_query` | D / T07；含氣 query 切域 | `if self.task in ('winter','qi') and ('氣' in label):` |
| scoped.py:414 `export_threshold` | B+D / T06；判断短语选择输出 | `if judgment in ('歲有閏','其歲有閏'):self.export('has_intercalation',e['writes']['result'],'new_moon')` |
| scoped.py:415 `export_threshold` | B+D / T06；判断短语选择输出 | `if judgment=='其月大':self.export('month_long',e['writes']['result'],'new_moon')` |
| scoped.py:425 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `one=self.literal('一',sp);v=self.inferred_value('subtract',{'left':v,'right':one},sp,'V3_ORDINAL',{}, {'unit':'year'},profile['basis'])` |
| scoped.py:433 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `value=self.inferred_value('add',{'left':self.env.focus,'right':self.literal('一',sp)},sp,'RESCUE_LOCAL_COUNT',{'count_convention':'inclusive','local_phrase':c['text']},{'unit':'year'},profile['basis']);self.env.focus=value;return True` |
| scoped.py:440 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `self.concordance_divisor=self.get('統法',sp,True);self.concordance_local=self.entry_remainder;self.concordance_condition_spans=sp;return True` |
| scoped.py:458 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `self.export('concordance_index',e['writes']['index']);self.export('local_elapsed_years',e['writes']['local']);self.export('head_day',e['writes']['head']);self.env.alias(e['writes']['local'],'入統歲數',sp);self.env.alias(e['writes']['head'],'統首日',sp);return True` |
| scoped.py:462 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `self.era_index=self.env.value('count',{'offset':self.entry_div['writes']['quotient']},sp,'V3_TABLE_COLUMN',{'ordinal_origin':0,'cyclic':False,'sequence':['天紀','地紀','人紀'],'convention':'筭外'},{'unit':'table_column'});self.export('era_index',self.era_index);self.env.focus=self.entry_remainder;return True` |
| scoped.py:464 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `if kind=='divide_by' and slots['value']['text']=='之':` |
| scoped.py:467 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `q=self.entry_div['writes']['quotient'];one=self.literal('一',sp)` |
| scoped.py:469 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `tables=self.context_ir['tables'];matching=[t for t in tables if '蔀首日' in t.get('columns',[])]` |
| scoped.py:472 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `e=self.env.event('lookup',{'row':row,'column':self.era_index},['head_day','head_year'],sp,'V3_LOOKUP',{'table':table,'day_column':table['columns'].index('蔀首日'),'row_base':1,'column_base':0},{'head_day':{'unit':'day_index'},'head_year':{'unit':'year_index'}})` |
| scoped.py:474 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `self.env.alias(e['writes']['head_day'],'所入蔀名',sp)` |
| scoped.py:477 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `self.export('years_into_obscuration',u);self.export('local_elapsed_years',local);self.env.alias(u,'入蔀年',sp)` |
| scoped.py:480 `lower_entry` | C+D+E / E03、profiles；三统四分历元与查表解释 | `e=self.env.event('count',{'offset':self.ex('era_entry','local_elapsed_years'),'origin':self.ex('era_entry','head_year'),'cycle':self.literal('六十',sp)},['result'],sp,'V3_YEAR_NAME',{'cyclic':True,'cycle':60,'convention':'筭上','zero_offset_at_origin':True},{'result':{'unit':'year_index'}})` |
| scoped.py:486 `normalize_query` | B+D / T07；日分余数导出 | `small=self.env.active.get('小餘')` |
| scoped.py:512 `lower_intercalation` | C+D+E / E05；闰月位置解释 | `if c['kind']=='count_origin' and '十一月' in c['slots']['origin']['text']:` |
| scoped.py:519 `nominal` | C+E / E05；月份命名模型 | `one=self.literal('一',sp);slot=self.binary('add',count,one,sp,'V3_COUNT')` |
| scoped.py:526 `nominal` | C+E / E05；月份命名模型 | `cycle=self.literal('十二',sp)` |
| scoped.py:560 `lower_primitive` | A+B+C+D+E / G01、G11、T08；算术语法内的task／单位／label专门处理 | `denominator=self.env.values[dividend].get('scale',{}).get('denominator') if divisor in ('其法','法') and isinstance(self.env.values[dividend].get('scale'),dict) else None` |
| scoped.py:570 `lower_primitive` | A+B+C+D+E / G01、G11、T08；算术语法内的task／单位／label专门处理 | `if slots['value']['text']=='大餘':self.env.alias(e['writes']['remainder'],'大餘',sp)` |
| scoped.py:574 `lower_primitive` | A+B+C+D+E / G01、G11、T08；算术语法内的task／单位／label专门处理 | `if slots['value']['text']=='大餘':self.env.alias(e['writes']['remainder'],'大餘',sp)` |
| scoped.py:605 `lower` | A+C+D+E / T01、T03、T08、G13；语义分派与气／五行解释 | `region=following_region(self.all_candidates[self.doc['doc_id']],c,postposed_targets=('中部二十四氣',))` |
| scoped.py:608 `lower` | A+C+D+E / T01、T03、T08、G13；语义分派与气／五行解释 | `self.normalize_query(sp);self.switch('qi',sp);super().start_query('二十四氣',sp)` |
| scoped.py:638 `lower` | A+C+D+E / T01、T03、T08、G13；语义分派与气／五行解释 | `v=self.env.value('fraction',{'whole':whole,'numerator':numerator,'denominator':denom},sp,'V3_MIXED',{'source_representation':{'whole':c['slots']['whole']['text'],'numerator':c['slots']['numerator']['text'],'denominator':c['slots'].get('denominator',{}).get('text',{'inherited_value_id':denom})},'historical_role_alternatives':['中央','water_before_central'] if c['kind']=='mixed_compact' and c['slots'].get('label',{}).get('text')=='中央' and self.env.scope.get('tradition')=='San_tong_li' and getattr(self,'temporal_anchor',None) else [],'temporal_anchor':getattr(self,'temporal_anchor',None)},{'unit':'day','quantity_kind':'duration'})` |
| scoped.py:655 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `self.env.alias(value,'大餘',sp,'RESCUE_METHOD_ARGUMENT')` |
| scoped.py:668 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `interval=bool(profile and amount_name in ('積月','後月餘') and self.env.scope.get('planet')=='Jupiter')` |
| scoped.py:691 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `if label=='之':` |
| scoped.py:693 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `left,right=self.env.products[-2:];self.env.bind('之',self.env.products[:-1],left,sp,'R03')` |
| scoped.py:697 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `if label!='之':self.env.alias(v,label,sp)` |
| scoped.py:709 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `role='day_index' if origin=='統首日' else None` |
| scoped.py:710 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `self.count(self.get('大餘',sp) if role else self.env.focus,origin,sp,role);return True` |
| scoped.py:711 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `if k=='count_command':self.count(self.get('大餘',sp),s['origin']['text'],sp,'day_index','筭盡之外');return True` |
| scoped.py:715 `lower_token_construct` | A+B+C+D+E / G08、G09、profiles；原点／参数／接收者及基本操作 | `factor=self.literal('二',sp);self.branch_support.extend(sp)` |
| scoped.py:742 `temporal_views` | D+E / T09；由特定导出及大餘进位建时间坐标 | `big=next((e for e in increments if e['attributes'].get('receiver')=='大餘'),None)` |
| scoped.py:764 `boundary_view` | D+E / T09；月气序列／边界模型 | `big=next((e for e in increments if e['attributes'].get('receiver')=='大餘'),None);small=next((e for e in increments if e['attributes'].get('receiver')=='小餘'),None)` |
| scoped.py:834 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `profile=p.program.initial_frame;sp=definition['source_spans'];head=p.env.active.get('統首日')` |
| scoped.py:838 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `ordinal=p.get(profile['initial_input'],sp);denominator=p.get('日法',sp,True)` |
| scoped.py:840 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `p.linked_initial_base={'大餘':base['writes']['day_offset'],'小餘':base['writes']['fraction'],'統首日':head};p.day_denominator=denominator` |
| scoped.py:870 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `before=len(p.report['events']);sp=definition['source_spans'];small=p.get('小餘',sp);big=p.get('大餘',sp)` |
| scoped.py:871 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `denominator=p.get('日法',sp,True);division=p.divide(small,denominator,sp)` |
| scoped.py:872 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `p.env.alias(division['writes']['remainder'],'小餘',sp,'RESCUE_QUERY_CARRY')` |
| scoped.py:873 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `carried=p.binary('add',big,division['writes']['quotient'],sp,'RESCUE_QUERY_CARRY',{'receiver':'大餘','query_base_ref':definition.get('base_ref')})` |
| scoped.py:874 `lower_linked` | A+C+D+E / T08、profiles；链接执行／共享夜半base及进位 | `p.env.alias(carried,'大餘',sp,'RESCUE_QUERY_CARRY');p.recall(sp,True)` |

## 附录 D：task 比较全量索引

AST 枚举 `scoped.py` 中含 self.task / p.task 或局部 task/current/domain 的比较，包含 ==、!=、in、not in 和条件表达式。self.task 的比较共 24 处；不把重复比较计为不同能力。代码效果见 T01–T10、E05。

| 位置 | 条件 |
|---|---|
| scoped.py:131 | `self.task == task` |
| scoped.py:143 | `k[0] != task` |
| scoped.py:145 | `task not in self.states` |
| scoped.py:147 | `task == 'intercalation'` |
| scoped.py:148 | `task in ('nodes', 'qi')` |
| scoped.py:152 | `task in ('nodes', 'qi')` |
| scoped.py:188 | `self.task == 'era_entry'` |
| scoped.py:190 | `self.task == 'intercalation'` |
| scoped.py:204 | `self.task == 'era_entry'` |
| scoped.py:257 | `self.task != 'intercalation'` |
| scoped.py:269 | `self.task in ('winter', 'nodes', 'qi')` |
| scoped.py:273 | `self.task == 'new_moon'` |
| scoped.py:285 | `self.task == 'winter'` |
| scoped.py:298 | `self.task == 'new_moon'` |
| scoped.py:299 | `self.task == 'winter'` |
| scoped.py:346 | `current == 'winter'` |
| scoped.py:347 | `current == 'new_moon'` |
| scoped.py:349 | `current in ('nodes', 'qi')` |
| scoped.py:350 | `current == 'nodes'` |
| scoped.py:401 | `self.task in ('winter', 'qi')` |
| scoped.py:484 | `self.task not in ('nodes', 'qi')` |
| scoped.py:489 | `self.task == 'nodes'` |
| scoped.py:534 | `self.task == 'intercalation'` |
| scoped.py:586 | `self.task == 'winter'` |
| scoped.py:587 | `domain is None` |
| scoped.py:587 | `self.task == 'winter'` |
| scoped.py:596 | `task == 'qi'` |
| scoped.py:596 | `self.task == 'qi'` |
| scoped.py:598 | `task == 'nodes'` |
| scoped.py:602 | `self.task == 'era_entry'` |
| scoped.py:603 | `self.task == 'intercalation'` |
| scoped.py:607 | `self.task in ('nodes', 'winter')` |
| scoped.py:626 | `self.task in ('qi', 'nodes')` |
| scoped.py:722 | `self.task in ('nodes', 'qi')` |
| scoped.py:724 | `self.task == 'winter'` |
| scoped.py:725 | `self.task == 'new_moon'` |
| scoped.py:741 | `e['scope'].get('task') == task` |
| scoped.py:743 | `e['scope'].get('task') == task` |
| scoped.py:763 | `e['scope'].get('task') == task` |
| scoped.py:818 | `p.task == 'winter'` |
| scoped.py:820 | `p.task == 'winter'` |

附录 C 共 184 个含中文字面值的代码行。它是覆盖索引，不是声称每一行都是独立领域规则。
