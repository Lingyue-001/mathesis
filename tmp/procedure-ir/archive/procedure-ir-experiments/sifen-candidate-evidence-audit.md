# Sifen Candidate Evidence Audit

> Quantitative evidence audit only. This does not create gold data, final glossary entries, or algorithm reconstructions.

## Scoring Formula

- coverage_score: 0.40 source_text_zh + 0.40 translation_en + 0.10 unit_id + 0.10 book_page, averaged over examples
- alignment_score: weighted average of alignment_strength counts; single=1.00, ordinal=0.92, near=0.76, targeted_same_unit=0.64, one_to_many=0.42, same_unit=0.24
- repetition_score: distinct chunk count mapped to 0.20/0.45/0.60/0.72/0.82/0.95/1.00
- specificity_score: literal template content after placeholders, penalizing over-general placeholders
- numeric_agreement_score: matched normalized Chinese/Arabic numbers divided by examples with numbers on both sides; null when not applicable
- contamination_penalty: weighted rate of missing source/translation, page garbage, table-like context, clause-ratio anomaly, and suppressed pairing
- overall_term_pair: 0.22 coverage + 0.24 alignment + 0.18 repetition + 0.18 specificity + 0.12 numeric_or_neutral + 0.06 procedure_coverage - 0.22 contamination
- overall_operation_template_pair: 0.24 coverage + 0.30 alignment + 0.18 repetition + 0.20 specificity + 0.08 procedure_coverage - 0.26 contamination
- status_thresholds: single_chunk_only is capped at single_instance_needs_human_review; otherwise >=0.82 strong_candidate, >=0.62 medium_candidate_needs_human_confirmation, >=0.42 weak_candidate, lower human_review_or_exclude

## Summary

| Metric | Value |
| --- | --- |
| Total candidates | 860 |
| Strong candidates | 8 |
| Medium candidates | 15 |
| Human review or weaker | 837 |

### By Status

| Status | Count |
| --- | --- |
| single_instance_needs_human_review | 818 |
| medium_candidate_needs_human_confirmation | 15 |
| human_review_or_exclude | 11 |
| strong_candidate | 8 |
| weak_candidate | 8 |

### By Candidate Type

| Candidate type | Count |
| --- | --- |
| operation_template_pair | 405 |
| motion_template_pair | 163 |
| term_or_constant_label_pair | 137 |
| expression_template_pair | 75 |
| term_pair | 74 |
| profile_pattern_seed | 6 |

## Strong Candidates

| Status | Type | ZH | EN | Overall | Alignment | Chunks | Failed checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strong_candidate | term_or_constant_label_pair | 合積月 | Conjunction Accumulated Lunations: | 0.9256 | 1 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 月餘 | Lunation Remainder: | 0.8972 | 0.984 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 入月日 | Days of entry into month [NUM]. | 0.8845 | 0.856 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 大餘 | Greater Remainder [NUM]. | 0.8666 | 0.952 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 日度法 | Day and Du Factor [NUM]. | 0.8584 | 0.952 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 小餘 | Lesser Remainder [NUM]. | 0.852 | 1 | 4 |  |
| strong_candidate | term_or_constant_label_pair | 月法 | Lunation Factor [NUM]. | 0.8503 | 0.952 | 5 |  |
| strong_candidate | term_or_constant_label_pair | 積度 | Accumulated Du [NUM]. | 0.8356 | 1 | 4 |  |

## Medium Candidates

