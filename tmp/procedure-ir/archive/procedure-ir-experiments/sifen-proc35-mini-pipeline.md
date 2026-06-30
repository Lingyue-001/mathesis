# Sifen Proc. 3.5 Mini Pipeline Pilot

This is a single-Proc pilot for evidence assembly, not final extraction, not gold, and not a writeback plan.

## Summary

| Field | Value |
| --- | --- |
| proc_id | Proc. 3.5 |
| unit_id | §46 |
| chunk_id | cullen:chunk:62 |
| book pages | 164-165 |
| step count | 8 |
| alignment risks | 6 |
| average evidence score | 0.74 |
| arithmetic validation ready now | false |
| verdict | Supports a curated Proc-level mini pipeline, but does not yet support fully automatic reconstruction or arithmetic validation. |

## Source Chunk

- Source: 推天正術， 置入蔀年減一， 以章月乘之， 滿章法得一， 名為積月， 不滿為閏餘， 十二以上, 其歲有閏．
- Translation: §46 Set out the years into the Obscuration and subtract one. Multiply by Rule Months [235]. Count one for each Rule Factor [19] filled. Call this Accu- mulated Months. The remainder is the Intercalation Remainder. If it is 12 or more, this year has an intercalation.
- Commentary excerpt: This section and the next aim to predict the sexagenary day name of the first day of the first month of the current year according to the Celestial count. We start from the beginning of the current Obscuration, at which we are guaranteed that midnight, conjunction beginning the first Celestial month and winter solstice coin- cide. We already know (from Proc. 3.3) the sexagenary day name with which the Obscuration begins. Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not. The first procedure deals with the fact that ‘years into the obscuration’ 入 蔀 年 means the ordinal number of year in the Obscuration. Since we want the number of years from the start of the Obscuration to the start of the current year, we have to subtract one from this number. Then we use the fact that 2…

## Step Candidates

| step | role | operation_id | source | translation | formal expression | evidence | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Proc.3.5.step.0 | procedure_title | procedure_scope_title | 推天正術 |  |  | scope_phrase_not_operation (0.48) | medium |
| Proc.3.5.step.1 | input_binding | set_out_years_into_obscuration | 置入蔀年 | Set out the years into the Obscuration | years_into_obscuration = input("入蔀年") | translation_and_commentary_explicit (0.74) | high |
| Proc.3.5.step.2 | operation | subtract_one_to_elapsed_years | 減一 | subtract one | elapsed_years = years_into_obscuration - 1 | translation_and_commentary_explicit (0.74) | high |
| Proc.3.5.step.3 | operation | multiply_by_rule_months | 以章月乘之 | Multiply by Rule Months [235]. | product = elapsed_years × 章月 | translation_commentary_template_supported (0.92) | high |
| Proc.3.5.step.4 | operation | count_one_for_each_rule_factor_filled | 滿章法得一 | Count one for each Rule Factor [19] filled. | quotient = floor(product / 章法) | translation_and_commentary_explicit (0.74) | high |
| Proc.3.5.step.5 | output_label | name_quotient_accumulated_months | 名為積月 | Call this Accu- mulated Months. | 積月 = quotient | translation_and_commentary_explicit (0.74) | high |
| Proc.3.5.step.6 | output_label | name_remainder_intercalation_remainder | 不滿為閏餘 | The remainder is the Intercalation Remainder. | 閏餘 = product mod 章法 | translation_and_commentary_explicit (0.74) | high |
| Proc.3.5.step.7 | condition | threshold_intercalary_year | 十二以上, 其歲有閏 | If it is 12 or more, this year has an intercalation. | has_intercalary_month = 閏餘 >= 12 | translation_and_commentary_explicit (0.82) | high |

## Detailed Evidence

### Proc.3.5.step.0 procedure_scope_title

- Source phrase: 推天正術
- Cullen commentary support:
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- Notes:
  - Treat as the procedure title/scope phrase, not as an arithmetic operation.

### Proc.3.5.step.1 set_out_years_into_obscuration

- Source phrase: 置入蔀年
- Cullen translation phrase: Set out the years into the Obscuration
- Cullen commentary support:
  - The first procedure deals with the fact that ‘years into the obscuration’ 入 蔀 年 means the ordinal number of year in the Obscuration.
- Alignment risk:
  - Existing alignment paired with: Multiply by Rule Months [235].
- Notes:
  - This is a variable-binding step, not an arithmetic calculation.

### Proc.3.5.step.2 subtract_one_to_elapsed_years

- Source phrase: 減一
- Cullen translation phrase: subtract one
- Cullen commentary support:
  - Since we want the number of years from the start of the Obscuration to the start of the current year, we have to subtract one from this number.
