# Paper Probes — 0.1.0-review2

六组已公开开发预期，authored_expected_nodes由人工编写，engine_observed_result全部为null。本次工具只验证已给结构及参考算术；本文件不代表新引擎运行结果。

## 阅读约定

节点表child_ids保持直接成分原文顺序；候选树、语义表达、状态三轴分别保存。操作预期、人工后续和执行预期不能混为K1验收。

## P01 — 積月：禁止整词语义查表

source_class: attested_excerpt

### 原文与reading

```json
[
  {
    "doc_id": "P01.text",
    "reading_id": "P01.text.reading1",
    "text": "積月",
    "source_sha256": "050fd2a2cd5254c4681fc94b0ab9c301c181cb8b03089202d904ecaa9a7e5ade",
    "basis_ids": [
      "S-C46"
    ],
    "source_note": "Attested micro-excerpt; coordinates are local to this exact excerpt, not offsets into full book."
  }
]
```


### 禁用整词捷径

```json
[
  "積月"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P01.ji | {"doc_id":"P01.text","end":1,"quote":"積","reading_id":"P01.text.reading1","source_sha256":"050fd2a2cd5254c4681fc94b0ab9c301c181cb8b03089202d904ecaa9a7e5ade","start":0} | ["cue",null,"LC06"] | [] | {"concept_id":"compute.accumulation","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P01.yue | {"doc_id":"P01.text","end":2,"quote":"月","reading_id":"P01.text.reading1","source_sha256":"050fd2a2cd5254c4681fc94b0ab9c301c181cb8b03089202d904ecaa9a7e5ade","start":1} | ["cue",null,"LC02"] | [] | {"concept_id":"time.month","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P01.total | {"doc_id":"P01.text","end":2,"quote":"積月","reading_id":"P01.text.reading1","source_sha256":"050fd2a2cd5254c4681fc94b0ab9c301c181cb8b03089202d904ecaa9a7e5ade","start":0} | ["composition","C01",null] | ["P01.ji","P01.yue"] | {"arguments":{"quantity":{"concept_id":"time.month","op":"concept"}},"op":"accumulation"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P01.total",
    "child_id": "P01.ji",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P01.total",
    "child_id": "P01.yue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  }
]
```


### 预期与边界

```json
[
  "至少形成accumulation(month)候选；另保留月体词义线索，由类型检查标明该组合不适用，而不全局删除该sense。",
  "候选不确定是本年/月总数、经过月数、间隔参数；不提供producer或数值。",
  "日/月互换压力样例应只改变相应叶节点；不允许新增完整词映射。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[]
```


### 负例

```json
[
  "移除所有完整词语义入口后仍可构造同一候选。",
  "把標题改成冬至不得赋day。",
  "積度不应被强制解释为month。"
]
```


### 参考算术

```json
{}
```


只测候选，不要求执行。

engine_observed_result: null

## P02 — 入蔀年：序位判断与继续推导

source_class: attested_excerpt

### 原文与reading

```json
[
  {
    "doc_id": "P02.text",
    "reading_id": "P02.text.reading1",
    "text": "置入蔀年減一",
    "source_sha256": "328c390c371453bf91777b874bd8a0c19ea600f7fa6178da6385505d0ab57964",
    "basis_ids": [
      "S-C46"
    ],
    "source_note": "Attested micro-excerpt; coordinates are local to this exact excerpt, not offsets into full book."
  }
]
```


### 禁用整词捷径

