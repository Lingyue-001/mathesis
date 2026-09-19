> K1 已实现可选 suggestion-only 候选；下面的 review2 定义仍保留原设计身份。人工裁决、统一授权、计数坐标、reading 选择与恢复尚未接入。既有 parser 硬编码未在本阶段清理。

# Schema Reference — 0.1.0-review2

由kernel.registry.json、kernel.schema.json及paper-probes.json确定性生成。这是设计说明；运行时能力状态以Codex实施后的consumer manifest和效应测试为准。


## 1. 候选状态与关系投影

构词的直接子项读取child_ids，语义参数读取expression.arguments；两个结构都保留。支持、约束、授权三轴分别显示；OSCA只表示处理活动。

```json
{
  "composition_children": {
    "source_field": "child_ids",
    "order": "source_reading_order",
    "index_base": 0,
    "edge_relation": "has_part",
    "derived_edge_index": "component_index",
    "preserve_cue_leaves": true,
    "id_array_order_affects_identity": true
  },
  "epistemic_derivation": {
    "relation": "derived_from",
    "layer": "provenance",
    "source_fields": [
      "provenance_ids",
      "rule_id",
      "cue_id",
      "child_ids",
      "premise_ids",
      "evidence_ids",
      "generated_by"
    ],
    "runtime_port_authority": false
  },
  "computational": {
    "layer": "dataflow",
    "native_reads": "reads",
    "native_writes": "writes",
    "value_producer": "producer",
    "value_port": "output_port",
    "writes_display_relation": "produces",
    "forbid_provenance_as_ports": true,
    "update_policy": "recorded_operations_only"
  },
  "semantic_scope": {
    "relation": "localized_in",
    "label_zh": "历法语义范围",
    "label_en": "Semantic scope",
    "source_location_fields": [
      "span",
      "source_spans"
    ],
    "concept_is_instance": false,
    "relation_aliases": []
  },
  "candidate_status": {
    "axes": [
      "support_status",
      "constraint_status",
      "authorization_status"
    ],
    "shared_definition": "#/$defs/StatusAxes",
    "ordering": "independent_axes",
    "reject_legacy_single_axis": true,
    "execution_requires_separate_gate": true
  }
}
```


### 共享状态字段

```json
{
  "type": "object",
  "description": "Independent evidence, constraint and authorization axes; not a lifecycle. Authorization validity is facet- and branch-scoped.",
  "properties": {
    "support_status": {
      "enum": [
        "proposed",
        "supported"
      ]
    },
    "constraint_status": {
      "enum": [
        "unchecked",
        "compatible",
        "incompatible",
        "underdetermined",
        "conflicted"
      ]
    },
    "authorization_status": {
      "enum": [
        "not_authorized",
        "authorized",
        "stale",
        "rejected"
      ]
    },
    "authorization_refs": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "support_status",
    "constraint_status",
    "authorization_status",
    "authorization_refs"
  ],
  "allOf": [
    {
      "if": {
        "properties": {
          "authorization_status": {
            "const": "authorized"
          }
        }
      },
      "then": {
        "properties": {
          "authorization_refs": {
            "minItems": 1
          },
          "constraint_status": {
            "const": "compatible"
          }
        }
      }
    }
  ]
}
```


## 2. 类型字段

### Registry

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| schema_version | required | composite | {"const":"0.1.0-review2"} |
| artifact_kind | required | composite | {"const":"design_registry_not_runtime"} |
| baseline_commit | required | string | {} |
| sources | required | array | {"minItems":1} |
| concepts | required | array | {"minItems":1} |
| lexical_cues | required | array | {"minItems":1} |
| constructors | required | array | {"minItems":1} |
| composition_rules | required | array | {"minItems":1} |
| fixed_expressions | required | array | {"minItems":0} |
| scoped_facts | required | array | {"minItems":0} |
| human_actions | required | array | {"minItems":1} |
| relations | required | array | {"minItems":1} |
| phases | required | object | {} |
| phase_note | required | string | {} |
| required_external_checks | required | array | {} |
| status | required | composite | {"const":"reviewable_specification_engine_not_implemented"} |
| predicate_contracts | required | array | {"minItems":1} |
| authority_rules | required | array | {"minItems":1} |
| projection_contracts | required | #/$defs/ProjectionContracts | {} |


additionalProperties = false

### ProbeSuite

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| schema_version | required | composite | {"const":"0.1.0-review2"} |
| artifact_kind | required | composite | {"const":"paper_probe_expectations"} |
| probe_status | required | composite | {"const":"authored_not_engine_test_results"} |
| probes | required | array | {"minItems":6} |


additionalProperties = false

### Expression

```json
{
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "concept"
        },
        "concept_id": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "op",
        "concept_id"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "unknown"
        },
        "source_text": {
          "type": "string",
          "minLength": 1
        },
        "sort": {
          "enum": [
            "semantic_expression",
            "quantity_expression",
            "scope_expression"
          ]
        }
      },
      "required": [
        "op",
        "source_text",
        "sort"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "accumulation"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "quantity": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "quantity"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "residual_of"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "associate": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "associate"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "factor_for"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "associate": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "associate"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "rate_for"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "associate": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "associate"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "part_of_quantity"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "associate": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "associate"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "localized_quantity"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "scope": {
              "$ref": "#/$defs/Expression"
            },
            "quantity": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "scope",
            "quantity"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "scoped_quantity"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "scope": {
              "$ref": "#/$defs/Expression"
            },
            "quantity": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "scope",
            "quantity"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "op": {
          "const": "number_of"
        },
        "arguments": {
          "type": "object",
          "properties": {
            "associate": {
              "$ref": "#/$defs/Expression"
            }
          },
          "required": [
            "associate"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "op",
        "arguments"
      ],
      "additionalProperties": false
    }
  ]
}
```


### SourceAnchor

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| doc_id | required | string | {} |
| reading_id | required | string | {} |
| source_sha256 | required | string | {} |
| start | required | integer | {"minimum":0} |
| end | required | integer | {"minimum":1} |
| quote | required | string | {} |


additionalProperties = false

### SemanticTarget

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| kind | required | enum | {"enum":["term_occurrence","quantity_input","quantity_output","binding","reading"]} |
| source_anchor | required | #/$defs/SourceAnchor | {} |
| branch_id | required | string | {} |
| definition_ref | required | ["string","null"] | {} |
| construction_ref | required | ["string","null"] | {} |
| output_port | required | ["string","null"] | {} |
| invocation_path | required | array | {} |


条件约束：

```json
[
  {
    "if": {
      "properties": {
        "kind": {
          "const": "quantity_output"
        }
      }
    },
    "then": {
      "properties": {
        "definition_ref": {
          "type": "string",
          "minLength": 1
        },
        "construction_ref": {
          "type": "string",
          "minLength": 1
        },
        "output_port": {
          "type": "string",
          "minLength": 1
        }
      }
    }
  }
]
```