- Alignment risk:
  - Existing alignment paired with: Multiply by Rule Months [235].
- Notes:
  - Cullen commentary explicitly explains why one is subtracted.

### Proc.3.5.step.3 multiply_by_rule_months

- Source phrase: 以章月乘之
- Cullen translation phrase: Multiply by Rule Months [235].
- Cullen commentary support:
  - Then we use the fact that 235 months are exactly equivalent to 19 years to find how many whole months have elapsed since the start of the Obscuration.
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- Template support:
  - 以[OBJECT]乘之 ↔ Multiply [OBJECT] by [OBJECT]; count 7; strength targeted_prespecified_same_unit
- Candidate audit support:
  - operation_template_pair:以乘之__Multiply_by; status medium_candidate_needs_human_confirmation; score 0.7144
- Alignment risk:
  - Existing alignment paired with: Count one for each Rule Factor [19] filled.
- Notes:
  - Global template support exists for 以[OBJECT]乘之 ↔ Multiply by [OBJECT], but local binding comes from this Proc.

### Proc.3.5.step.4 count_one_for_each_rule_factor_filled

- Source phrase: 滿章法得一
- Cullen translation phrase: Count one for each Rule Factor [19] filled.
- Cullen commentary support:
  - Then we use the fact that 235 months are exactly equivalent to 19 years to find how many whole months have elapsed since the start of the Obscuration.
  - The remainder will be a fraction of a month at a scale of Rule Factor [19].
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- Alignment risk:
  - Existing alignment paired with: Call this Accu- mulated Months.
- Notes:
  - Cullen gives the operation as counting filled Rule Factors; floor division is the modern formalization of that count.

### Proc.3.5.step.5 name_quotient_accumulated_months

- Source phrase: 名為積月
- Cullen translation phrase: Call this Accu- mulated Months.
- Cullen commentary support:
  - Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- Alignment risk:
  - Existing alignment paired with: The remainder is the Intercalation Remainder.
- Notes:
  - This is a naming/binding step rather than a new arithmetic operation.

### Proc.3.5.step.6 name_remainder_intercalation_remainder

- Source phrase: 不滿為閏餘
- Cullen translation phrase: The remainder is the Intercalation Remainder.
- Cullen commentary support:
  - The remainder will be a fraction of a month at a scale of Rule Factor [19].
  - This is the Intercalation Remainder, and may be taken as the pending fraction of a new intercalary month representing the amount by which the start of the new year is in advance of its ideal date, which should coincide with winter solstice.
- Alignment risk:
  - Existing alignment paired with: If it is 12 or more, this year has an intercalation.
- Notes:
  - The modulo expression is a modern formalization of the named remainder after counting filled Rule Factors.

### Proc.3.5.step.7 threshold_intercalary_year

- Source phrase: 十二以上, 其歲有閏
- Cullen translation phrase: If it is 12 or more, this year has an intercalation.
- Cullen commentary support:
  - So if at the start of the current year this Remainder is 12 or more, the Remainder will at least have reached 19 by the end of the year, calling for a delay of a whole month before the next year starts – which requires an intercalary month to be inserted in t…
- Notes:
  - This is a threshold condition, not a lookup table.

## Alignment Risks

| step | source | expected translation | existing aligned translation | confidence |
| --- | --- | --- | --- | --- |
| Proc.3.5.step.1 | 置入蔀年 | Set out the years into the Obscuration | Multiply by Rule Months [235]. | medium |
| Proc.3.5.step.2 | 減一 | subtract one | Multiply by Rule Months [235]. | medium |
| Proc.3.5.step.3 | 以章月乘之 | Multiply by Rule Months [235]. | Count one for each Rule Factor [19] filled. | low |
| Proc.3.5.step.4 | 滿章法得一 | Count one for each Rule Factor [19] filled. | Call this Accu- mulated Months. | low |
| Proc.3.5.step.5 | 名為積月 | Call this Accu- mulated Months. | The remainder is the Intercalation Remainder. | medium |
| Proc.3.5.step.6 | 不滿為閏餘 | The remainder is the Intercalation Remainder. | If it is 12 or more, this year has an intercalation. | high |

## Interpretation

- This Proc is suitable for a curated algorithm-reconstruction pilot because source, translation, and Cullen commentary all support the main sequence.
- It is not ready for automatic arithmetic validation because no concrete worked-example input value for 入蔀年 is present in this chunk.
- Existing global template evidence is useful as schema support, but local source/translation/commentary binding remains the authority for this pilot.
- All items are `do_not_writeback: true`.