```json
[
  "入蔀年"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P02.ru | {"doc_id":"P02.text","end":2,"quote":"入","reading_id":"P02.text.reading1","source_sha256":"328c390c371453bf91777b874bd8a0c19ea600f7fa6178da6385505d0ab57964","start":1} | ["cue",null,"LC12"] | [] | {"concept_id":"relation.entry","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P02.bu | {"doc_id":"P02.text","end":3,"quote":"蔀","reading_id":"P02.text.reading1","source_sha256":"328c390c371453bf91777b874bd8a0c19ea600f7fa6178da6385505d0ab57964","start":2} | ["cue",null,"LC14"] | [] | {"concept_id":"scope.bu","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P02.year | {"doc_id":"P02.text","end":4,"quote":"年","reading_id":"P02.text.reading1","source_sha256":"328c390c371453bf91777b874bd8a0c19ea600f7fa6178da6385505d0ab57964","start":3} | ["cue",null,"LC03"] | [] | {"concept_id":"time.year","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P02.scoped | {"doc_id":"P02.text","end":4,"quote":"入蔀年","reading_id":"P02.text.reading1","source_sha256":"328c390c371453bf91777b874bd8a0c19ea600f7fa6178da6385505d0ab57964","start":1} | ["composition","C06",null] | ["P02.ru","P02.bu","P02.year"] | {"arguments":{"quantity":{"concept_id":"time.year","op":"concept"},"scope":{"concept_id":"scope.bu","op":"concept"}},"op":"localized_quantity"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P02.scoped",
    "child_id": "P02.ru",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P02.scoped",
    "child_id": "P02.bu",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P02.scoped",
    "child_id": "P02.year",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 2
  }
]
```


### 预期与边界

```json
[
  "组合得到year-in-bu候选；原文明示load/subtract1由grammar处理。",
  "仅ordinal标签不足以授权elapsed；起点/序号基数/端点分别有证据。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[
  {
    "id": "P02.D1",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "set_quantity_semantics",
    "target_description": "入蔀年输入出现处，尚非减一后的输出",
    "structured_changes": {
      "coordinate_kind": "ordinal"
    },
    "required_additional_prerequisites": [],
    "expected_resumes": [],
    "still_blocked": [
      "index_base",
      "reference_origin",
      "counting_boundary",
      "input_value"
    ],
    "adapter_status": "需要新增输入目标/计数坐标适配；现有semantic_output只地址化操作输出"
  },
  {
    "id": "P02.D2",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "set_quantity_semantics",
    "target_description": "同一输入出现处",
    "structured_changes": {
      "coordinate_kind": "ordinal",
      "index_base": 1,
      "counting_boundary": "start_of_current_year",
      "reference_origin": "current_bu_start",
      "step_unit": "year",
      "evidence_ids": [
        "S-C46"
      ]
    },
    "required_additional_prerequisites": [
      "D1未被互斥决定覆盖或以完整修订替换"
    ],
    "expected_resumes": [
      "将源文减一表达解释为至本年年首的经过年数",
      "重检下游乘除的输入相容性"
    ],
    "still_blocked": [
      "缺少235/19模型时不能继续授权月转换",
      "缺输入数值时仍不能执行"
    ],
    "adapter_status": "本包是DecisionIntent规格；禁止把这组字段直接交给现有API后宣称已应用"
  }
]
```


### 负例

```json
[
  "置甲量減一只生成减法，不把量赋year。",
  "0基索引−1仍为另一个位置，不自动当经过年数。",
  "一基月份序位−1得到经过月数，不能沿用year结果。"
]
```


### 参考算术

```json
{
  "synthetic_inputs": [
    1,
    2,
    63
  ],
  "expected_completed_years": [
    0,
    1,
    62
  ]
}
```


数值为条件化算术检查，不是新parser输出。

engine_observed_result: null

## P03 — 入蔀積月：递归组合与实例绑定

source_class: attested_excerpt_with_synthetic_context

### 原文与reading

```json
[
  {
    "doc_id": "P03.text",
    "reading_id": "P03.text.reading1",
    "text": "入蔀積月",
    "source_sha256": "e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d",
    "basis_ids": [
      "S-C47"
    ],
    "source_note": "Attested micro-excerpt; coordinates are local to this exact excerpt, not offsets into full book."
  }
]
```


### 禁用整词捷径

