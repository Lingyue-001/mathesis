# Sifen Proc. 3.5 Automatic Reconstruction Trial

This file is an automatic trial. It does not use a handwritten step list and does not generate gold.

## Summary

| Field | Value |
| --- | --- |
| target | Proc. 3.5 / §46 / cullen:chunk:62 |
| source units | 8 |
| translation units | 7 |
| candidate count | 8 |
| aligned candidates | 7 |
| confidence | high 7, medium 0, low 1 |
| arithmetic validation ready | false |
| automation verdict | automatic_trial_partially_successful_but_requires_human_review |
| main limitation | Automatic rules can recover the local operation sequence, but semantic variable names and quotient/remainder formalization remain caveated. |

## Auto Candidates

| id | op | source | translation | expression | score | confidence | caveats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Proc. 3.5.auto.1 | procedure_scope_title | 推天正術 |  |  | 0.18 | low | not_aligned, no_commentary_sentence_matched_by_keywords, no_same_chunk_template_support, not_formalizable_yet |
| Proc. 3.5.auto.2 | set_out | 置入蔀年 | Set out the years into the Obscuration. | current_value = input("入蔀年") | 0.888 | high | no_same_chunk_template_support, formalizable_with_caveat |
| Proc. 3.5.auto.3 | subtract | 減一 | subtract one. | current_value = current_value - 1 | 0.833 | high | no_same_chunk_template_support |
| Proc. 3.5.auto.4 | multiply | 以章月乘之 | Multiply by Rule Months [235]. | current_value = current_value * Rule Months [235] | 0.969 | high |  |
| Proc. 3.5.auto.5 | count_filled | 滿章法得一 | Count one for each Rule Factor [19] filled. | quotient = floor(current_value / Rule Factor [19]) | 0.869 | high | no_same_chunk_template_support, formalizable_with_caveat, counting_filled_as_floor_division_is_modern_formalization |
| Proc. 3.5.auto.6 | name_output | 名為積月 | Call this Accumulated Months. | 積月 = quotient | 0.809 | high | no_same_chunk_template_support, formalizable_with_caveat |
| Proc. 3.5.auto.7 | remainder_output | 不滿為閏餘 | The remainder is the Intercalation Remainder. | 閏餘 = current_value mod Rule Factor [19] | 0.809 | high | no_same_chunk_template_support, formalizable_with_caveat, remainder_as_modulo_depends_on_previous_count_filled_step |
| Proc. 3.5.auto.8 | threshold_condition | 十二以上, 其歲有閏 | If it is 12 or more, this year has an intercalation. | condition = 閏餘 >= 12 | 0.833 | high | no_same_chunk_template_support |

## Evidence Highlights

### Proc. 3.5.auto.1 procedure_scope_title

- Source: 推天正術
- Translation: (none)
- Expression candidate: (none)
- Matched features: source_matches_^推.+術$

### Proc. 3.5.auto.2 set_out

- Source: 置入蔀年
- Translation: Set out the years into the Obscuration.
- Expression candidate: current_value = input("入蔀年")
- Matched features: same_operation_type, preserves_order, order_distance_0, set_out_object_match_obscuration_years
- Commentary support:
  - The first procedure deals with the fact that ‘years into the obscuration’ 入 蔀 年 means the ordinal number of year in the Obscuration.
  - We start from the beginning of the current Obscuration, at which we are guaranteed that midnight, conjunction beginning the first Celestial month and winter solstice coincide.

### Proc. 3.5.auto.3 subtract

- Source: 減一
- Translation: subtract one.
- Expression candidate: current_value = current_value - 1
- Matched features: same_operation_type, preserves_order, order_distance_0, numeric_value_match
- Commentary support:
  - Since we want the number of years from the start of the Obscuration to the start of the current year, we have to subtract one from this number.
  - Then we use the fact that 235 months are exactly equivalent to 19 years to find how many whole months have elapsed since the start of the Obscuration.