additionalProperties = false

### FacetAssertion

```json
{
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "term_expression"
        },
        "value": {
          "$ref": "#/$defs/Expression"
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "coordinate_kind"
        },
        "value": {
          "enum": [
            "ordinal",
            "elapsed_count",
            "duration",
            "cycle_residue",
            "unknown"
          ]
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "index_base"
        },
        "value": {
          "type": "integer"
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "counting_boundary"
        },
        "value": {
          "enum": [
            "start_of_current_year",
            "end_of_current_year",
            "unresolved"
          ]
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "reference_origin"
        },
        "value": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "step_unit"
        },
        "value": {
          "enum": [
            "year",
            "month",
            "day",
            "du",
            "unresolved"
          ]
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "selected_reading"
        },
        "value": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "producer_binding"
        },
        "value": {
          "type": "object",
          "properties": {
            "producer_ref": {
              "type": "string",
              "minLength": 1
            },
            "output_port": {
              "type": "string",
              "minLength": 1
            }
          },
          "required": [
            "producer_ref",
            "output_port"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    },
    {
      "type": "object",
      "properties": {
        "facet": {
          "const": "representation"
        },
        "value": {
          "type": "object",
          "properties": {
            "kind": {
              "enum": [
                "whole",
                "fraction_numerator",
                "fraction"
              ]
            },
            "denominator_ref": {
              "type": [
                "string",
                "null"
              ]
            },
            "base_unit": {
              "type": "string",
              "minLength": 1
            }
          },
          "required": [
            "kind",
            "denominator_ref",
            "base_unit"
          ],
          "additionalProperties": false,
          "allOf": [
            {
              "if": {
                "properties": {
                  "kind": {
                    "enum": [
                      "fraction",
                      "fraction_numerator"
                    ]
                  }
                }
              },
              "then": {
                "properties": {
                  "denominator_ref": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            }
          ]
        }
      },
      "required": [
        "facet",
        "value"
      ],
      "additionalProperties": false
    }
  ]
}
```


### SemanticClaim

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| id | required | string | {} |
| target | required | #/$defs/SemanticTarget | {} |
| assertion | required | #/$defs/FacetAssertion | {} |
| premise_ids | required | array | {} |
| evidence_ids | required | array | {} |
| generated_by | required | string | {} |
| support_status | required | #/$defs/StatusAxes/properties/support_status | {} |
| constraint_status | required | #/$defs/StatusAxes/properties/constraint_status | {} |
| authorization_status | required | #/$defs/StatusAxes/properties/authorization_status | {} |
| authorization_refs | required | #/$defs/StatusAxes/properties/authorization_refs | {} |


条件约束：

```json
[
  {
    "$ref": "#/$defs/StatusAxes"
  }
]
```


additionalProperties = false

### ReviewTicket

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| id | required | string | {} |
| target | required | #/$defs/SemanticTarget | {} |
| snapshot | required | object | {} |
| question | required | string | {} |
| missing_facets | required | array | {} |
| candidate_claim_ids | required | array | {} |
| allowed_actions | required | array | {} |
| allow_manual_constructor | required | boolean | {} |
| resume_from | required | string | {} |
| resume_prerequisites | required | array | {} |
| scope_of_block | required | enum | {"enum":["dependent_region_only","whole_export"]} |


additionalProperties = false

### DecisionIntent

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| id | required | string | {} |
| record_kind | required | composite | {"const":"illustrative_not_recorded"} |
| ticket_id | required | string | {} |
| intent_action | required | string | {} |
| target | required | #/$defs/SemanticTarget | {} |
| assertions | required | array | {"minItems":1} |
| evidence_ids | required | array | {"minItems":1} |
| reason | required | string | {} |
| actor | required | composite | {"const":"example_human_not_actual_user"} |
| depends_on | required | array | {} |
| current_backend_payload | required | null | {} |
| adapter_requirement | required | string | {} |


additionalProperties = false

### RuntimeExamples

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| schema_version | required | composite | {"const":"0.1.0-review2"} |
| artifact_kind | required | composite | {"const":"runtime_contract_examples"} |
| status | required | composite | {"const":"proposed_not_implemented"} |
| claims | required | array | {"minItems":0} |
| tickets | required | array | {"minItems":1} |
| decision_intents | required | array | {"minItems":1} |


additionalProperties = false

### StatusAxes

Independent evidence, constraint and authorization axes; not a lifecycle. Authorization validity is facet- and branch-scoped.

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| support_status | required | enum | {"enum":["proposed","supported"]} |
| constraint_status | required | enum | {"enum":["unchecked","compatible","incompatible","underdetermined","conflicted"]} |
| authorization_status | required | enum | {"enum":["not_authorized","authorized","stale","rejected"]} |
| authorization_refs | required | array | {} |


条件约束：

```json
[
  {
    "if": {
      "properties": {
        "authorization_status": {
          "const": "authorized"
        }
      }
    },
    "then": {
      "properties": {
        "authorization_refs": {
          "minItems": 1
        },
        "constraint_status": {
          "const": "compatible"
        }
      }
    }
  }
]
```


### SemanticCandidate

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| id | required | string | {} |
| span | required | #/$defs/SourceAnchor | {} |
| method | required | enum | {"enum":["cue","composition","manual_construction","opaque_component"]} |
| cue_id | required | ["string","null"] | {} |
| rule_id | required | ["string","null"] | {} |
| child_ids | required | array | {"description":"Ordered direct components including cue leaves, in source reading order. The array index is the only stored order; graph component_index is a derived, parent-edge-local value.","uniqueItems":true} |
| expression | required | #/$defs/Expression | {} |
| claim_authority | required | enum | {"description":"Maximum allowed effect on canonical semantics; S is suggestion-only and does not authorize anything.","enum":["S","C","A"]} |
| provenance_ids | required | array | {} |
| support_status | required | #/$defs/StatusAxes/properties/support_status | {} |
| constraint_status | required | #/$defs/StatusAxes/properties/constraint_status | {} |
| authorization_status | required | #/$defs/StatusAxes/properties/authorization_status | {} |
| authorization_refs | required | #/$defs/StatusAxes/properties/authorization_refs | {} |
| analysis_range | optional | array | {"maxItems":2,"minItems":2} |
| region_ids | optional | array | {"uniqueItems":true} |
| generated_by | optional | string | {} |
| precondition_checks | optional | object | {} |


条件约束：

