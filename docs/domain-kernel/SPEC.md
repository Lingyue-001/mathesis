# MATHesis Domain Knowledge Kernel — v0.1 review2

日期：2026-09-19。代码核查基点：`63ed5c2b12dbe6501f5f607ec7a062c9e7b50d46`。交付类型：**有结构校验的设计规格、数据注册表和纸面预期**。没有实现或运行新候选引擎，没有修改或提交仓库。

## 本轮要解决的事情

将原文中的未知技术词拆为可追溯的词素/概念候选，再按有限、类型化的组合规则建立更大的表达。研究者在任何卡点可复用同一schema选择、修改或组装缺失结构；决定进入编译输入，机器重新运行受影响的依赖部分。最终仍服务于操作、数量流、参照和程序关系的比较。

交付必须同时区分四项：原文证据、学者解释、工程建模提案、程序实测。当前目录的候选树属于人工编写的预期；`engine_observed_result`全部为null。

## 1. 知识层与运行层

知识注册表保留四类核心对象：LexicalCue、DomainConcept、CompositionRule、ScopedFact。构造器、来源和权限是其共同配套。运行时另有SourceOccurrence、SemanticCandidate/Claim、ReviewTicket、DecisionIntent、Authorization及执行图；这些对象不能混入历史概念的上下位关系。

`入蔀積月`的目标表示为`localized_quantity(scope.bu, accumulation(time.month))`。推导必须显示C01把積和月组合、C06再把入、蔀、前一个子项组合。注册表不存这条完整词的语义答案。由同一构造器生成中文说明时，可以显示“蔀范围内的累计月相关量”；中文句子不承担判断功能。

`章法=19`等完整词出现在ScopedFact中是局部声明证据；它们不会为词法/组合测试提前提供答案。测试时分成“只给primitive和组合规则”与“追加声明/选定解释”两个暴露阶段。

## 2. 多义与关系类型

日保留太阳、日单位两类候选；月保留月体、lunation、civil month等候选。四分历日率的Solar Rate解释见S-C79，不能由day-only cue产生。年/歲的区别限于当前材料，见S-C8。

法首先提示计算参数；divisor是该量在具体操作的使用角色，scale是数值表示的关系，同一个量可以兼任二者。它们不构成互斥的一条分类链。積提示汇集/累计结果的可能结构；并未宣称数学文献中的所有積都等于时间累计。

`subtype_of`、`has_part`、`derived_from`、`produces`、`reads`、`localized_in`和`alternative_to`分别定义。`derived_from`严格限定为解释/认识来源，归入provenance层。计算依赖继续使用既有event.reads/writes、value.producer/output_port；`produces`是writes的显示名称，更新关系只来自已记录操作。来源边不能充当计算端口绑定。

`localized_in`保留唯一内部名称，显示为“历法语义范围 / Semantic scope”；原文位置使用span/source_spans。scope.bu是范围概念候选，不能因出现它就声称绑定到某个具体蔀。

divmod的商与余数是两个输出端口，随后分数表示引用商、余数、分母。语法树、词义组合树、执行依赖图都可呈层次，但不能塞成同一棵树。

## 3. 组合器的最小契约

输入：原文及不可变reading、带源坐标的重叠token candidates、知识版本、已知的局部作用范围、有效人工决定。输出：结构化候选、子项、rule_id、证据、替代组、未满足条件、截断标识。

`child_ids`是构词推导的**有序直接成分**，顺序对应原文、规则pattern及变量绑定；不允许集合化或按ID排序。子项中保留積、入等cue叶节点。图导出时由父项数组位置生成0基`component_index`，它属于父子边，不能成为子节点全局序号。外层节点列表可以稳定排序，但不能改变每个节点的child_ids。候选身份摘要必须保留数组顺序。

`expression.arguments`记录语义槽位，`child_ids`记录构词成分；例如accumulation(month)仍须保留積与月两个构词子项。不得从语义槽的dict迭代顺序重建构词树。`has_part`只投影这一构词包含关系，不能据此构造执行依赖。

规则只接受同一reading内有序相邻跨度，且处于可作为术语的区域。跨逗号/操作边界乱拼词不合法。`入+S+Q`在名词性输入表达中可提出范围关系；独立动词用法不能被这一规则吞并。C05的分部候选同样不得吞掉`分之`的数值/构式读法。

类型检查按候选分支进行：`accumulation(month)`可行不等于证明月体词义在所有位置不可能。被某一组合排除的子项义，不应从全局词表删除。未知修饰项可保留为typed unknown，例如中法的中；未知节点不得以默认概念获得执行权限。

固定技术表达C08额外提出整式候选，保留来源与替代关系。不得把“识别實如法而一”解释为“结果等于1”。[S-BK314]

## 4. 权限与状态

OSCA分别指观察、提议、约束、授权；E单列执行。各字段与图区域可以同时处于不同阶段。一个原文数词已确认，不代表整个量的kind、unit、frame、scale、producer都已确认。

每个SemanticCandidate和SemanticClaim共享`#/$defs/StatusAxes`，分开记录support_status、constraint_status、authorization_status及authorization_refs；schema拒绝旧semantic_status单字段。`supported / underdetermined / not_authorized`为合法组合，不能压成一个进度条。authorized必须有有效引用且constraint=compatible；另外仍需运行时目标/分支/依赖检查，schema形状通过不等于授权已经有效。旧parser的candidate_state.status保持原语义，不替换为这组新状态。

K1自动生成的候选保持support=proposed、authorization=not_authorized、authorization_refs=[]、claim_authority=S；约束轴按实际局部检查填写。纸面树为authored，因此constraint=unchecked；不能把样例状态抄成机器检查结论。相容只说明暂未冲突，不能凭“只剩一个候选”获得授权。A是对明确字段的编译许可；historical truth不由布尔状态表示。用户可以在单独分支显式采纳一个解释假设；来源和假设性质须保留。

