# Deterministic Pattern Lab annotation reference（evaluation only）

本轮以 `ece6f5dc983ee22488d8777a52f92efe26f2beda` 冻结的 parser 为基线；不修改 UI、parser 或已有 operation crosswalk。旧的 agent-imported `proc-3.5.json` 已移除。现在所有 reference 都由完整原始 annotation 经 Python 机械生成，无逐条补写的 expectation。

## 输入、职责与复现

- `ch3-chunk-breakdown.json`：完整原始人工 JSON 的字节副本，25 chunks / 457 terms / 89 relations / 35 steps；保留所有原字段和缺省状态，不补空字段、不改文本。
- `source-chunks.json`：从现有 Cullen chunks 自动按 annotation chunk_id 取出的 25 条最小来源摘录，逐字段保留原 `source_text_zh`、procedure 和页码；登记完整上游文件 hash。它是 reference 坐标来源，不是 compiler 输入。
- `operation-crosswalk.json`：上一轮固定的 7 项 operation 映射，原字节不变；未新增 `add/count/divide/distribute/remove_modulus/seek` 等映射。
- `frozen-inputs.json`：HEAD、全部 production parser Python 文件、canonical corpus、原始 annotations、source excerpts 与 crosswalk 的 SHA-256；不匹配则停止评估。
- `../pattern_importer.py`：纯函数 `import_annotations(annotations, sources, packet, crosswalk)`；只做确定性语法解析、精确坐标恢复与 reference 序列化，无 production imports。
- `../pattern_reference.py`：沿用现有 evaluator，接收已编译 graph，支持同一 construction 对应多个 manual semantic steps；CLI 串联先编译、后导入、再评估。

Importer 与 comparator 分开是因为来源消歧/旧标注小语法不属于 graph matching，也不能进入生产 parser。没有新增 passage-specific 模块、operation、adapter 或学者判断。全文 batch source packet 在 evaluator 内从全部编号 corpus 章节机械建立；不改变生产 SourcePacket adapter。

```powershell
python -X utf8 -m evaluation.pattern_reference --output .cache/pattern-reference-run
python -X utf8 -m unittest discover -s tests -p 'test_pattern*.py' -v
```

输出包括 `imported.json`（全部 original 与派生层）、纯代码生成的 `proc-3.5.json`、local comparison、batch comparison、summary、两个 Markdown 对照和 `sha256.json`。JSON 使用可读 Unicode、固定键排序、固定 LF，无时间戳、绝对输出路径或随机 ID。大体积可再生输出只放 `.cache/`；本目录只登记简短结果和 hash 证据。

## 真实执行顺序与隔离

1. 独立生成已登记 Proc.3.5 canonical packet，调用 `parse_packet()`。
2. 独立读取 canonical 四分历全部 100 个编号章节，作为 primary documents 编译一次；不根据人工 chunk 选择范围，不导入人工术语/参数/steps。
3. 两次 compiler 都完成后，才读取完整 annotation、固定 crosswalk 和 reference source excerpts。
4. 从完整 JSON 分别生成 local/batch reference，交给只读 evaluator。

Proc.3.5 local packet 保持上一轮比较范围；batch packet 为全文范围，两种结果分列。测试实际监测文件打开时机和 compiler 调用次数，不只检查一串声明的阶段名。生产核心的隔离安装测试继续证明无需 evaluation/history。

## 确定性坐标规则

`original` 保存每个输入 chunk 的全部内容；term、relation、step 也保留原对象。所有 spans 都是原样 quote、doc_id、reading_id、Unicode code-point `[start,end)`；文档保留 SHA-256，canonical 文档保留文件偏移。旧 chunk 坐标不冒充 PDF 原件坐标。