| Status | Type | ZH | EN | Overall | Alignment | Chunks | Failed checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 度餘 | Du Remainder [NUM]. | 0.8192 | 1 | 4 |  |
| medium_candidate_needs_human_confirmation | motion_template_pair | 留不行 | It delays and does not move for [NUM] days. | 0.8156 | 0.76 | 6 |  |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 日餘 | Day Remainder [NUM]. | 0.813 | 0.94 | 4 |  |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 虛分 | V oid Parts [NUM]. | 0.8094 | 0.952 | 5 | overgeneral_template |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 日率 | Solar Rate: | 0.796 | 1 | 3 |  |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 周率 | Cycle Rate: | 0.796 | 1 | 3 |  |
| medium_candidate_needs_human_confirmation | operation_template_pair | 除伏逆 | Casting out invisibility and retrogradation, one Appearance is [NUM] days, and it moves [NUM] du. | 0.7721 | 0.675 | 4 | weak_or_ambiguous_alignment |
| medium_candidate_needs_human_confirmation | motion_template_pair | [NUM]日行[NUM]度 | In [NUM] days it moves [NUM] du, and speeds up. | 0.7712 | 0.84 | 2 | low_repetition |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 周率 | Cycle Rate [NUM]. | 0.7543 | 1 | 2 | low_repetition, overgeneral_template |
| medium_candidate_needs_human_confirmation | motion_template_pair | 日行[NUM]分度之[NUM] | In a day it moves [NUM]/[NUM] du, and in [NUM] days it moves [NUM] du. | 0.749 | 0.76 | 2 | low_repetition |
| medium_candidate_needs_human_confirmation | term_or_constant_label_pair | 日率 | Solar Rate [NUM]. | 0.7367 | 1 | 2 | low_repetition, overgeneral_template |
| medium_candidate_needs_human_confirmation | operation_template_pair | 以[OBJECT]乘之 | Multiply [OBJECT] by [OBJECT] | 0.7144 | 0.6086 | 7 | weak_or_ambiguous_alignment, overgeneral_template |
| medium_candidate_needs_human_confirmation | profile_pattern_seed | 滿X得一 / 如X得一 ↔ Count one for each X filled |  | 0.6804 | 0.52 | 19 | profile_seed_not_clause_aligned |
| medium_candidate_needs_human_confirmation | profile_pattern_seed | zh_term_number ↔ en_term_number |  | 0.6804 | 0.52 | 34 | profile_seed_not_clause_aligned |
| medium_candidate_needs_human_confirmation | profile_pattern_seed | 以X乘之 ↔ Multiply by X |  | 0.6231 | 0.52 | 15 | profile_seed_not_clause_aligned |

## Needs Human Review