确定的原文构式可以自动授权操作；明确的量词表达可在解析和作用范围确认后支持对应unit。普通词素、标题、组合结果只有提议能力。明确的数字声明可授权本reading内的字面值；其历史含义与率关系仍需额外证据。

统一gate检查适用传统、天体、模型/程序关系、reading、参数绑定、必要前提和显式选择。scope缺失为underdetermined；已知冲突为incompatible。某个旧task字段是否应该成为硬限制，须逐条分析真实关系；不机械照抄旧metadata。标题可帮助定位，不能单独给商余赋单位。

## 5. 人工介入及机器恢复

机器到达局部不动点后，为缺失条件生成ReviewTicket。票据包含原文位置、当前假设、缺失字段、允许动作、候选及证据、预期恢复点。候选为空时仍可用同一构造器/操作schema组装结构，或保持未决。

研究者提交的是字段化DecisionIntent，经过目标、类型、scope、reading、冲突检查，再适配成正式compiler input。决定不会直接修改生成图。重新编译首先可沿用现有全量重编译来保证正确性；增量调度是后续优化，不能冒充已实现能力。

“选ordinal就自动走完”只有在其余前提齐备时成立。P02显式拆出index_base、reference_origin、counting_boundary和step_unit。仅确定ordinal时，下游不能偷补一基起点。若采用S-C46整组解释，并已提供235/19模型和参数绑定，机器才可继续经过年数→月数→商余。研究者补充多少字段、多少来源选择都应计入人工成本。

恢复按依赖图推进至新的不动点；仍缺输入、模型、基态、分母或producer的部分保持未决。可执行的局部子图允许单独核算，并清楚标为局部结果。撤销或更换reading后，依赖该决定的授权标stale；独立原文事实和不受影响部分保留。

## 6. 数量与数值表示

分别记录quantity concept、数值域、单位、计数坐标、表示方式、frame以及操作使用角色。旧backend的year_ordinal/day_fraction等标签可以通过适配器映射，知识层不沿用其全部混合分类。

P04的裸余数348来自整数divmod；在选定月→日模型下，它表示348/940日。分子整数、分母引用和表示单位均需保留。原文给出的raw remainder不能直接当同数值的完整日量。商余关系由同一个division producer与两个端口表达。

只给27759与940两个数，并不能证明转换意义。授权还需要参数的共同模型角色、输入月量种类和选定解释。裸整数运算可作诊断，不能标为历史语义执行完成。

## 7. 原文、校读与模型

P06保留repo的中法四十二及Cullen的三十二为不同reading。选择32产生派生analysis reading，保留旧文字与映射；没有选择时不得把32写进编译输入。[S-REPO; S-CCONST]

二十四气段的月餘/日餘是第二处独立问题，选中法32不能顺便改它。168/32为一年删去整60日部分后的余日21/4，绝不直接标作完整年长。[S-C49; S-L69]

确认后保留生成来源是本项目明确要求。2018年DISHAS文档支持suggested/validated区分，但同时说验证后会丢失生成来源记忆；本项目在这里采用不同的保存规则。[S-DTI8]

## 8. 范围与验证

v0.1只验证最小候选/人工续推接口，不扩展全部五星/食模型。已有标题分派、现有日分赋值问题等必须在正式接lowering之前处理；本轮未修复。

六组纸面probe覆盖组合、计数坐标、实例绑定、率/商余、含日的陌生compound、多reading与跨传统同名词。它们是开发期公开样例，不是未见文本泛化验证。后续保留未参与规则设计的文本窗口；完整词禁用测试必须同时禁用TERMS、UNITS、alias、profile和整句分支可能泄漏的答案。

最小验收同时看正确候选覆盖、错误授权数、分母与端口保持、人工改动后新增可解项、撤销失效、未支持结构的保留。新增可解项不能通过扩大一次人工决定的隐藏内容伪造。

## 9. 交付与下一轮

`kernel.schema.json`检查设计记录的形状；`kernel.registry.json`保存候选概念、组合器和有限事实；`paper-probes.json`保存人工预期；`runtime-contract-examples.json`提供票据/决定规格。

`SCHEMA_REFERENCE.md`、`PAPER_PROBES.md`和`CONSUMPTION_CONTRACT.md`由本包交付的`../tools/design_tools.py`从这些JSON再生，可用--check-docs只读核对。当前只与本包数据绑定，尚未挂到repo的build/CI。代码联动需增加每个consumer的字段契约与效应测试，详见`CODE_INTEGRATION.md`。

下一轮Codex任务应限于隔离的suggestion-only模块和这些接口的测试。先证明不登记整词仍产生递归候选，且不修改canonical unit/role/scale；通过后再接人工裁决与lowering。此规格review2可审阅，尚未作为冻结生产契约部署。

## 10. 当前集成位置（review2）

最新阅读入口为tools/parser_inspector/readable.py::compile_view，直接执行automatic和empty-session reviewed两条路径；旧runner.run仍承担原始文件输出。K1必须在这两个既有入口中使用同一个suggest_packet_semantics，仅增加默认关闭的旁路产物。不得用runner替换compile_view、不得删掉双路径比较、不得修改render_html或app界面。

新的corpus输入复用build_source_packet_from_units；旧两项procedure registry仅用于legacy smoke。新增evaluation.semantic_regression._canonical会排序列表，只服务既有R1–R4基线，禁止对新构词树/ID应用它。新候选另保留有序child_ids。完整施工范围、测试和白名单见../CODEX_START_HERE.md与../REPO_MAPPING.md。