```json
[
  "入蔀積月",
  "積月"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P03.ru | {"doc_id":"P03.text","end":1,"quote":"入","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":0} | ["cue",null,"LC12"] | [] | {"concept_id":"relation.entry","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P03.bu | {"doc_id":"P03.text","end":2,"quote":"蔀","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":1} | ["cue",null,"LC14"] | [] | {"concept_id":"scope.bu","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P03.ji | {"doc_id":"P03.text","end":3,"quote":"積","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":2} | ["cue",null,"LC06"] | [] | {"concept_id":"compute.accumulation","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P03.yue | {"doc_id":"P03.text","end":4,"quote":"月","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":3} | ["cue",null,"LC02"] | [] | {"concept_id":"time.month","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P03.acc | {"doc_id":"P03.text","end":4,"quote":"積月","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":2} | ["composition","C01",null] | ["P03.ji","P03.yue"] | {"arguments":{"quantity":{"concept_id":"time.month","op":"concept"}},"op":"accumulation"} | ["proposed","unchecked","not_authorized"] |
| P03.local | {"doc_id":"P03.text","end":4,"quote":"入蔀積月","reading_id":"P03.text.reading1","source_sha256":"e1b7916e4835b6b0573d492cc128b7b0f1ff7904dc47ae43ccf3bff0ad1aa76d","start":0} | ["composition","C06",null] | ["P03.ru","P03.bu","P03.acc"] | {"arguments":{"quantity":{"arguments":{"quantity":{"concept_id":"time.month","op":"concept"}},"op":"accumulation"},"scope":{"concept_id":"scope.bu","op":"concept"}},"op":"localized_quantity"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P03.acc",
    "child_id": "P03.ji",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P03.acc",
    "child_id": "P03.yue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P03.local",
    "child_id": "P03.ru",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P03.local",
    "child_id": "P03.bu",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P03.local",
    "child_id": "P03.acc",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 2
  }
]
```


### 预期与边界

```json
[
  "先以C01产生積月子项，再以C06组合；需显示两层推导。",
  "把前术積月视为本处quantity的候选producer；绝不通过全局alias直接绑定。",
  "两个producer为人工构造的歧义情景；并非说原文实际有两个同名输出。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[
  {
    "id": "P03.D1",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "bind_value",
    "target_description": "下一术入蔀積月的formal输入",
    "structured_changes": {
      "producer": "SF.46.quotient",
      "output_port": "quotient",
      "binding_scope": "same_bu_and_year",
      "synthetic_competing_producer": "another_invocation.SF.46.quotient"
    },
    "required_additional_prerequisites": [
      "双方的bu、年、历元/边界相容",
      "被选producer已经可用"
    ],
    "expected_resumes": [
      "绑定并沿用已获授权的月数语义",
      "重检27759/940换算的实参"
    ],
    "still_blocked": [
      "任一新参数、模型或起算日缺失仍单独停下"
    ],
    "adapter_status": "复用现有bind_value框架；实际payload必须填两个definition_anchor和formal，不能使用此示例字符串地址"
  }
]
```


### 负例

```json
[
  "同名而不同query/year的两个量不得合并。",
  "撤销绑定后后代依赖待重验，原文叶节点保留。",
  "入紀日为另一个synthetic变体；可产生候选，不宣称历史见例。",
  "交换同一父项的child_ids顺序，必须拒绝；保持有序children时任意重排顶层节点集合不改变合法结构。",
  "has_part导出边的component_index从父项child_ids派生；每个父项从0计数，不能存成子项全局序号。"
]
```


### 参考算术

```json
{}
```


绑定后是否执行取决于下一术其余前提，不能只按同名或同单位放行。

engine_observed_result: null

## P04 — 蔀日/蔀月：率、商余与分母

source_class: attested_excerpt

### 原文与reading