### Proc. 3.5.auto.4 multiply

- Source: 以章月乘之
- Translation: Multiply by Rule Months [235].
- Expression candidate: current_value = current_value * Rule Months [235]
- Matched features: same_operation_type, preserves_order, order_distance_0
- Commentary support:
  - Then we use the fact that 235 months are exactly equivalent to 19 years to find how many whole months have elapsed since the start of the Obscuration.
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- Template support:
  - 以[OBJECT]乘之 ↔ Multiply [OBJECT] by [OBJECT]; count 7

### Proc. 3.5.auto.5 count_filled

- Source: 滿章法得一
- Translation: Count one for each Rule Factor [19] filled.
- Expression candidate: quotient = floor(current_value / Rule Factor [19])
- Matched features: same_operation_type, preserves_order, order_distance_0
- Commentary support:
  - The remainder will be a fraction of a month at a scale of Rule Factor [19].
  - This condition recurs at the beginning of the next Rule 19 years later, but the conjunction with which the first winter solstice of that Rule coincides is seven later than the one that would have been indicated if winter solstices were separated by exactly 12 lunations each.

### Proc. 3.5.auto.6 name_output

- Source: 名為積月
- Translation: Call this Accumulated Months.
- Expression candidate: 積月 = quotient
- Matched features: same_operation_type, preserves_order, order_distance_0
- Commentary support:
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
  - Then we use the fact that 235 months are exactly equivalent to 19 years to find how many whole months have elapsed since the start of the Obscuration.

### Proc. 3.5.auto.7 remainder_output

- Source: 不滿為閏餘
- Translation: The remainder is the Intercalation Remainder.
- Expression candidate: 閏餘 = current_value mod Rule Factor [19]
- Matched features: same_operation_type, preserves_order, order_distance_0
- Commentary support:
  - This is the Intercalation Remainder, and may be taken as the pending fraction of a new intercalary month representing the amount by which the start of the new year is in advance of its ideal date, which should coincide with winter solstice.
  - Now since 235/19 is 12 + 7/19, it is clear that by the end of the year we are now starting the Intercalation Remainder will have increased by 7.

### Proc. 3.5.auto.8 threshold_condition

- Source: 十二以上, 其歲有閏
- Translation: If it is 12 or more, this year has an intercalation.
- Expression candidate: condition = 閏餘 >= 12
- Matched features: same_operation_type, preserves_order, order_distance_0, numeric_value_match
- Commentary support:
  - So if at the start of the current year this Remainder is 12 or more, the Remainder will at least have reached 19 by the end of the year, calling for a delay of a whole month before the next year starts – which requires an intercalary month to be inserted in the current year, as stated.
  - This is the Intercalation Remainder, and may be taken as the pending fraction of a new intercalary month representing the amount by which the start of the new year is in advance of its ideal date, which should coincide with winter solstice.

## Existing Exploratory Alignment Comparison

- Found: true
- Note: Existing exploratory alignment is recorded for comparison only; it is not used as binding authority by this automatic trial.

| source | translation | confidence | score |
| --- | --- | --- | --- |
| 推天正術 | §46 Set out the years into the Obscuration and subtract one. | low | 46 |
| 置入蔀年減一 | Multiply by Rule Months [235]. | medium | 53 |
| 以章月乘之 | Count one for each Rule Factor [19] filled. | low | 45 |
| 滿章法得一 | Call this Accu- mulated Months. | low | 44 |
| 名為積月 | The remainder is the Intercalation Remainder. | medium | 54 |

## Quality Judgment

- The automatic trial recovers the broad operation order for this Proc without a handwritten step list.
- It still produces generic expressions such as `current_value = ...`; human/LLM review is needed to assign stable algorithmic variable names.
- The count-filled and remainder steps are machine-formalizable only with caveats because floor/modulo are modern formalizations of Cullen's wording.
- This supports building a reviewable extraction layer, but not yet autonomous full algorithm reconstruction.