| Status | Type | ZH | EN | Overall | Alignment | Chunks | Failed checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| single_instance_needs_human_review | operation_template_pair | 不盡名[為]合餘 | What is not exhausted, call it Conjunctions Remainder. | 0.856 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 以日法乘周率為日度法 | By the Day Factor [BRACKETED] Multiply the Cycle Rate to make the Day and Du Factor. | 0.856 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | motion_template_pair | 合以斗[NUM]度[NUM]分[NUM] | Now the days in a lunation (and hence the du moved by the sun between conjunctions) are given by: | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 滿蔀月得[NUM] | Intercalation Remainder is the fraction of a month at a scale of [NUM] by which the conjunction of Celestial New Year falls in advance of the winter solstice. | 0.832 | 0.92 | 1 | low_repetition, numeric_disagreement_or_partial_match, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 以減大周餘 | Join with it the [NUM] du ¼ of Dipper, and this is the du where the sun and moon are located at the Celestial Standard conjunction. | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 以章法乘周率為(用)[月]法 | By multiplying the Cycle Rate by the Rule Factor [BRACKETED] one makes the Lunation Factor, then Rule Months [BRACKETED] multiplies the Solar Rate, and [from the number of] accords with the Lunation Factor, one makes the Accumulated Months and the Lunation Remainder. | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 餘滿蔀(日)[月] | As for the remain- der, [find] the amount of filled Obscuration Months [BRACKETED]. | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 餘滿沒法得[NUM] | The Lesser Remainder of the winter solstice is the remainder when years into the Obscuration are multiplied by Day Remainder [BRACKETED] and divided by Medial [ Qi] factor [BRACKETED]. | 0.832 | 0.92 | 1 | low_repetition, numeric_disagreement_or_partial_match, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 與元通 | [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] An Origin is [NUM] = [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] To make the result a multiple of the Origin, we thus need to multiply by [NUM] × [NUM] × [NUM] = [NUM], an Obscuration Factor. | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 章月乘日率 | Cycle Rate × Rule Factor [BRACKETED] gives the number of Conjunctions in Solar Rate years, at a scale of Rule Factor: | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 周天乘[閏餘]減之 | Diminish it by Circuits of Heaven [BRACKETED] multiplied by Intercalation Remainder. | 0.832 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 不盡為[RESULT] | Count it off starting from jiazi.[NUM], and outside the count is the conjunction day of the month of the planet’s conjunction. | 0.806 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 滿蔀月得[NUM]為積日 | As the Accumulated Days fill [NUM], cast that out, and the remainder is the Greater Remainder. | 0.806 | 0.92 | 1 | low_repetition, numeric_disagreement_or_partial_match, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 命以甲子 | The procedure is a simple conversion of whole months into days and fractions of a day at a scale of Obscuration Months [BRACKETED], using the equivalence: | 0.806 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 其閏[餘]滿[NUM]以上至[NUM]星合閏月 | When we subtract the intercalary months, we are left with the months in the present year, plus a multiple of [NUM] months representing whole years. | 0.806 | 0.92 | 1 | low_repetition, numeric_disagreement_or_partial_match, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 閏或 進退 | Subtracting the latter, we have the months in the present year preceding the month in which the conjunction occurs, on the Celestial month count. | 0.806 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 推朔日 | By Obscuration Days multiply the months into the Era, and as this fills Obscuration Months get one to make Accumulated Days. | 0.806 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 以蔀日乘(之)入紀月 | What is not exhausted is the Lesser Remainder. | 0.806 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | 日率相約取之 | T aking it by harmonising the Solar Rates, obtain for the termination of the five planets [NUM]. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | 如蔀之數 | Wood (Jupiter) [NUM] = [NUM] × [NUM] = [NUM] × [NUM] × [NUM] × [NUM] × [NUM] × [NUM] Fire (Mars) [NUM] = [NUM] × [NUM] × [NUM] × [NUM] Earth (Saturn) [NUM] = [NUM] × [NUM] × [NUM] Metal (Venus) [NUM] = [NUM] × [NUM] Water (Mercury) [NUM] = prime The number given above is the lowest common multiple of these, and its factors are: | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | 則天正合 朔日月所在度 | [NUM] × Circuits of Heaven [BRACKETED]/Obscuration Months [BRACKETED]. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | 則天正後沒也 | It takes on the values [NUM] and [NUM] over a four-year cycle. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_pair | 如月法 | this is Lunation Factor. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_pair | 為積月月餘 | Rule Months [BRACKETED] × Solar Rate gives the number of months in the years of Solar Rate, at a scale of Rule Factor [BRACKETED]. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_pair | 則天正朔日也 | Then that is the day of the Celestial Standard Conjunction. | 0.7948 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | 元會 | Origin Coincidence: | 0.7895 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 積月滿紀月去之 | As Accumulated Months fills Era Months cast them out, and the remain - der makes months entered into the Era. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 經斗除如行母 | When it goes through [the lodge] Dipper, corresponding to the motion denominator, take one in four. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 滿章月得[NUM]為閏 | The Era is the period of [NUM] years or [NUM] months giving repeat of concor - dance for conjunction, qi inception, time of day and sexagenary day number. | 0.784 | 0.76 | 1 | low_repetition, numeric_disagreement_or_partial_match, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 命之如前 | We know how many du the planet moves between conjunc - tion and its appearance while remaining invisible – see for instance section | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 其分有損益 | When the planet moves through the lodge Dipper, of width [NUM]¼ du, we subtract the fraction and calculate accordingly, to find how far the planet has moved into the next lodge. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 其以赤道命度 | Y ou are to count off the du along the Red Road. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | (如)[加]星合日度餘 | In Proc. [NUM], we found where the planet would be when it was in conjunc - tion with the sun. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 以[OBJECT]乘之 | What is not exhausted makes Intercalation Remainder. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | operation_template_pair | 餘以乘周天 | [Reckon] accords with the Day and Du Fac- tor, to make the du and remainder of the Accumulated Du. | 0.784 | 0.76 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | term_or_constant_label_pair | [NUM]合[NUM]日有[NUM]分 | One conjunction is [NUM] days and [NUM] parts, and the motion relative to the stars is like it. | 0.7768 | 0.92 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | motion_template_pair | [NUM]日退[NUM]度 | It turns retrograde, and in a day it retreats [NUM] du. | 0.776 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | motion_template_pair | [NUM]日退[NUM]度 | On visibility it retrogrades, and in a day it retreats [NUM] du. | 0.776 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | motion_template_pair | [NUM]日行[NUM]度 | It returns to [moving] direct, and in [NUM] days moves [NUM] du. | 0.776 | 1 | 1 | low_repetition, single_chunk_only |
| single_instance_needs_human_review | expression_template_pair | 以朔制之 | Of course the month of conjunction may be an intercalary month itself. | 0.7728 | 0.92 | 1 | low_repetition, single_chunk_only |

## Top Examples For Strong Candidates

### 合積月 ↔ Conjunction Accumulated Lunations:

Status: strong_candidate; overall: 0.9256; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:112 §88 Proc. 3.36 p.190 [single_zh_single_en]
  - zh: 合積月
  - en: §88 Conjunction Accumulated Lunations:
- cullen:chunk:125 §101 Proc. 3.36 p.193 [single_zh_single_en]
  - zh: 合積月
  - en: §101 Conjunction Accumulated Lunations:
