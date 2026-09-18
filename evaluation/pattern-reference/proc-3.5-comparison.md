# cullen:ch3:chunk:0055 — reference 与 machine 对照

仅用于 evaluation。原人工 steps 原样保留；reference 由确定性 Python importer 机械生成。

| 人工步骤 | 原文／corpus 字符区间 | 旧 operation | machine construction → event | 结果 |
|---|---|---|---|---|
| step-1 | 置入蔀年 [5,9) | set | load / sifen:38:ast6 → load / e4 | match |
| step-2 | 減一 [9,11) | subtract | load / sifen:38:ast6 → subtract / e6 | match |
| step-3 | 以章月乘之 [12,17) | multiply | multiply / sifen:38:ast9 → multiply / e7 | match |
| step-4 | 滿章法得一 [18,23) | fill_divide | divide / sifen:38:ast12 → divmod / e8 | match |
| step-5 | 名為積月 [24,28) | name_result | name / sifen:38:ast14 → alias / e9 | match |
| step-6 | 不滿為閏餘 [29,34) | name_remainder | remainder_name / sifen:38:ast16 → alias / e10 | match |
| step-7 | 十二以上 [35,39)；其歲有閏 [40,44) | judge | threshold / sifen:38:ast19 → threshold / e12 | match |

| 步骤 | 原人工 input / parameter → output | 实际机器输入（producer.port）→ 输出 |
|---|---|---|
| step-1 | 入蔀年 / — → out1 | input=v3 (e3.result) → result=v4 |
| step-2 | out1 / 一 → out2 | input=v4 (e4.result); parameter=v5 (e5.result) → result=v6 |
| step-3 | out2 / 章月 → out3 | input=v6 (e6.result); parameter=v2 (e2.result) → result=v7 |
| step-4 | out3 / 章法 → quotient=quot4;remainder=rem4 | input=v7 (e7.result); parameter=v1 (e1.result) → quotient=v8; remainder=v9 |
| step-5 | quot4 / — → 積月 | input=v8 (e8.quotient) → result=v10 |
| step-6 | rem4 / — → 閏餘 | input=v9 (e8.remainder) → result=v11 |
| step-7 | 閏餘 / value(閏餘)>=十二 → 其歲有閏 | input=v11 (e10.result); parameter=v12 (e11.result) → result=v13 |

语义步骤对照：7/7。这不是 parser 准确率或图闭合率。

## 粒度与证据

- 一个 machine construction `sifen:38:ast6` 对应多个 manual semantic steps：step-1, step-2。
- step-7 使用 2 个 exact source spans：十二以上；其歲有閏。
- 逐步检查输入引用、producer/output port、literal、商／余数及命名／判断属性；文字重叠本身不算 match。
- 两份 reading、原始人工字段、逐字符映射和导入 provenance 见 proc-3.5.json；operation 映射见 operation-crosswalk.json。

## 机器仍然存在的缺口

```json
{
  "machine_unresolved": [],
  "machine_diagnostics": [],
  "machine_program_diagnostics": [],
  "machine_link_diagnostics": [
    {
      "kind": "missing_import",
      "definition_id": "def-2e26c7772103b8a537d4",
      "formal": "入蔀年",
      "candidates": [],
      "source_spans": [
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 0,
          "end": 4,
          "quote": "推天正術"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 5,
          "end": 11,
          "quote": "置入蔀年減一"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 12,
          "end": 17,
          "quote": "以章月乘之"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 18,
          "end": 23,
          "quote": "滿章法得一"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 24,
          "end": 28,
          "quote": "名為積月"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 29,
          "end": 34,
          "quote": "不滿為閏餘"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 35,
          "end": 39,
          "quote": "十二以上"
        },
        {
          "doc_id": "sifen:38",
          "reading_id": "sifen:38.7e79b4ae7a87",
          "start": 40,
          "end": 44,
          "quote": "其歲有閏"
        }
      ]
    }
  ],
  "machine_unparsed_spans": []
}
```

Reference 不修改上述缺口，不判定 graph closure，也不传给 parser。

复现 Proc.3.5：`python -X utf8 -m evaluation.pattern_reference --output .cache/pattern-reference`。

## 输入身份（JSON 按键排序、UTF-8 的 SHA-256）

```json
{
  "packet": "5d18b4de2c233ba00bcc1fc0241a2899ef4fc1b9339899f02321ae22ad8b5474",
  "graph": "eb59ab121135ad366947ff7df4087be30113a220c2843a161af1fc1046d4d403",
  "reference": "100d7024696c21a4bdf80007bc82c806813f6646f3a7356a8b95e0f51f89b133",
  "crosswalk": "da9323d16d38c6e3dbcca020788f36cf65be693aa15b19e0f609c49156798592"
}
```