```json
[
  {
    "if": {
      "properties": {
        "method": {
          "const": "cue"
        }
      }
    },
    "then": {
      "properties": {
        "cue_id": {
          "type": "string",
          "minLength": 1
        },
        "rule_id": {
          "type": "null"
        },
        "child_ids": {
          "maxItems": 0
        }
      }
    }
  },
  {
    "if": {
      "properties": {
        "method": {
          "const": "composition"
        }
      }
    },
    "then": {
      "properties": {
        "rule_id": {
          "type": "string",
          "minLength": 1
        },
        "cue_id": {
          "type": "null"
        },
        "child_ids": {
          "minItems": 1
        }
      }
    }
  },
  {
    "$ref": "#/$defs/StatusAxes"
  },
  {
    "if": {
      "properties": {
        "authorization_status": {
          "const": "authorized"
        }
      }
    },
    "then": {
      "properties": {
        "claim_authority": {
          "const": "A"
        }
      }
    }
  },
  {
    "if": {
      "properties": {
        "method": {
          "const": "opaque_component"
        }
      }
    },
    "then": {
      "properties": {
        "cue_id": {
          "type": "null"
        },
        "rule_id": {
          "type": "null"
        },
        "child_ids": {
          "maxItems": 0
        },
        "expression": {
          "properties": {
            "op": {
              "const": "unknown"
            }
          }
        }
      }
    }
  }
]
```


additionalProperties = false

### ProjectionContracts

| 字段 | 必需 | 类型／引用 | 限定 |
| --- | --- | --- | --- |
| composition_children | required | composite | {"const":{"derived_edge_index":"component_index","edge_relation":"has_part","id_array_order_affects_identity":true,"index_base":0,"order":"source_reading_order","preserve_cue_leaves":true,"source_field":"child_ids"}} |
| epistemic_derivation | required | composite | {"const":{"layer":"provenance","relation":"derived_from","runtime_port_authority":false,"source_fields":["provenance_ids","rule_id","cue_id","child_ids","premise_ids","evidence_ids","generated_by"]}} |
| computational | required | composite | {"const":{"forbid_provenance_as_ports":true,"layer":"dataflow","native_reads":"reads","native_writes":"writes","update_policy":"recorded_operations_only","value_port":"output_port","value_producer":"producer","writes_display_relation":"produces"}} |
| semantic_scope | required | composite | {"const":{"concept_is_instance":false,"label_en":"Semantic scope","label_zh":"历法语义范围","relation":"localized_in","relation_aliases":[],"source_location_fields":["span","source_spans"]}} |
| candidate_status | required | composite | {"const":{"axes":["support_status","constraint_status","authorization_status"],"execution_requires_separate_gate":true,"ordering":"independent_axes","reject_legacy_single_axis":true,"shared_definition":"#/$defs/StatusAxes"}} |


additionalProperties = false

## 3. 概念层级

