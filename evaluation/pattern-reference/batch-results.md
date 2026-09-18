# Deterministic Pattern Lab reference import — frozen parser batch

Actor: deterministic Python software evaluation。没有新人工判断；没有修改 parser 或固定 crosswalk。

完整导入：25 chunks / 457 terms / 89 relations。
Proc.3.5 原局部 packet：7/7。

批量输入是独立于 annotation 的 canonical 四分历全部编号章节；先编译，再读取 annotation。与局部 packet 的输入范围不同，结果分别报告。

| Chunk | 原始步数 | 可转换步骤 | 匹配 | 结果分布 |
|---|---|---|---|---|
| cullen:ch3:chunk:0026 | 13 | 1 | 0 | {"missing_machine_semantics": 1, "reference_not_convertible": 12} |
| cullen:ch3:chunk:0055 | 7 | 7 | 7 | {"match": 7} |
| cullen:ch3:chunk:0056 | 15 | 7 | 0 | {"dependency_unavailable": 6, "mismatch": 1, "reference_not_convertible": 8} |

## 导入状态（不算 parser false negative）

```json
{
  "lexical_reference_statuses": {
    "needs_review": 41,
    "resolved": 416
  },
  "relation_target_statuses": {
    "not_current_parser_target": 89
  },
  "import_issues": {
    "crosswalk_missing": 12,
    "manual_schema_unparsed": 2,
    "needs_review": 10
  },
  "crosswalk_missing_operations": [
    "add",
    "count",
    "distribute",
    "divide",
    "remove_modulus",
    "seek"
  ]
}
```

所有 relations 单独保留为 not_current_parser_target。词项/参数/数量单独生成 lexical/semantic reference。
reference_not_convertible、dependency_unavailable 不得与已可评估步骤的机器缺失混算。匹配不代表历史真值、单位/尺度验证或 graph closure。

## 每步结果

| Chunk / step | 原 phrase | 原 operation | 状态 | 导入问题／细节 |
|---|---|---|---|---|
| cullen:ch3:chunk:0026 / step-1 | 置十二中以定月位 | set | missing_machine_semantics |  |
| cullen:ch3:chunk:0026 / step-2 | 有朔而無中者為閏月 | judge | reference_not_convertible | needs_review; needs_review: non-scalar operand unsupported by registered crosswalk |
| cullen:ch3:chunk:0026 / step-3 | 中之始(日) [曰]節 | name_result | reference_not_convertible | manual_schema_unparsed; needs_review; input: manual_schema_unparsed: unsupported expression |
| cullen:ch3:chunk:0026 / step-4 | 與中為二十四氣 | name_result | reference_not_convertible | needs_review; needs_review: non-scalar operand unsupported by registered crosswalk |
| cullen:ch3:chunk:0026 / step-5 | 以除一歲日， 為一氣之日數也 | divide | reference_not_convertible | crosswalk_missing; needs_review |
| cullen:ch3:chunk:0026 / step-6 | 其分 | name_remainder | reference_not_convertible | needs_review; needs_review: roles outside registered crosswalk |
| cullen:ch3:chunk:0026 / step-7 | 其分積而成日 | add | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0026 / step-8 | 為 沒 | name_result | reference_not_convertible | needs_review |
| cullen:ch3:chunk:0026 / step-9 | 并歲氣之分 | add | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0026 / step-10 | 如法為一歲沒 | fill_divide | reference_not_convertible | needs_review; needs_review: unspecified quotient/remainder output |
| cullen:ch3:chunk:0026 / step-11 | 沒分于終中 | distribute | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0026 / step-12 | 冬至之分積如其 法得一日 | fill_divide | reference_not_convertible | needs_review; needs_review: unspecified quotient/remainder output |
| cullen:ch3:chunk:0026 / step-13 | 四歲而終 | count | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0055 / step-1 | 置入蔀年 | set | match |  |
| cullen:ch3:chunk:0055 / step-2 | 減一 | subtract | match |  |
| cullen:ch3:chunk:0055 / step-3 | 以章月乘之 | multiply | match |  |
| cullen:ch3:chunk:0055 / step-4 | 滿章法得一 | fill_divide | match |  |
| cullen:ch3:chunk:0055 / step-5 | 名為積月 | name_result | match |  |
| cullen:ch3:chunk:0055 / step-6 | 不滿為閏餘 | name_remainder | match |  |
| cullen:ch3:chunk:0055 / step-7 | 十二以上, 其歲有閏 | judge | match |  |
| cullen:ch3:chunk:0056 / step-1 | 置入蔀積月 | set | mismatch |  |
| cullen:ch3:chunk:0056 / step-2 | 以蔀日乘之 | multiply | dependency_unavailable | out1 |
| cullen:ch3:chunk:0056 / step-3 | 滿蔀月得一 | fill_divide | reference_not_convertible | needs_review |
| cullen:ch3:chunk:0056 / step-4 | 名為積日 | name_result | dependency_unavailable | quot3 |
| cullen:ch3:chunk:0056 / step-5 | 不滿為小餘 | name_remainder | dependency_unavailable | rem3 |
| cullen:ch3:chunk:0056 / step-6 | 積日以六十 除去之 | remove_modulus | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0056 / step-7 | 其餘為大餘 | name_remainder | dependency_unavailable | rem6 |
| cullen:ch3:chunk:0056 / step-8 | 以所入蔀名命之， 筭盡之外， 則前年天正十一月朔日 也 | count | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0056 / step-9 | 小餘四百四十一以上， 其月大 | judge | dependency_unavailable | 小餘 |
| cullen:ch3:chunk:0056 / step-10 | 求後月朔 | seek | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0056 / step-11 | 加大餘二十九 | add | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0056 / step-12 | 小餘四百九十 [九] | add | reference_not_convertible | crosswalk_missing; manual_schema_unparsed; needs_review; parameter: manual_schema_unparsed: unsupported expression |
| cullen:ch3:chunk:0056 / step-13 | 小餘滿蔀月得一 | fill_divide | dependency_unavailable | out12 |
| cullen:ch3:chunk:0056 / step-14 | 上加大餘 | add | reference_not_convertible | crosswalk_missing |
| cullen:ch3:chunk:0056 / step-15 | 命之如前 | count | reference_not_convertible | crosswalk_missing |

复现：`python -X utf8 -m evaluation.pattern_reference --output .cache/pattern-reference-run`。
完整原始对象、exact anchors、小语法 AST、每步 checks、未决诊断及 SHA manifest 均在该输出目录；重复运行按文件逐字节比较。