```json
[
  {
    "doc_id": "P04.text",
    "reading_id": "P04.text.reading1",
    "text": "置入蔀積月，以蔀日乘之，滿蔀月得一，名為積日，不滿為小餘",
    "source_sha256": "42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe",
    "basis_ids": [
      "S-C47"
    ],
    "source_note": "Attested micro-excerpt; coordinates are local to this exact excerpt, not offsets into full book."
  }
]
```


### 禁用整词捷径

```json
[
  "蔀日",
  "蔀月"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P04.days.scope | {"doc_id":"P04.text","end":8,"quote":"蔀","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":7} | ["cue",null,"LC14"] | [] | {"concept_id":"scope.bu","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P04.days.quantity | {"doc_id":"P04.text","end":9,"quote":"日","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":8} | ["cue",null,"LC01"] | [] | {"concept_id":"time.day","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P04.days | {"doc_id":"P04.text","end":9,"quote":"蔀日","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":7} | ["composition","C07",null] | ["P04.days.scope","P04.days.quantity"] | {"arguments":{"quantity":{"concept_id":"time.day","op":"concept"},"scope":{"concept_id":"scope.bu","op":"concept"}},"op":"scoped_quantity"} | ["proposed","unchecked","not_authorized"] |
| P04.months.scope | {"doc_id":"P04.text","end":14,"quote":"蔀","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":13} | ["cue",null,"LC14"] | [] | {"concept_id":"scope.bu","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P04.months.quantity | {"doc_id":"P04.text","end":15,"quote":"月","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":14} | ["cue",null,"LC02"] | [] | {"concept_id":"time.month","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P04.months | {"doc_id":"P04.text","end":15,"quote":"蔀月","reading_id":"P04.text.reading1","source_sha256":"42757144ae7e0184df2416f8810e68963a36dbe74e52b7ed37ab8eb0422a24fe","start":13} | ["composition","C07",null] | ["P04.months.scope","P04.months.quantity"] | {"arguments":{"quantity":{"concept_id":"time.month","op":"concept"},"scope":{"concept_id":"scope.bu","op":"concept"}},"op":"scoped_quantity"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P04.days",
    "child_id": "P04.days.scope",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P04.days",
    "child_id": "P04.days.quantity",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P04.months",
    "child_id": "P04.months.scope",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P04.months",
    "child_id": "P04.months.quantity",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  }
]
```


### 预期与边界

```json
[
  "两条数字声明本身不提供月→日证明；输入kind、共同scope及转换关系必须明确。",
  "原始余数r=348；其表示量是348/940日；不能把348直接当348日，也不能丢弃分母。",
  "除法节点有quotient/remainder两个兄弟端口；随后混合分数引用q、r及d。",
  "允许日数子图执行；未解决日名的部分保持未决。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[
  {
    "id": "P04.D1",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "select_profile",
    "target_description": "局部月→日转换模型",
    "structured_changes": {
      "selected_fact": "F-SF-MD"
    },
    "required_additional_prerequisites": [
      "input已经绑定并有lunation_count解释",
      "蔀日27759和蔀月940来自选定reading",
      "参数属于同一model scope"
    ],
    "expected_resumes": [
      "授权月数乘27759/940的目标日量",
      "分别保留商端口和余数端口",
      "将r与分母940关联为日分表示"
    ],
    "still_blocked": [
      "求日名仍需要蔀首日和计数约定"
    ],
    "adapter_status": "拟将ScopedFact转为有范围的profile；当前仓库未注册F-SF-MD这个ID"
  }
]
```


### 负例

```json
[
  "去掉conversion_model只保留27759与940：可核算裸整数商余，禁止标注已授权日量。",
  "把输入换成日数：模型输入不相容，不能套月→日。",
  "换到三统scope同名参数也不自动生效。",
  "derived_from仅用于解释来源；增加该边不能绑定计算输入、producer或商余端口。"
]
```


### 参考算术