| ID | 名称 | family | parents | 定义状态 | 来源 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| body.sun | 太阳 | astral_body | [] | bounded_candidate_vocabulary | ["S-C79"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| body.moon | 月体 | astral_body | [] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.day | 日相关量 | quantity_concept | [] | bounded_candidate_vocabulary | ["S-C47"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.month | 月相关量 | quantity_concept | [] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.lunation | lunation | quantity_concept | ["time.month"] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.civil_month | 民用月 | quantity_concept | ["time.month"] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.year | 年相关量 | quantity_concept | [] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.civil_year | 民用年 | quantity_concept | ["time.year"] | bounded_candidate_vocabulary | ["S-C8"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| time.solar_cycle | 太阳周期 | quantity_concept | ["time.year"] | bounded_candidate_vocabulary | ["S-C8","S-C79"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| measure.du | 度相关量 | quantity_concept | [] | bounded_candidate_vocabulary | ["S-C79"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.accumulation | 累计/汇集结果提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-C46","S-C47"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.residual | 余量提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-C46","S-C47"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.factor | 计算参数提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-C23","S-BK314"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.rate | 率/比值参数提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-C79"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.part | 分/分部表示提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-C23"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| compute.number | 数/数量提示 | computational_cue | [] | bounded_candidate_vocabulary | ["S-REPO"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| relation.entry | 进入/局部定位提示 | relation_cue | [] | bounded_candidate_vocabulary | ["S-C46"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| scope.calendar_cycle | 历算周期类别 | scope_concept | [] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| scope.zhang | 章 | scope_concept | ["scope.calendar_cycle"] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| scope.bu | 蔀 | scope_concept | ["scope.calendar_cycle"] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| scope.ji | 紀 | scope_concept | ["scope.calendar_cycle"] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| scope.yuan | 元周期 | scope_concept | ["scope.calendar_cycle"] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| frame.origin | 起算参照 | frame_concept | [] | bounded_candidate_vocabulary | ["S-CCONST"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| event.conjunction | 日月会合事件 | event_concept | [] | bounded_candidate_vocabulary | ["S-C47"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| event.full_moon | 望事件 | event_concept | [] | bounded_candidate_vocabulary | ["S-REPO"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| event.solstice | 冬至事件 | event_concept | [] | bounded_candidate_vocabulary | ["S-C49"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| event.qi | 气事件 | event_concept | [] | bounded_candidate_vocabulary | ["S-C49"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |
| calendar.intercalation | 置闰 | calendar_concept | [] | bounded_candidate_vocabulary | ["S-C46"] | 概念类别不提供数值、计算单位、起点或producer绑定。 |


## 4. 词形线索

| ID | form | sense_concept_ids | 完整记录 |
| --- | --- | --- | --- |
| LC01 | 日 | ["body.sun","time.day"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C47","S-C79"],"form":"日","id":"LC01","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["body.sun","time.day"]} |
| LC02 | 月 | ["body.moon","time.month","time.lunation","time.civil_month"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C8"],"form":"月","id":"LC02","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["body.moon","time.month","time.lunation","time.civil_month"]} |
| LC03 | 年 | ["time.civil_year","time.year"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C8"],"form":"年","id":"LC03","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["time.civil_year","time.year"]} |
| LC04 | 歲 | ["time.solar_cycle","time.civil_year"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C79","S-C8"],"form":"歲","id":"LC04","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["time.solar_cycle","time.civil_year"]} |
| LC05 | 度 | ["measure.du"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C79"],"form":"度","id":"LC05","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["measure.du"]} |
| LC06 | 積 | ["compute.accumulation"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C46","S-C47"],"form":"積","id":"LC06","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.accumulation"]} |
| LC07 | 餘 | ["compute.residual"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C46","S-C47"],"form":"餘","id":"LC07","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.residual"]} |
| LC08 | 法 | ["compute.factor"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-BK314","S-C23"],"form":"法","id":"LC08","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.factor"]} |
| LC09 | 率 | ["compute.rate"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C79"],"form":"率","id":"LC09","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.rate"]} |
| LC10 | 分 | ["compute.part"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C23"],"form":"分","id":"LC10","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.part"]} |
| LC11 | 數 | ["compute.number"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-REPO"],"form":"數","id":"LC11","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["compute.number"]} |
| LC12 | 入 | ["relation.entry"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C46"],"form":"入","id":"LC12","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["relation.entry"]} |
| LC13 | 章 | ["scope.zhang"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-CCONST"],"form":"章","id":"LC13","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["scope.zhang"]} |
| LC14 | 蔀 | ["scope.bu"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-CCONST"],"form":"蔀","id":"LC14","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["scope.bu"]} |
| LC15 | 紀 | ["scope.ji"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-CCONST"],"form":"紀","id":"LC15","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["scope.ji"]} |
| LC16 | 元 | ["scope.yuan","frame.origin"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-CCONST"],"form":"元","id":"LC16","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["scope.yuan","frame.origin"]} |
| LC17 | 朔 | ["event.conjunction"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C47"],"form":"朔","id":"LC17","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["event.conjunction"]} |
| LC18 | 合朔 | ["event.conjunction"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C47"],"form":"合朔","id":"LC18","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["event.conjunction"]} |
| LC19 | 望 | ["event.full_moon"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-REPO"],"form":"望","id":"LC19","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["event.full_moon"]} |
| LC20 | 冬至 | ["event.solstice"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C49"],"form":"冬至","id":"LC20","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["event.solstice"]} |
| LC21 | 氣 | ["event.qi"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C49"],"form":"氣","id":"LC21","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["event.qi"]} |
| LC22 | 閏 | ["calendar.intercalation"] | {"condition":"必须保留原文跨度和所用reading；这里只列历算语境候选；功能词/动词等其他用法由构式层处理。","effect":"suggest","evidence_ids":["S-C46"],"form":"閏","id":"LC22","lexical_status":"lexical_cue_not_tokenization_command","sense_concept_ids":["calendar.intercalation"]} |


## 5. 语义构造器

| ID | 说明 | 参数sort | result_sort | 关系提示 |
| --- | --- | --- | --- | --- |
| accumulation | 累计某量 | {"quantity":"quantity_expression"} | quantity_expression | associated_with |
| residual_of | 与X关联的余量 | {"associate":"semantic_expression"} | quantity_expression | associated_with |
| factor_for | 与X关联的计算参数 | {"associate":"semantic_expression"} | quantity_expression | associated_with |
| rate_for | 与X关联的率参数 | {"associate":"semantic_expression"} | quantity_expression | associated_with |
| part_of_quantity | 与X关联的分部 | {"associate":"semantic_expression"} | quantity_expression | associated_with |
| localized_quantity | 在某范围内的量 | {"quantity":"quantity_expression","scope":"scope_expression"} | quantity_expression | localized_in |
| scoped_quantity | 与某范围关联的量 | {"quantity":"quantity_expression","scope":"scope_expression"} | quantity_expression | associated_with |
| number_of | 与X关联的数量 | {"associate":"semantic_expression"} | quantity_expression | associated_with |


relation_kind是受分层约束的投影提示，不将expression.arguments冒充构词顺序；所有构词父子边仍由child_ids产生。

## 6. 组合规则

### C01 — 積Q

```json
{
  "id": "C01",
  "label_zh": "積Q",
  "pattern": [
    {
      "kind": "cue",
      "cue_id": "LC06"
    },
    {
      "kind": "variable",
      "name": "Q",
      "sort": "quantity_expression"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "accumulation",
    "arguments_from": {
      "quantity": "$Q"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C02 — X餘

```json
{
  "id": "C02",
  "label_zh": "X餘",
  "pattern": [
    {
      "kind": "variable",
      "name": "X",
      "sort": "semantic_expression"
    },
    {
      "kind": "cue",
      "cue_id": "LC07"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "residual_of",
    "arguments_from": {
      "associate": "$X"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C03 — X法

```json
{
  "id": "C03",
  "label_zh": "X法",
  "pattern": [
    {
      "kind": "variable",
      "name": "X",
      "sort": "semantic_expression"
    },
    {
      "kind": "cue",
      "cue_id": "LC08"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "factor_for",
    "arguments_from": {
      "associate": "$X"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C04 — X率

```json
{
  "id": "C04",
  "label_zh": "X率",
  "pattern": [
    {
      "kind": "variable",
      "name": "X",
      "sort": "semantic_expression"
    },
    {
      "kind": "cue",
      "cue_id": "LC09"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "rate_for",
    "arguments_from": {
      "associate": "$X"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C05 — X分

```json
{
  "id": "C05",
  "label_zh": "X分",
  "pattern": [
    {
      "kind": "variable",
      "name": "X",
      "sort": "semantic_expression"
    },
    {
      "kind": "cue",
      "cue_id": "LC10"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "part_of_quantity",
    "arguments_from": {
      "associate": "$X"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C06 — 入SQ

```json
{
  "id": "C06",
  "label_zh": "入SQ",
  "pattern": [
    {
      "kind": "cue",
      "cue_id": "LC12"
    },
    {
      "kind": "variable",
      "name": "S",
      "sort": "scope_expression"
    },
    {
      "kind": "variable",
      "name": "Q",
      "sort": "quantity_expression"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "localized_quantity",
    "arguments_from": {
      "scope": "$S",
      "quantity": "$Q"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C07 — SQ

```json
{
  "id": "C07",
  "label_zh": "SQ",
  "pattern": [
    {
      "kind": "variable",
      "name": "S",
      "sort": "scope_expression"
    },
    {
      "kind": "variable",
      "name": "Q",
      "sort": "quantity_expression"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "scoped_quantity",
    "arguments_from": {
      "scope": "$S",
      "quantity": "$Q"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


### C09 — X數

```json
{
  "id": "C09",
  "label_zh": "X數",
  "pattern": [
    {
      "kind": "variable",
      "name": "X",
      "sort": "semantic_expression"
    },
    {
      "kind": "cue",
      "cue_id": "LC11"
    }
  ],
  "preconditions": [
    "same_reading",
    "ordered_adjacent_spans",
    "nominal_term_region",
    "typed_arguments"
  ],
  "build": {
    "op": "number_of",
    "arguments_from": {
      "associate": "$X"
    }
  },
  "effect": "propose_candidate",
  "evidence_ids": [
    "S-ENG"
  ],
  "non_claim": "通用组合是假说生成规则；不是文献声称所有同形词都符合该规则。",
  "forbidden_effects": [
    "set_runtime_unit",
    "bind_producer",
    "supply_numeric_constant",
    "select_reading",
    "authorize_conversion"
  ]
}
```


## 7. 固定技术表达候选

```json
[
  {
    "id": "C08",
    "form": "實如法而一",
    "proposes": "division_construction",
    "effect": "propose_candidate",
    "evidence_ids": [
      "S-BK314"
    ],
    "required_context": "technical_computational_expression",
    "policy": "保留整式候选及与组成候选的alternative_group；不按字符串长度或分数自动删除其他解释。",
    "forbidden_effects": [
      "literal_answer_one",
      "drop_operand_bindings",
      "override_reading",
      "force_runtime_result"
    ]
  }
]
```


## 8. Scoped facts（K1运行视图不消费）

```json
[
  {
    "id": "F-SF-CH-M",
    "subject": "章月",
    "predicate": "numeric_declaration",
    "value": 235,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-CH-Y",
    "subject": "章法",
    "predicate": "numeric_declaration",
    "value": 19,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-BU-M",
    "subject": "蔀月",
    "predicate": "numeric_declaration",
    "value": 940,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-BU-D",
    "subject": "蔀日",
    "predicate": "numeric_declaration",
    "value": 27759,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-BU-Y",
    "subject": "蔀法",
    "predicate": "numeric_declaration",
    "value": 76,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-YM",
    "subject": "year_to_lunation",
    "predicate": "conversion_model",
    "value": {
      "numerator_fact": "F-SF-CH-M",
      "denominator_fact": "F-SF-CH-Y",
      "from": "completed_year_count",
      "to": "lunation_count",
      "frame_relation": "common_obscuration_origin",
      "preconditions": [
        "year_coordinate_confirmed",
        "model_selected",
        "parameter_bindings_valid"
      ]
    },
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C46",
      "S-CCONST"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-MD",
    "subject": "lunation_to_day",
    "predicate": "conversion_model",
    "value": {
      "numerator_fact": "F-SF-BU-D",
      "denominator_fact": "F-SF-BU-M",
      "from": "lunation_count",
      "to": "day_duration",
      "preconditions": [
        "lunation_kind_confirmed",
        "model_selected",
        "parameter_bindings_valid"
      ]
    },
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C47",
      "S-CCONST"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-COORD",
    "subject": "入蔀年@§46",
    "predicate": "counting_convention",
    "value": {
      "coordinate_kind": "ordinal",
      "index_base": 1,
      "boundary": "start_of_current_year",
      "origin": "current_obscuration_start",
      "step_unit": "year",
      "result_of_subtract_one": "completed_year_count"
    },
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "SF.46",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C46",
      "S-L67"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-FA4",
    "subject": "日法",
    "predicate": "numeric_declaration",
    "value": 4,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST"
    ],
    "assertion_kind": "edited_primary_statement",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-ST-FA81",
    "subject": "日法",
    "predicate": "numeric_parameter",
    "value": 81,
    "scope": {
      "tradition": "San_tong_li",
      "section": "lunar_scaling",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C23"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-ZF42",
    "subject": "中法",
    "predicate": "numeric_declaration",
    "value": 42,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-REPO"
    ],
    "assertion_kind": "repo_transcription",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": false,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-ZF32",
    "subject": "中法",
    "predicate": "edited_numeric_declaration",
    "value": 32,
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "solar_lunar",
      "astral_body": null
    },
    "evidence_ids": [
      "S-CCONST",
      "S-L69"
    ],
    "assertion_kind": "editorial_reading",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-SOLAR",
    "subject": "日率@planetary",
    "predicate": "semantic_interpretation",
    "value": {
      "referent": "solar_cycle_count",
      "role": "ratio_parameter",
      "counterpart": "周率",
      "not_inferred": "day^-1"
    },
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "planetary",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C79"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  },
  {
    "id": "F-SF-RESIDUAL",
    "subject": "日餘/中法@§49",
    "predicate": "residual_model",
    "value": {
      "numerator": 168,
      "denominator": 32,
      "value": "21/4",
      "whole_days_omitted_per_year": 360,
      "kind": "annual_day_residue"
    },
    "scope": {
      "tradition": "Han_Si_fen_li",
      "section": "SF.49",
      "astral_body": null
    },
    "evidence_ids": [
      "S-C49",
      "S-L69"
    ],
    "assertion_kind": "scholarly_interpretation",
    "eligibility": "scope_and_prerequisites_must_match",
    "selection_required": true,
    "runtime_loaded": false
  }
]
```


## 9. 人工动作

| ID | 阶段 | 作用 | 当前状态 | 校验 | 恢复 |
| --- | --- | --- | --- | --- | --- |
| resegment | O/S | 重新划分当前原文区间并重新解析 | consumer_present_read_only_verified | 阅读版本与跨度有效；保留覆盖与拆分记录 | lexical_candidates |
| set_lexical_role | S/C | 确定该出现处的语法功能；计划作为候选生成/筛选输入 | metadata_only_in_current_compiler | 语法角色与数量角色分开；不得自动跳过必要操作 | lexical_or_construction_selection |
| select_candidate | S/C | 选择当前候选；新增term_domain适配后支持领域候选 | construction_candidates_only | 候选ID属于当前snapshot和target；领域候选不冒充构式ID | selected_candidate_dependencies |
| set_quantity_semantics | C/A | 说明指定数量的kind、unit、representation等 | semantic_output_consumer_present | 现有API需完整semantic_output地址；输入量/计数坐标字段需新增稳定目标适配 | quantity_constraints |
| bind_value | C/A | 绑定具体producer与output_port | consumer_present_read_only_verified | 相容类型、frame、query、source；仅同名不得建立绑定 | dataflow_linking |
| bind_call | C/A | 绑定既有方法/过程调用 | consumer_present_read_only_verified | 调用签名、实参端口、适用范围匹配 | call_linking |
| attach_context | O/C | 添加有出处的完整背景文档 | consumer_present_read_only_verified | 不把学者数值伪装成原文；相同doc_id不可冲突 | context_compilation |
| select_profile | A | 选择有范围的解释集合 | selection_present_unified_gate_missing | ID存在只是第一步；还需scope、前提、冲突、consumer效应检查 | applicability |
| declare_parameter | C/A | 声明合法根输入 | consumer_present_read_only_verified | 不能把应由术文算出的输出随意当根输入；本次数值另需提供 | input_linking |
| assemble_known_structure | S/C | 当机器没有候选时，按同一有限schema填写操作、槽位与原文证据 | limited_operation_consumer_present | 仅使用现有operation签名；领域term构造器与扩展类型尚需适配 | program_rebuild |
| proposed.compose_term_candidate | S/C | 用同一组合构造器填写scope、quantity等槽位，补出缺失的词义候选 | proposed_not_implemented | 要求子项、跨度、构造器、证据；结果仍为候选 | semantic_candidates |
| proposed.select_reading | O | 选择现有reading或有证据的校读并派生新的analysis文本 | proposed_adapter_not_implemented | 保留底本；更新reading/hash/坐标映射；依赖旧reading的决定需重验 | source_mapping |
| defer | any | 保留未决或提出schema扩展要求 | consumer_present_read_only_verified | 扩展请求不会自动增加executor操作 | unaffected_regions_only |
| retract | any | 撤销决定及依赖授权，重新运行受影响部分 | replay_present_incremental_resume_unverified | 保留历史记录；后代待重验；独立证据仍可另行支持 | earliest_affected_stage |


## 10. 关系词汇

| 关系 | 层 | 中文显示 | 英文显示 | 含义 | 限制 |
| --- | --- | --- | --- | --- | --- |
| associated_with | semantic | 概念关联 | Associated with | 暂只确定某量或参数与一个概念有关 | per_unit_or_same_quantity |
| subtype_of | semantic | 概念上下位 | Subtype of | 概念类型的上下位 | has_part |
| has_part | term_composition | 有序直接成分 | Ordered component | 候选词义组合树包含有序直接成分；保留词素提示叶节点；由child_ids投影 | unordered_part_of_or_dataflow_or_expression_argument_order |
| derived_from | provenance | 解释依据 | Interpretive derivation | 候选或解释依赖证据、规则及前提的认识来源；仅属于provenance层 | reads_writes_producer_output_port_or_source_order |
| produces | dataflow | 产出量 | Produces | 现有event.writes输出端口的显示投影；不新增运行时produces字段 | quotient包含remainder |
| reads | dataflow | 读取量 | Reads | consumer使用具体producer的端口 | same_name |
| localized_in | semantic | 历法语义范围 | Semantic scope | 数量表达的历法语义范围；与原文地址及具体范围实例绑定分开 | source_span_or_confirmed_scope_instance |
| alternative_to | semantic | 替代解释 | Alternative interpretation | 同一判断位置的互斥解释候选 | both_confirmed |
| authorizes | authorization | 授权字段 | Authorizes facet | 满足规则的证据/决定授权某一字段 | authorizes_all_semantics |


## 11. 来源记录（本轮保留原核查身份，不新增历史证明）

```json
[
  {
    "id": "S-C8",
    "kind": "scholarship",
    "title": "Cullen 2017, The Foundations of Celestial Reckoning",
    "locator": "printed p.8; local PDF p.21",
    "checked_by": "local_pdf_text",
    "supports": [
      "月可指天体、lunation 或 civil month；歲可指 solar cycle 或 civil year；本书历法语境下年指 civil year。"
    ],
    "limits": [
      "这里的 sense inventory 是针对本书材料；不宣称跨全部时代穷尽词义。"
    ]
  },
  {
    "id": "S-C23",
    "kind": "scholarship",
    "title": "Cullen 2017",
    "locator": "printed pp.22–23, §1.5.2; local PDF pp.35–36",
    "checked_by": "local_pdf_text",
    "supports": [
      "三统的日法81、月法2392与整数化表示；商余与分母共同表示混合数。"
    ],
    "limits": [
      "数值81不可传播到四分历；这里的位形叙述不能替代对具体物质操作的独立研究。"
    ]
  },
  {
    "id": "S-CCONST",
    "kind": "edited_primary_and_scholarship",
    "title": "Cullen 2017, Han Quarter Remainder system",
    "locator": "printed pp.154–157, §§19–35; local PDF pp.167–170",
    "checked_by": "local_pdf_text_and_page",
    "supports": [
      "章法19、章月235、蔀法76、蔀月940、蔀日27759、日法4；中法的校读32。"
    ],
    "limits": [
      "原文声明给出名字和数值；单位与转换关系仍需相应解释；Cullen 的校读不是 repo 底本文字。"
    ]
  },
  {
    "id": "S-C46",
    "kind": "edited_primary_and_scholarship",
    "title": "Cullen 2017, Proc.3.5",
    "locator": "printed pp.164–165, §46; local PDF pp.177–178",
    "checked_by": "local_pdf_text_and_page",
    "supports": [
      "入蔀年在此为年序位；减一用于蔀首至本年年首的经过年数；235/19 换算；閏餘的月分表示；12阈值比较原始余数。"
    ],
    "limits": [
      "序位减一的解释需要起始序号与端点约定；不能推广到任意 X−1。"
    ]
  },
  {
    "id": "S-C47",
    "kind": "edited_primary_and_scholarship",
    "title": "Cullen 2017, Proc.3.6",
    "locator": "printed pp.165–166, §47; local PDF pp.178–179",
    "checked_by": "local_pdf_text",
    "supports": [
      "积月乘27759再除940；商为积日；小余为以940作分母的日分分子；随后积日按60取余；第二年例为354、348、54。"
    ],
    "limits": [
      "日名还需要蔀首日及计数约定；赋day单位不提供日名。"
    ]
  },
  {
    "id": "S-C49",
    "kind": "edited_primary_and_scholarship",
    "title": "Cullen 2017, Proc.3.8",
    "locator": "printed p.167, §49; local PDF p.180",
    "checked_by": "local_pdf_text",
    "supports": [
      "日餘168、中法32；168/32=21/4是删去整60日后的一年余日；下一气增15日7/32。"
    ],
    "limits": [
      "168/32不是完整年长；本段还校读月餘为日餘；选择中法32不等于同时选择另一处校读。"
    ]
  },
  {
    "id": "S-C79",
    "kind": "edited_primary_and_scholarship",
    "title": "Cullen 2017, Proc.3.36 and Jupiter constants",
    "locator": "printed pp.187–190, §§79–90; local PDF pp.200–203",
    "checked_by": "local_pdf_text_and_page",
    "supports": [
      "日率译作Solar Rate，表示太阳周行数/solar cycles；周率为行星与太阳会合次数；同一段有相应月法构造。"
    ],
    "limits": [
      "以日率乘月率为本包人工构造的词法压力样例；本轮没有为月率登记对应的历史定义。"
    ]
  },
  {
    "id": "S-L67",
    "kind": "scholarship",
    "title": "刘洪涛 2003，《古代历法计算法》",
    "locator": "printed pp.66–67, eqs.(3.7)–(3.9); local PDF pp.86–87",
    "checked_by": "local_pdf_page_visual",
    "supports": [
      "入蔀年减一；235/19换算；余数与闰年阈值；63年例：766月、余16；换算22620日、余594。"
    ],
    "limits": [
      "本轮核对的是上述局部页；没有校验全书。"
    ]
  },
  {
    "id": "S-L69",
    "kind": "scholarship",
    "title": "刘洪涛 2003，《古代历法计算法》",
    "locator": "printed p.69, eqs.(3.11)–(3.12); local PDF p.89",
    "checked_by": "local_pdf_page_visual",
    "supports": [
      "168/32=21/4余日；每气15又7/32日；两种分母表示。"
    ],
    "limits": [
      "完整年长与年余日须分别记录。"
    ]
  },
  {
    "id": "S-BK314",
    "kind": "scholarship",
    "title": "Bréard and Kiel, “實如法而一”: Division and Equality in Early Chinese Mathematical Texts",
    "locator": "ASIA 80(1), printed pp.313–315; local PDF pp.1–3; DOI 10.1515/asia-2025-0025",
    "checked_by": "uploaded_text",
    "supports": [
      "實如法而一是固定技术表达；从非技术的日常词义逐字解释会失败；dividend/divisor角色需技术构式。"
    ],
    "limits": [
      "技术表述支持除法候选，不授权答案恒等于1；本包组合规则是工程建模提案。"
    ]
  },
  {
    "id": "S-DTI8",
    "kind": "historical_software_documentation",
    "title": "DISHAS table interface documentation V2, August 2018",
    "locator": "PDF pp.8–9, Validation / Prediction tools",
    "checked_by": "uploaded_text",
    "supports": [
      "区分suggested与validated；预测需用户确认。"
    ],
    "limits": [
      "该2018文档明确说验证后丢失生成来源记忆；MATHesis这里提出确认后仍永久保留，不声称照搬该行为；未核实DISHAS当前代码。"
    ]
  },
  {
    "id": "S-REPO",
    "kind": "repository_snapshot",
    "title": "Lingyue-001/mathesis",
    "locator": "First checked at 2973dc7014cca300768f54cc9e28139387ac4ef8; rechecked at 63ed5c2b12dbe6501f5f607ec7a062c9e7b50d46 with unchanged calendars-四分历.md blob 16d2b4c8953c7850a5a26264692de44ef13e71e9; source numbered entries 18,24,38–41,71–72",
    "checked_by": "github_connector_read",
    "supports": [
      "原文转录含日法四、中法四十二；天正和朔日术文；二十四气段写月餘；日率出现在五星部分。"
    ],
    "limits": [
      "该转录不自动等于critical edition；本轮保留相同原文blob，未校改原文。旧2973基点只保留为首次证据定位，当前工程基点见baseline_commit。"
    ]
  },
  {
    "id": "S-ENG",
    "kind": "project_design",
    "title": "MATHesis Domain Kernel v0.1 review2",
    "locator": "2026-09-19; present design package",
    "checked_by": "authored_specification",
    "supports": [
      "构造器、类型化组合、逐字段授权、人工循环、文档生成与验收标准是本项目工程提案。"
    ],
    "limits": [
      "纸面预期不能作为引擎实测；schema通过不证明语义正确或泛化。"
    ]
  },
  {
    "id": "S-JSON",
    "kind": "technical_standard",
    "title": "JSON Schema Draft 2020-12",
    "locator": "https://json-schema.org/draft/2020-12/json-schema-core ; https://json-schema.org/draft/2020-12/json-schema-validation",
    "checked_by": "official_web",
    "supports": [
      "使用$defs、$ref、required、additionalProperties、oneOf描述结构。"
    ],
    "limits": [
      "JSON Schema检查结构，跨记录语义、scope gate、消费者实际行为仍需独立检查。"
    ]
  },
  {
    "id": "S-PROV",
    "kind": "technical_standard",
    "title": "W3C PROV-O",
    "locator": "https://www.w3.org/TR/prov-o/",
    "checked_by": "official_web",
    "supports": [
      "区分来源实体、生成活动和操作者，为本包provenance字段设计提供参考。"
    ],
    "limits": [
      "本包采用JSON表示，不宣称RDF/PROV-O合规。"
    ]
  }
]
```

## K1 运行产物封装

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://mathesis.local/domain-kernel/output.schema.json",
  "type": "object",
  "properties": {
    "schema": {
      "const": "TermSemanticCandidates/1"
    },
    "identity": {
      "type": "object",
      "properties": {
        "doc_id": {
          "type": "string",
          "minLength": 1
        },
        "reading_id": {
          "type": "string",
          "minLength": 1
        },
        "source_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "registry_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "schema_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "engine_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "dependency_hashes": {
          "type": "object",
          "required": [
            "analysis_parser.inputs",
            "analysis_parser.lexical",
            "analysis_parser.construction_ir",
            "analysis_parser.syntax_ir"
          ],
          "additionalProperties": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$"
          }
        },
        "options": {
          "type": "object",
          "properties": {
            "max_candidates": {
              "type": "integer",
              "minimum": 1
            },
            "term_regions": {
              "type": "array",
              "items": {
                "$ref": "kernel.schema.json#/$defs/SourceAnchor"
              }
            }
          },
          "required": [
            "max_candidates",
            "term_regions"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "doc_id",
        "reading_id",
        "source_sha256",
        "registry_sha256",
        "schema_sha256",
        "engine_sha256",
        "dependency_hashes",
        "options"
      ],
      "additionalProperties": false
    },
    "candidates": {
      "type": "array",
      "items": {
        "allOf": [
          {
            "$ref": "kernel.schema.json#/$defs/SemanticCandidate"
          },
          {
            "required": [
              "analysis_range",
              "region_ids",
              "generated_by",
              "precondition_checks"
            ],
            "properties": {
              "claim_authority": {
                "const": "S"
              },
              "support_status": {
                "const": "proposed"
              },
              "authorization_status": {
                "const": "not_authorized"
              },
              "authorization_refs": {
                "const": []
              },
              "expression": {
                "$ref": "kernel.schema.json#/$defs/Expression"
              },
              "span": {
                "$ref": "kernel.schema.json#/$defs/SourceAnchor"
              }
            }
          }
        ]
      }
    },
    "fixed_expression_candidates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "span": {
            "$ref": "kernel.schema.json#/$defs/SourceAnchor"
          },
          "analysis_range": {
            "type": "array",
            "prefixItems": [
              {
                "type": "integer",
                "minimum": 0
              },
              {
                "type": "integer",
                "minimum": 1
              }
            ],
            "items": false,
            "minItems": 2,
            "maxItems": 2
          },
          "rule_id": {
            "type": "string",
            "minLength": 1
          },
          "proposes": {
            "type": "string",
            "minLength": 1
          },
          "alternative_group": {
            "type": "string",
            "minLength": 1
          },
          "claim_authority": {
            "const": "S"
          },
          "support_status": {
            "const": "proposed"
          },
          "authorization_status": {
            "const": "not_authorized"
          },
          "authorization_refs": {
            "const": []
          },
          "constraint_status": {
            "const": "underdetermined"
          },
          "provenance_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "precondition_checks": {
            "type": "object",
            "additionalProperties": {
              "enum": [
                "unchecked",
                "compatible",
                "incompatible",
                "underdetermined"
              ]
            }
          },
          "generated_by": {
            "type": "string",
            "minLength": 1
          }
        },
        "required": [
          "id",
          "span",
          "analysis_range",
          "rule_id",
          "proposes",
          "alternative_group",
          "claim_authority",
          "support_status",
          "authorization_status",
          "authorization_refs",
          "constraint_status",
          "provenance_ids",
          "precondition_checks",
          "generated_by"
        ],
        "additionalProperties": false
      }
    },
    "regions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "span": {
            "$ref": "kernel.schema.json#/$defs/SourceAnchor"
          },
          "analysis_range": {
            "type": "array",
            "prefixItems": [
              {
                "type": "integer",
                "minimum": 0
              },
              {
                "type": "integer",
                "minimum": 1
              }
            ],
            "items": false,
            "minItems": 2,
            "maxItems": 2
          },
          "basis": {
            "enum": [
              "explicit_selection",
              "grammar_candidate"
            ]
          },
          "origins": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "parent_id": {
                  "type": "string",
                  "minLength": 1
                },
                "slot": {
                  "type": "string",
                  "minLength": 1
                },
                "node_id": {
                  "type": "string",
                  "minLength": 1
                }
              },
              "required": [
                "parent_id",
                "slot",
                "node_id"
              ],
              "additionalProperties": false
            }
          }
        },
        "required": [
          "id",
          "span",
          "analysis_range",
          "basis",
          "origins"
        ],
        "additionalProperties": false
      }
    },
    "diagnostics": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "truncated": {
      "type": "boolean"
    },
    "syntax_preview": {
      "type": "object",
      "required": [
        "nodes",
        "roots",
        "diagnostics",
        "token_coverage"
      ]
    }
  },
  "required": [
    "schema",
    "identity",
    "candidates",
    "fixed_expression_candidates",
    "regions",
    "diagnostics",
    "truncated",
    "syntax_preview"
  ],
  "additionalProperties": false
}
```

## 实际消费者与能力状态

| 能力 | 状态 | producer | validator | consumer | 允许效果 | 效应测试 |
| --- | --- | --- | --- | --- | --- | --- |
| compositional_candidates | suggestion_only | ["domain_kernel/engine.py::suggest_term_semantics"] | ["domain_kernel/engine.py::validate_term_bundle"] | ["domain_kernel/engine.py::suggest_packet_semantics"] | Emit source-grounded S-only hypotheses; no unit, scale, instance or execution authority. | ["tests/domain_kernel/test_engine.py::EngineTests.test_nested_composition_without_terms","tests/domain_kernel/test_engine.py::EngineTests.test_registry_rules_are_consumed_and_input_is_unchanged","tests/domain_kernel/test_engine.py::EngineTests.test_all_authored_probe_derivations_are_generated","tests/domain_kernel/test_engine.py::EngineTests.test_candidate_limit_avoids_quadratic_interval_allocation","tests/domain_kernel/test_engine.py::EngineTests.test_all_rules_have_observable_effect_without_whole_terms"] |
| shared_candidate_schema | suggestion_only | ["domain_kernel/engine.py::suggest_packet_semantics"] | ["domain_kernel/engine.py::validate_term_bundle"] | ["tools/parser_inspector/runner.py::run","tools/parser_inspector/readable.py::compile_view","tools/parser_inspector/readable.py::render_html"] | Validate shape offline and verify source/type/derivation at runtime. | ["tests/domain_kernel/test_engine.py::EngineTests.test_schema_offline_and_shared_axes","tests/domain_kernel/test_engine.py::EngineTests.test_validator_rejects_corrupt_identity_structure_and_authority","tests/domain_kernel/test_engine.py::EngineTests.test_fixed_validator_rejects_rehashed_contract_and_authority_changes","tests/domain_kernel/test_engine.py::EngineTests.test_region_provenance_must_resolve_to_actual_selection_or_syntax"] |
| optional_inspector_output | suggestion_only | ["domain_kernel/engine.py::suggest_packet_semantics"] | ["domain_kernel/engine.py::validate_term_bundle"] | ["tools/parser_inspector/runner.py::run","tools/parser_inspector/readable.py::compile_view"] | Backend opt-in remains default off. Fixed Inspector enables read-only term candidates after R2; source and R1–R4 HTML, native reports and reviewed graph remain unchanged. No decisions or runtime authority. | ["tools/parser_inspector/test_term_semantics.py::TermSemanticsTests.test_native_reports_artifacts_html_and_both_entrypoints","tools/parser_inspector/test_term_semantics.py::TermSemanticsTests.test_candidate_failure_is_separate_and_clears_previous_result","tools/parser_inspector/test_term_semantics.py::TermSemanticsTests.test_switching_off_removes_owned_file_and_preserves_old_bytes","tools/parser_inspector/test_term_semantics.py::TermPresentationTests.test_real_primary_readonly_section_position_and_all_alternatives","tools/parser_inspector/test_term_semantics.py::TermPresentationTests.test_tree_uses_ordered_child_ids_not_expression_arguments","tools/parser_inspector/test_term_semantics.py::TermPresentationTests.test_failures_are_local_including_malformed_trees"] |
| reproducible_docs | implemented | ["domain_kernel/docs.py::render_documents"] | ["domain_kernel/docs.py::validate_manifest"] | ["domain_kernel/docs.py::main"] | Generate and check reference docs; no CI or website hook. | ["tests/domain_kernel/test_docs.py::DocumentationTests.test_check_detects_stale_docs_without_writing","tests/domain_kernel/test_docs.py::DocumentationTests.test_manifest_checks_real_symbols_and_effect_tests"] |
| existing_local_lexical_role | metadata_only | ["adjudication/compiler.py::_apply_local_lexical_roles"] | ["adjudication/compiler.py::compile_reviewed"] | ["adjudication/compiler.py::compile_reviewed"] | Existing reviewed lexical metadata only; no new domain decision routing. | [] |
| term_candidate_selection | planned | [] | [] | [] | Future adaptation to existing adjudication/compiler inputs. | [] |
| input_count_coordinates | planned | [] | [] | [] | Future explicit index base, origin and boundary inputs. | [] |
| reading_selection | planned | [] | [] | [] | Future reading selection via existing source/replay contracts. | [] |
| unified_authorization_gate | planned | [] | [] | [] | Future applicability checks replacing old heading/profile overreach. | [] |
| automatic_resume | planned | [] | [] | [] | Future authorized recompilation via existing compile_reviewed, not a new state machine. | [] |

符号存在校验不等于效应测试执行；实际测试结果见 INTEGRATION.md。后端候选选项默认关闭；固定 Inspector 在 R2 后开启只读候选展示。未接网站 build/CI，未实现 kernel/code 失效 watcher。