- cullen:chunk:139 §114 Proc. 3.36 p.194 [single_zh_single_en]
  - zh: 合積月
  - en: §114 Conjunction Accumulated Lunations:

### 月餘 ↔ Lunation Remainder:

Status: strong_candidate; overall: 0.8972; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:113 §89 Proc. 3.36 p.190 [single_zh_single_en]
  - zh: 月餘
  - en: §89 Lunation Remainder:
- cullen:chunk:126 §102 Proc. 3.36 p.193 [single_zh_single_en]
  - zh: 月餘
  - en: §102 Lunation Remainder:
- cullen:chunk:140 §115 Proc. 3.36 p.194 [single_zh_single_en]
  - zh: 月餘
  - en: §115 Lunation Remainder:

### 入月日 ↔ Days of entry into month [NUM].

Status: strong_candidate; overall: 0.8845; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:118 §94 Proc. 3.36 p.191-192 [single_zh_single_en]
  - zh: 入月日
  - en: §94 Days of entry into month 15.
- cullen:chunk:131 §107 Proc. 3.36 p.194 [near_ordinal_aligned]
  - zh: 入月日
  - en: §107 Days of entry into month 12.
- cullen:chunk:145 §120 Proc. 3.36 p.195 [near_ordinal_aligned]
  - zh: 入月日
  - en: §120 Days of entry into month 24.

### 大餘 ↔ Greater Remainder [NUM].

Status: strong_candidate; overall: 0.8666; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:115 §91 Proc. 3.36 p.190 [near_ordinal_aligned]
  - zh: 大餘
  - en: §91 Greater Remainder 23.
- cullen:chunk:128 §104 Proc. 3.36 p.193 [single_zh_single_en]
  - zh: 大餘
  - en: §104 Greater Remainder 47.
- cullen:chunk:142 §117 Proc. 3.36 p.194-195 [single_zh_single_en]
  - zh: 大餘
  - en: §117 Greater Remainder 54.

### 日度法 ↔ Day and Du Factor [NUM].

Status: strong_candidate; overall: 0.8584; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:120 §96 Proc. 3.36 p.192 [single_zh_single_en]
  - zh: 日度法
  - en: §96 Day and Du Factor 17,308.
- cullen:chunk:133 §109 Proc. 3.36 p.194 [single_zh_single_en]
  - zh: 日度法
  - en: §109 Day and Du Factor 3516.
- cullen:chunk:147 §122 Proc. 3.36 p.195 [single_zh_single_en]
  - zh: 日度法
  - en: §122 Day and Du Factor 36,384.

### 小餘 ↔ Lesser Remainder [NUM].

Status: strong_candidate; overall: 0.852; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:129 §105 Proc. 3.36 p.193 [single_zh_single_en]
  - zh: 小餘
  - en: §105 Lesser Remainder 754.
- cullen:chunk:143 §118 Proc. 3.36 p.194-195 [single_zh_single_en]
  - zh: 小餘
  - en: §118 Lesser Remainder 348.
- cullen:chunk:156 §131 Proc. 3.36 p.195-196 [single_zh_single_en]
  - zh: 小餘
  - en: §131 Lesser Remainder 731.

### 月法 ↔ Lunation Factor [NUM].

Status: strong_candidate; overall: 0.8503; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:114 §90 Proc. 3.36 p.190 [single_zh_single_en]
  - zh: 月法
  - en: §90 Lunation Factor 82,213.
- cullen:chunk:127 §103 Proc. 3.36 p.193 [single_zh_single_en]
  - zh: 月法
  - en: §103 Lunation Factor 16,701.
- cullen:chunk:141 §116 Proc. 3.36 p.194 [single_zh_single_en]
  - zh: 月法
  - en: §116 Lunation Factor 172,824.

### 積度 ↔ Accumulated Du [NUM].

Status: strong_candidate; overall: 0.8356; usable for: glossary_candidate, concept_inventory, variable_label_candidate

- cullen:chunk:121 §97 Proc. 3.36 p.192-193 [single_zh_single_en]
  - zh: 積度
  - en: §97 Accumulated Du 33.
- cullen:chunk:148 §123 Proc. 3.36 p.195 [single_zh_single_en]
  - zh: 積度
  - en: §123 Accumulated Du 12.
- cullen:chunk:161 §136 Proc. 3.36 p.196 [single_zh_single_en]
  - zh: 積度
  - en: §136 Accumulated Du 292.