```json
{
  "case_Cullen_year2": {
    "month_count": 12,
    "numerator_factor": 27759,
    "divisor": 940,
    "expected_quotient": 354,
    "expected_remainder": 348,
    "cycle_divisor": 60,
    "expected_cycle_remainder": 54
  },
  "case_Liu_year63": {
    "month_count": 766,
    "numerator_factor": 27759,
    "divisor": 940,
    "expected_quotient": 22620,
    "expected_remainder": 594,
    "cycle_divisor": 60,
    "expected_cycle_remainder": 0
  }
}
```


原文摘录到小余为止；循环余数为同节后续步骤的数值对照，不宣称摘录独立包含全文。

engine_observed_result: null

## P05 — 日率/月率：词法压力与多义保留

source_class: synthetic_stress_test

### 原文与reading

```json
[
  {
    "doc_id": "P05.text",
    "reading_id": "P05.text.reading1",
    "text": "以日率乘月率",
    "source_sha256": "f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a",
    "basis_ids": [
      "S-ENG"
    ],
    "source_note": "Synthetic stress string; 日率 attested in S-C79; 月率 meaning not attested in this round."
  }
]
```


### 禁用整词捷径

```json
[
  "日率",
  "月率"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P05.sun.base | {"doc_id":"P05.text","end":2,"quote":"日","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":1} | ["cue",null,"LC01"] | [] | {"concept_id":"body.sun","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.sun.ratecue | {"doc_id":"P05.text","end":3,"quote":"率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":2} | ["cue",null,"LC09"] | [] | {"concept_id":"compute.rate","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.sun.rate | {"doc_id":"P05.text","end":3,"quote":"日率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":1} | ["composition","C04",null] | ["P05.sun.base","P05.sun.ratecue"] | {"arguments":{"associate":{"concept_id":"body.sun","op":"concept"}},"op":"rate_for"} | ["proposed","unchecked","not_authorized"] |
| P05.day.base | {"doc_id":"P05.text","end":2,"quote":"日","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":1} | ["cue",null,"LC01"] | [] | {"concept_id":"time.day","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.day.ratecue | {"doc_id":"P05.text","end":3,"quote":"率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":2} | ["cue",null,"LC09"] | [] | {"concept_id":"compute.rate","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.day.rate | {"doc_id":"P05.text","end":3,"quote":"日率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":1} | ["composition","C04",null] | ["P05.day.base","P05.day.ratecue"] | {"arguments":{"associate":{"concept_id":"time.day","op":"concept"}},"op":"rate_for"} | ["proposed","unchecked","not_authorized"] |
| P05.moon.base | {"doc_id":"P05.text","end":5,"quote":"月","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":4} | ["cue",null,"LC02"] | [] | {"concept_id":"body.moon","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.moon.ratecue | {"doc_id":"P05.text","end":6,"quote":"率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":5} | ["cue",null,"LC09"] | [] | {"concept_id":"compute.rate","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.moon.rate | {"doc_id":"P05.text","end":6,"quote":"月率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":4} | ["composition","C04",null] | ["P05.moon.base","P05.moon.ratecue"] | {"arguments":{"associate":{"concept_id":"body.moon","op":"concept"}},"op":"rate_for"} | ["proposed","unchecked","not_authorized"] |
| P05.month.base | {"doc_id":"P05.text","end":5,"quote":"月","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":4} | ["cue",null,"LC02"] | [] | {"concept_id":"time.month","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.month.ratecue | {"doc_id":"P05.text","end":6,"quote":"率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":5} | ["cue",null,"LC09"] | [] | {"concept_id":"compute.rate","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P05.month.rate | {"doc_id":"P05.text","end":6,"quote":"月率","reading_id":"P05.text.reading1","source_sha256":"f0419799a2c5aa5bbe2f7a240f3405b877bd5a2f805f50f6d1b7ae45cba41d0a","start":4} | ["composition","C04",null] | ["P05.month.base","P05.month.ratecue"] | {"arguments":{"associate":{"concept_id":"time.month","op":"concept"}},"op":"rate_for"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P05.sun.rate",
    "child_id": "P05.sun.base",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P05.sun.rate",
    "child_id": "P05.sun.ratecue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P05.day.rate",
    "child_id": "P05.day.base",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P05.day.rate",
    "child_id": "P05.day.ratecue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P05.moon.rate",
    "child_id": "P05.moon.base",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P05.moon.rate",
    "child_id": "P05.moon.ratecue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  },
  {
    "parent_id": "P05.month.rate",
    "child_id": "P05.month.base",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P05.month.rate",
    "child_id": "P05.month.ratecue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  }
]
```