- Mention：先枚举原 chunk 中 `anchor` 的所有完全相同出现处，再查其中 `text` 的完全相同出现处。唯一候选直接恢复；多个候选时，`mention_id` 的 `_NNN` 后缀仅能选择本 chunk 第 N 个 exact text occurrence，且必须仍在某个 exact anchor 内。无合法唯一结果则 `needs_review`。不通过拼音、term_id 或语义相似度猜测。
- Canonical 桥接：优先用完整 chunk 的逐字对应范围；若正文含校读差异，仅允许唯一、完全相同的首分句确定来源 document。每个具体 term/step 仍须独立精确映射，首分句定位不会批准后续校读变化。
- 桥接仅忽略 Unicode 空白及固定 `，,．。；;：:`。不替换文字、不去掉方括号/校读符号，不编辑任何 reading。每个已恢复 span 的 quote 仍取自未修改的来源字符串。
- 重复短语没有足够 occurrence 证据时保持 `needs_review`，不取第一次。step 中多个分句各保留 evidence span；`十二以上` 与 `其歲有閏` 因此可以共同支持一个判断步骤。

## Steps 小语法与 crosswalk

`order` 必须为唯一正整数；原数组仍完整保留，派生步骤按 order 排序。`phrase/op/input/parameter/output` 原样保留，unknown format 记录 `manual_schema_unparsed`。

小语法只接受：

```text
atom := outN | remN | quotN | decimal | Chinese-integer | CJK-label | identifier | true | false
call := value(atom) | presence(atom)
comparison := [atom-or-call] (>= | <= | > | < | = | == | !=) atom
assignment := identifier = expression
list := expression ； expression ...
sequence := expression ; expression ...
```

`key=value;...` 形成有唯一 key 的 assignments；`quotient=quot4;remainder=rem4` 机械生成两个明确 output ports；`value(閏餘)>=十二` 与 `>=四百四十一` 形成 comparison AST。`presence(朔)=true;presence(中)=false` 可以解析语法，但不因语法成功就声称已有语义映射。任意函数、算术表达式、校读数词及未知符号都不猜解。

只有固定 crosswalk 决定 legacy operation 对应哪些 current construction/event。未登记 operation 输出 `crosswalk_missing`；登记 operation 的超出已知形态、非标量 slots、未明确的 quotient/remainder port 输出 `needs_review` 或 `crosswalk_missing`，不补规则。`evaluation_expectation` 由 AST、已有输出符号表与固定 semantic contract 机械生成，绝不由逐步人工配置提供。

## 分层计分与结果含义

- Procedure steps 进入现有 comparator；检查 construction/event、source evidence、input producer/port、literal、前序引用、命名/阈值属性和 outputs。一个 load construction 允许匹配 set 与 subtract 两个步骤。
- ASTRO_TERM / PARAMETER / QUANTITY / CALC_OP 单独进入 lexical/semantic reference，保留原 type；本轮不把这些术语数量当成 operation 分母。
- 全部 relations 原样保留并标为 `not_current_parser_target`，没有 relation false negative。
- `reference_not_convertible` 与 `dependency_unavailable` 单列；不得算成 parser 缺失。`missing_machine_semantics`、`mismatch` 只描述已有明确 reference 的检查结果，不自动判定历史解释孰对孰错。
- 不执行数值，不判 graph closure，不清理 machine unresolved / linked diagnostics。旧标注未提供的 unit/scale/时间参照信息也不补全。

## 本轮结果与证据

详见 [batch-results.md](batch-results.md)、[proc-3.5-comparison.md](proc-3.5-comparison.md) 和 [output-sha256.json](output-sha256.json)。两个不同 PYTHONHASHSEED 的独立进程逐文件字节比较由测试执行；可用同一命令分别输出两个新目录，再比较其中 sha256.json。

测试包括：原 JSON 全量保留；纯代码 Proc.3.5 7/7；missing crosswalk；未知表达式；重复文本/suffix；Unicode 补充平面、组合符与换行；校读差异不自动通过；跨粒度映射；错 port、错 operand、错 threshold；先编译后读取；独立进程 byte/SHA identity。原 parser 61/94/78 和 production/reconciliation 边界另行重跑。

没有根据 batch 失败修改 parser 或扩大 crosswalk。软件测试不冒充真人审定。