### 预期与边界

```json
[
  "保留日率和月率完整可选Term跨度，同时保留各词素；BOUNDARY不能先截断可组合量。",
  "日可关联sun或day；月可关联moon或month；率不是每单位时间的同义标签。",
  "以A乘B能够得到两个引用槽，未定词义保持可见；不得从multiply本身发明量纲。",
  "真实日率在S-C79中是Solar Rate；本例验证它不会被day-only词典排除。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[
  {
    "id": "P05.D1",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "select_candidate",
    "target_description": "日率出现处的领域候选",
    "structured_changes": {
      "selected_expression": {
        "op": "rate_for",
        "arguments": {
          "associate": {
            "op": "concept",
            "concept_id": "body.sun"
          }
        }
      },
      "support": "S-C79"
    },
    "required_additional_prerequisites": [
      "当前文本scope确认为四分历五星相关",
      "S-C79解释显式选用"
    ],
    "expected_resumes": [
      "确定本处日关联太阳的解释",
      "在相应ratio模型下可进一步解释为solar-cycle count"
    ],
    "still_blocked": [
      "月率仍无对应历史定义",
      "两个操作量的具体数值及计算关系未齐备"
    ],
    "adapter_status": "需term candidate路由；现有select_candidate只消费构式候选"
  }
]
```


### 负例

```json
[
  "无S-C79或对应选用解释时，sun/day两条候选都保留。",
  "不登记月率完整词义。",
  "声称rate=day^-1直接失败。",
  "若候选数量被截断必须报truncated，不把第一条当唯一答案。",
  "supported / underdetermined / not_authorized是合法多轴状态；不能折成authorized或一个进度百分比。"
]
```


### 参考算术

```json
{}
```


预期在缺少月率定义与数值处停下；完整候选结构就是本probe的成功条件。

engine_observed_result: null

## P06 — 中法/日法：reading、scope与表示尺度

source_class: multiple_readings

### 原文与reading

```json
[
  {
    "doc_id": "P06.repo",
    "reading_id": "P06.repo.reading1",
    "text": "中法，四十二",
    "source_sha256": "2635b5f4ed83494f79d5f31ec273bfa46c97bd1f55278d305da0cf673f5521d9",
    "basis_ids": [
      "S-REPO"
    ],
    "source_note": "Repo transcription; preserve 42."
  },
  {
    "doc_id": "P06.edited",
    "reading_id": "P06.edited.reading1",
    "text": "中法，三十二",
    "source_sha256": "25bb62709edec46ebe6b105535db8bf4c461e99603a2e829c3e590be2f648927",
    "basis_ids": [
      "S-CCONST"
    ],
    "source_note": "Selected edited reading represented as a separate micro-document; Cullen displays the emendation in apparatus."
  },
  {
    "doc_id": "P06.fa",
    "reading_id": "P06.fa.reading1",
    "text": "日法",
    "source_sha256": "aa376916b78a513a8c537654c09b8ef778aa6a195301368592076e35a2459978",
    "basis_ids": [
      "S-C23",
      "S-CCONST"
    ],
    "source_note": "Same form tested under two declared traditions; no global numeric default."
  }
]
```


### 禁用整词捷径

```json
[
  "中法",
  "日法"
]
```


### 有序候选树（人工预期）

| ID | 跨度 | method / rule / cue | 直接child_ids | 表达 | 支持／约束／授权 |
| --- | --- | --- | --- | --- | --- |
| P06.zhong | {"doc_id":"P06.repo","end":1,"quote":"中","reading_id":"P06.repo.reading1","source_sha256":"2635b5f4ed83494f79d5f31ec273bfa46c97bd1f55278d305da0cf673f5521d9","start":0} | ["opaque_component",null,null] | [] | {"op":"unknown","sort":"semantic_expression","source_text":"中"} | ["proposed","unchecked","not_authorized"] |
| P06.fa-cue | {"doc_id":"P06.repo","end":2,"quote":"法","reading_id":"P06.repo.reading1","source_sha256":"2635b5f4ed83494f79d5f31ec273bfa46c97bd1f55278d305da0cf673f5521d9","start":1} | ["cue",null,"LC08"] | [] | {"concept_id":"compute.factor","op":"concept"} | ["proposed","unchecked","not_authorized"] |
| P06.zhongfa | {"doc_id":"P06.repo","end":2,"quote":"中法","reading_id":"P06.repo.reading1","source_sha256":"2635b5f4ed83494f79d5f31ec273bfa46c97bd1f55278d305da0cf673f5521d9","start":0} | ["composition","C03",null] | ["P06.zhong","P06.fa-cue"] | {"arguments":{"associate":{"op":"unknown","sort":"semantic_expression","source_text":"中"}},"op":"factor_for"} | ["proposed","unchecked","not_authorized"] |


边序号是父项局部派生值：

```json
[
  {
    "parent_id": "P06.zhongfa",
    "child_id": "P06.zhong",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 0
  },
  {
    "parent_id": "P06.zhongfa",
    "child_id": "P06.fa-cue",
    "relation": "has_part",
    "layer": "term_composition",
    "component_index": 1
  }
]
```


### 预期与边界

```json
[
  "X法可生成参数候选，即使X=中的具体义项未定；不能从中自动判定medial_count单位。",
  "底本42和校读32分别存储；无选择时标明reading冲突。",
  "三统日法81与四分日法4均为scoped事实；同字形不共享数值。",
  "168/32=21/4是年余日，不能无证明当365又1/4日。"
]
```


### 后续人工步骤（K1不提交为真实决定）

```json
[
  {
    "id": "P06.D1",
    "record_kind": "illustrative_decision_not_recorded",
    "intent_action": "proposed.select_reading",
    "target_description": "中法数值声明",
    "structured_changes": {
      "selected_reading_id": "P06.edited.reading1",
      "retain_other_reading_id": "P06.repo.reading1",
      "value": 32
    },
    "required_additional_prerequisites": [
      "Cullen校读作为本次明确选择",
      "来源定位与新阅读版本建立"
    ],
    "expected_resumes": [
      "重新解析此声明并绑定32",
      "使引用原42的约束与数值结果待重验"
    ],
    "still_blocked": [
      "日餘/月餘是另一个reading问题，不能自动一并改",
      "day尺度/余日模型需另有授权"
    ],
    "adapter_status": "待加reading选择适配；当前本包不重写repo"
  }
]
```


### 负例

```json
[
  "无reading决定，不能悄悄消费32。",
  "只选择32不可暗改月餘为日餘。",
  "四分profile套三统时gate返回incompatible或underdetermined而非成功。"
]
```


### 参考算术

```json
{
  "selected_32": {
    "numerator": 168,
    "denominator": 32,
    "expected_fraction": "21/4"
  },
  "preserved_42": {
    "numerator": 168,
    "denominator": 42,
    "expected_fraction": "4"
  },
  "same_form_scoped_values": {
    "Han_Si_fen_li": 4,
    "San_tong_li": 81
  }
}
```


本probe不要求生成完整二十四气图；隔离验证reading和参数适用性。

engine_observed_result: null
