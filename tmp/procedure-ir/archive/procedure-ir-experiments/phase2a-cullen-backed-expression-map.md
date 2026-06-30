# Phase 2A-2 Cullen-Backed Expression Map

- Scope: Proc. 2.3, Proc. 2.4, Proc. 2.5, Proc. 2.9, Proc. 3.2
- Input restriction respected: phase2a pilot + Cullen-led reconstruction + phase1 baseline only
- Original Phase 2A pilot remains unchanged

## Proc. 2.3

### Proc.2.3.step.1

- backup_level: A_worked_example_formula
- operation_id: multiply_accumulated_months_by_lunation_factor
- formalization_status: formalizable_now
- source_phrase: 以月法乘积月
- cullen_chinese_phrase: 以月法乘積月
- cullen_translation_phrase: Multiply Accumulated Months by Lunation Factor [2392].
- cullen_commentary_phrase: Here the aim is to predict the cyclical day on which falls the conjunction of the first day of the first month of the Celestial year.
- cullen_worked_example: 24 × 2392 = 57,408.
- formal_expression: product = 积月 × 月法
- validation_rule: Check Cullen worked example: when 积月 = 24, product must equal 57,408.

### Proc.2.3.step.2

- backup_level: A_worked_example_formula
- operation_id: divide_product_by_day_factor_to_get_accumulated_days_and_lesser_remainder
- formalization_status: formalizable_now
- source_phrase: 盈日法得一，名曰积日，不盈者名曰小馀
- cullen_chinese_phrase: 盈日法得一，名曰積日，不盈者名曰小餘
- cullen_translation_phrase: Count 1 for each filling of the Day Factor [81], and the name of this is Accumulated Days. What does not fill is called the Lesser Remainder.
- cullen_commentary_phrase: 57,408/81 = 708 remainder 60.
- cullen_worked_example: 57,408/81 = 708 remainder 60.
- formal_expression: 积日 = floor(product / 日法); 小馀 = product mod 日法
- validation_rule: Check Cullen worked example: floor(57,408 / 81) = 708 and 57,408 mod 81 = 60.

### Proc.2.3.step.3

- backup_level: B_commentary_explicit_relation
- operation_id: classify_long_month_from_lesser_remainder_threshold
- formalization_status: formalizable_with_caveat
- source_phrase: 小馀三十八以上，其月大
- cullen_chinese_phrase: 小餘三十八以上，其月大
- cullen_translation_phrase: If the Lesser Remainder is 38 or above, the month is long.
- cullen_commentary_phrase: Since 38 + 43 = 81 it is clear that if the Lesser Remainder at the start of this month is 43 or more, then a whole extra day will have to be counted before we get to the next conjunction.
- cullen_worked_example: none
- formal_expression: is_long_month = (小馀 >= 38)
- validation_rule: Evaluate the predicate only after 小馀 is resolved from the Day Factor quotient/remainder step.

Uncertainties:
- Cullen commentary explains the carry implication for later month advance, but not a separate standalone month-length algorithm beyond this threshold test.

### Proc.2.3.step.4

- backup_level: A_worked_example_formula
- operation_id: cast_out_sixty_from_accumulated_days_to_get_greater_remainder
- formalization_status: formalizable_now
- source_phrase: 积日盈六十，除之，不盈者名曰大馀
- cullen_chinese_phrase: 積日盈六十，除之，不盈者名曰大餘
- cullen_translation_phrase: If the Accumulated Days fills 60, cast it out. What does not fill is called the Greater Remainder.
- cullen_commentary_phrase: 708/60 = 11 remainder 48. So 11 complete 60-day cycles and 48 odd days have elapsed since the start of the current concordance, and thus 48 is the Greater Remainder.
- cullen_worked_example: 708/60 = 11 remainder 48.
- formal_expression: 大馀 = 积日 mod 60
- validation_rule: Check Cullen worked example: 708 mod 60 = 48.

### Proc.2.3.step.5

- backup_level: B_commentary_explicit_relation
- operation_id: count_outside_from_concordance_head_to_conjunction_day
- formalization_status: formalizable_with_caveat
- source_phrase: 数从统首日起，算外，则朔日也
- cullen_chinese_phrase: 數從統首日起，算外，則朔日也
- cullen_translation_phrase: Count starting from the Concordance Head, and outside the count is the day of conjunction.
- cullen_commentary_phrase: If the first day is number 1 and we are to count 48, the day 'outside the count', the day of conjunction, is number 49.
- cullen_worked_example: none
- formal_expression: 朔日_index = ((统首日起点_index - 1) + 大馀) mod 60 + 1
- validation_rule: Only validate when a concrete cyclical-day index for 统首日 is supplied; use Cullen's 48 -> 49 counting explanation as the convention check.

Uncertainties:
- This remains a counting convention tied to a cyclical-day index, not a pure arithmetic step recoverable from the source phrase alone.

### Proc.2.3.step.6

- backup_level: B_commentary_explicit_relation
- operation_id: advance_remainder_pair_to_next_month
- formalization_status: formalizable_now
- source_phrase: 求其次月，加大馀二十九，小馀四十三
- cullen_chinese_phrase: 求其次月，加大餘二十九，小餘四十三
- cullen_translation_phrase: To seek the next month, add to the Greater Remainder 29, and to the Lesser Remainder 43.
- cullen_commentary_phrase: Since the mean interval between conjunctions will be 2392/81 days = 29 + 43/81 days it is clear that 29 and 43 are the amounts we must add to the Greater and Lesser Remainders to get to the next conjunction.
- cullen_worked_example: none
- formal_expression: next_month_greater_raw = 大馀 + 29; next_month_lesser_raw = 小馀 + 43
- validation_rule: Validate the 29 + 43/81 decomposition against Cullen's commentary relation 2392/81 = 29 + 43/81.

### Proc.2.3.step.7

- backup_level: B_commentary_explicit_relation
- operation_id: carry_lesser_remainder_into_greater_remainder_for_next_month
- formalization_status: formalizable_with_caveat
- source_phrase: 小馀盈日法得一，从大馀，数除如法
- cullen_chinese_phrase: 小餘盈日法得一，從大餘，數除如法
- cullen_translation_phrase: Count one for each time the Lesser Remainder fills the Day Factor [81], and let it go with the Greater Remainder. Then count and cast out according to the method.
- cullen_commentary_phrase: If the Lesser Remainder at the start of this month is 43 or more, then a whole extra day will have to be counted before we get to the next conjunction.
- cullen_worked_example: none
- formal_expression: next_month_greater = next_month_greater_raw + floor(next_month_lesser_raw / 日法); next_month_lesser = next_month_lesser_raw mod 日法
- validation_rule: Validate carry behavior only through the Day Factor division rule; do not collapse the later '数除如法' convention into this arithmetic substep.

Uncertainties:
- The final phrase 数除如法 still points back to an external counting convention, so only the carry arithmetic is formalized here.

### Proc.2.3.step.8

- backup_level: A_worked_example_formula
- operation_id: advance_remainder_pair_to_first_quarter
- formalization_status: formalizable_now
- source_phrase: 求弦，加大馀七，小馀三十一
- cullen_chinese_phrase: 求弦，加大餘七，小餘三十一
- cullen_translation_phrase: To seek the first quarter, add to the Greater Remainder 7, and to the Lesser Remainder 31.
- cullen_commentary_phrase: 2392/4 = 598 and 598/81 = 7 remainder 31.
- cullen_worked_example: 2392/4 = 598 and 598/81 = 7 remainder 31.
- formal_expression: first_quarter_greater_raw = 大馀 + 7; first_quarter_lesser_raw = 小馀 + 31
- validation_rule: Check Cullen worked example: 2392/4 = 598 and 598 = 7 × 81 + 31.

### Proc.2.3.step.9

- backup_level: C_translation_explicit_operation
- operation_id: double_first_quarter_increment_to_get_full_moon_increment
- formalization_status: formalizable_now
- source_phrase: 求望，倍弦
- cullen_chinese_phrase: 求望，倍弦
- cullen_translation_phrase: To seek full moon, double [the amounts] for the first quarter.
- cullen_commentary_phrase: It is assumed that the lunar phases are equally spaced.
- cullen_worked_example: none
- formal_expression: full_moon_increment = 2 × first_quarter_increment
- validation_rule: Validate only after the first-quarter increment pair is resolved; the doubling rule itself is explicit in Cullen's translation.

Uncertainties:
- The source does not restate whether both greater and lesser components are doubled, but Cullen's translation supports doubling the first-quarter amounts as a pair.

## Proc. 2.4

### Proc.2.4.step.1

- backup_level: A_worked_example_formula
- operation_id: rescale_intercalation_surplus_by_twelve
- formalization_status: formalizable_now
- source_phrase: 以十二乘闰馀
- cullen_chinese_phrase: 以十二乘閏餘
- cullen_translation_phrase: Multiply the Intercalation Surplus by 12.
- cullen_commentary_phrase: The initial multiplication by 12 is needed to convert the Intercalation Surplus to the correct scale, since 12 × 19 = 228.
- cullen_worked_example: 14 × 12 = 168.
- formal_expression: rescaled_surplus = 闰馀 × 12
- validation_rule: Check Cullen worked example: when 闰馀 = 14, rescaled_surplus = 168.

### Proc.2.4.step.2a

- backup_level: D_source_only_needs_human_review
- operation_id: source_increment_ten_discrepancy_before_medial_qi_fill
- formalization_status: not_formalizable_yet
- source_phrase: 加十得一
- cullen_chinese_phrase: 加(十)[七]得一
- cullen_translation_phrase: For an addition of seven, obtain 1, [until you] fill Rule Medial [Qi] [228].
- cullen_commentary_phrase: We then find how many times we need to add 7 to this until we reach a total exceeding 228.
- cullen_worked_example: 14 × 12 = 168 and (228 − 168) / 7 = 8, remainder 4.
- formal_expression: null
- validation_rule: Do not validate as a deterministic formula until the source/Cullen discrepancy is resolved by human review.

Uncertainties:
- The source text says 加十, while Cullen's reconstructed Chinese and translation support 加七; this entry preserves the discrepancy without normalization.

### Proc.2.4.step.2b

- backup_level: A_worked_example_formula
- operation_id: compute_number_of_sevens_needed_to_cross_rule_medial_qi_cycle
- formalization_status: formalizable_with_caveat
- source_phrase: 加十得一
- cullen_chinese_phrase: 加(十)[七]得一
- cullen_translation_phrase: For an addition of seven, obtain 1, [until you] fill Rule Medial [Qi] [228].
- cullen_commentary_phrase: If we start counting with winter solstice taken as #1, and if (say) 3 additions of 7 are required, the 4th qi will be the one 'outside the count' that has shifted onto or past the next mean conjunction.
- cullen_worked_example: (228 − 168) / 7 = 8, remainder 4.
- formal_expression: steps_before_overflow = floor((章中 − rescaled_surplus) / 7)
- validation_rule: Check Cullen worked example: floor((228 − 168) / 7) = 8 with remainder 4.

Uncertainties:
- This formalization is Cullen-backed but cannot overwrite the source's 加十 reading.

### Proc.2.4.step.3

- backup_level: B_commentary_explicit_relation
- operation_id: map_overflow_step_count_to_medial_qi_outside_the_count
- formalization_status: formalizable_with_caveat
- source_phrase: 盈章中，数所得，起冬至，算外，则中至终闰盈
- cullen_chinese_phrase: 盈章中，數所得，起冬至，算外，則中至終閏盈
- cullen_translation_phrase: With the number you get, start counting off from winter solstice. Outside the count, then the Medial [Qi] has reached the conclusion of the filling of the Intercalation [Surplus].
- cullen_commentary_phrase: If 3 additions of 7 are required, the 4th qi will be the one 'outside the count' that has shifted onto or past the next mean conjunction.
- cullen_worked_example: none
- formal_expression: overflow_qi_index = steps_before_overflow + 1
- validation_rule: Validate only as an ordinal counting convention: if 3 additions are required, the 4th qi is outside the count.

Uncertainties:
- This step formalizes only Cullen's ordinal explanation, not a full calendrical date computation.

### Proc.2.4.step.4

- backup_level: B_commentary_explicit_relation
- operation_id: classify_preceding_month_as_intercalary_from_medial_qi_timing
- formalization_status: formalizable_with_caveat
- source_phrase: 中气在朔若二日，则前月闰也
- cullen_chinese_phrase: 中氣在朔若二日，則前月閏也
- cullen_translation_phrase: The Medial [Qi] is on the conjunction or the second day, so the preceding month is intercalary.
- cullen_commentary_phrase: This qi could fall on the day after the day of the conjunction, if the conjunction falls more than 0.22 day after midnight on the first day of the month.
- cullen_worked_example: none
- formal_expression: preceding_month_is_intercalary = (medial_qi_day == conjunction_day) or (medial_qi_day == conjunction_day + 1)
- validation_rule: Validate only when conjunction-day and medial-qi day placements are both available; do not infer them from this line alone.

Uncertainties:
- This remains dependent on calendrical placement data outside the source phrase itself.

## Proc. 2.5

### Proc.2.5.step.1

- backup_level: B_commentary_explicit_relation
- operation_id: multiply_years_into_concordance_by_reckoning_surplus
- formalization_status: formalizable_now
- source_phrase: 以算馀乘入统岁数
- cullen_chinese_phrase: 以(算)[策]餘乘(人)[入]統歲數
- cullen_translation_phrase: By Reckoning Surplus [8080] multiply the number of years into the Concordance.
- cullen_commentary_phrase: The number 8080 is the number of days by which the days in a Concordance of 1539 years exceed a multiple of 360.
- cullen_worked_example: none
- formal_expression: winter_solstice_product = 入统岁数 × 算馀
- validation_rule: Validate only after the Reckoning Surplus constant is accepted from Cullen's commentary.

Uncertainties:
- Cullen gives the constant's meaning but not a worked numerical example for this specific procedure.

### Proc.2.5.step.2

- backup_level: C_translation_explicit_operation
- operation_id: divide_winter_solstice_product_by_concordance_factor
- formalization_status: formalizable_with_caveat
- source_phrase: 盈统法得一，名曰大馀，不盈者名曰小馀
- cullen_chinese_phrase: 盈統法得一，名曰大餘，不盈者名曰小餘
- cullen_translation_phrase: Obtaining 1 for each filling of the Concordance Factor [1539]. [This] is called the Greater Remainder. What does not fill is called the Lesser Remainder.
- cullen_commentary_phrase: The rest follows.
- cullen_worked_example: none
- formal_expression: 大馀 = floor(winter_solstice_product / 统法); 小馀 = winter_solstice_product mod 统法
- validation_rule: Validate quotient/remainder only after the multiplier step is accepted; no Cullen worked example is available in the allowed inputs.

Uncertainties:
- The translation is explicit about quotient/remainder behavior, but the allowed inputs do not include a worked numerical example for this step.

### Proc.2.5.step.3

- backup_level: C_translation_explicit_operation
- operation_id: recover_winter_solstice_day_by_prior_counting_method
- formalization_status: needs_human_review
- source_phrase: 除数如法，则所求冬至日也
- cullen_chinese_phrase: 除數如法，則所求冬至日也
- cullen_translation_phrase: Cast out and count off according to the method, then that is the winter solstice day of the year sought.
- cullen_commentary_phrase: The rest follows.
- cullen_worked_example: none
- formal_expression: null
- validation_rule: Do not run arithmetic validation until the prior counting convention referenced by 如法 is explicitly grounded.

Uncertainties:
- 除数如法 points to an external convention not formalized by Cullen in the allowed input scope.

## Proc. 2.9

### Proc.2.9.step.1

- backup_level: B_commentary_explicit_relation
- operation_id: convert_month_lesser_remainder_to_du_fraction_scale
- formalization_status: formalizable_now
- source_phrase: 以章岁乘月小馀
- cullen_chinese_phrase: 以章歲乘月小餘
- cullen_translation_phrase: Multiply the Lesser Remainder of the month by Rule Years [19].
- cullen_commentary_phrase: Multiplying this by 19 converts to a scale of 19 × 81 = 1539, the Concordance Factor, used for fractions of a du.
- cullen_worked_example: none
- formal_expression: midnight_offset_parts = 月小馀 × 章岁
- validation_rule: Check the scale-conversion relation 19 × 81 = 1539 before using this offset in subtraction.

### Proc.2.9.step.2

- backup_level: B_commentary_explicit_relation
- operation_id: subtract_midnight_offset_from_conjunction_mark_point
- formalization_status: formalizable_with_caveat
- source_phrase: 以减合晨度
- cullen_chinese_phrase: 以減合晨度
- cullen_translation_phrase: And by that diminish the du of the mark-point for the conjunction.
- cullen_commentary_phrase: Subtracting this amount from the du for the conjunction gives the du for the preceding midnight.
- cullen_worked_example: none
- formal_expression: 日夜半所在度 = 合晨度 − (midnight_offset_parts / 统法)
- validation_rule: Validate only on a common du/part scale; do not collapse lodge indexing into this expression.

Uncertainties:
- This formalizes the du/part subtraction, not the full lodge-plus-du representation.

### Proc.2.9.step.3

- backup_level: C_translation_explicit_operation
- operation_id: borrow_one_whole_du_into_parts_before_subtraction
- formalization_status: formalizable_with_caveat
- source_phrase: 小馀不足者，破全度
- cullen_chinese_phrase: 小餘不足者，破全度
- cullen_translation_phrase: If the Lesser Remainder is insufficient, break a whole du [into parts].
- cullen_commentary_phrase: The Lesser Remainder for a month is a fraction of a day at a scale of 81... used for fractions of a du.
- cullen_worked_example: none
- formal_expression: if midnight_offset_parts > conjunction_fractional_parts then borrow_du = 1 and conjunction_fractional_parts = conjunction_fractional_parts + 统法
- validation_rule: Validate only after the conjunction mark-point is represented on the same 1539-part scale.

Uncertainties:
- The source does not spell out the exact bookkeeping of the borrowed whole du, so the expression captures only the necessary borrow condition.

## Proc. 3.2

### Proc.3.2.step.1

- backup_level: B_commentary_explicit_relation
- operation_id: cast_out_whole_origins_from_accumulated_years
- formalization_status: formalizable_now
- source_phrase: 以元法除去上元
- cullen_chinese_phrase: 以元法除去上元
- cullen_translation_phrase: Cast out Origin Factor [4560] from accumulated years from Grand Origin.
- cullen_commentary_phrase: First we cast out whole Origins, since all relevant conditions repeat in an Origin.
- cullen_worked_example: none
- formal_expression: origin_remainder = 上元积年 mod 元法
- validation_rule: Validate only as the first nested cycle cast-out in the benchmark procedure.

### Proc.3.2.step.2

- backup_level: B_commentary_explicit_relation
- operation_id: cast_out_era_factor_from_origin_remainder
- formalization_status: formalizable_now
- source_phrase: 其馀以纪法除之
- cullen_chinese_phrase: 其餘以紀法除之
- cullen_translation_phrase: Cast out Era Factor [1520] from the remainder.
- cullen_commentary_phrase: Since an Origin is three Eras, we then establish which of the three Eras of the current Origin we are in.
- cullen_worked_example: none
- formal_expression: entered_era_index = floor(origin_remainder / 纪法); 入纪年数 = origin_remainder mod 纪法
- validation_rule: Validate only as a nested quotient/remainder relation; do not yet convert the quotient into table lookup behavior.

Uncertainties:
- The quotient's conversion to a named Era sequence is intentionally left to a later benchmark-only convention layer.

### Proc.3.2.step.3

- backup_level: C_translation_explicit_operation
- operation_id: cast_out_obscuration_factor_from_years_into_era
- formalization_status: formalizable_now
- source_phrase: 以蔀法除之
- cullen_chinese_phrase: 以蔀法除之
- cullen_translation_phrase: Cast out Obscuration Factor [76] from it.
- cullen_commentary_phrase: Each column has 20 rows, containing the sexagenary numbers of the first year of each of the 20 Obscurations that make up the relevant Era.
- cullen_worked_example: none
- formal_expression: entered_obscuration_index = floor(入纪年数 / 蔀法); 入蔀年数 = 入纪年数 mod 蔀法
- validation_rule: Validate only as the third nested quotient/remainder relation in the benchmark procedure.

### Proc.3.2.step.4

- backup_level: B_commentary_explicit_relation
- operation_id: map_era_quotient_to_heaven_era_counting_convention
- formalization_status: needs_human_review
- source_phrase: 所得数从天纪，算外则所入纪也
- cullen_chinese_phrase: 所得數從天紀，筭外則所入紀也
- cullen_translation_phrase: Number from the Heaven Era by how many you obtain, then outside the count is the Era you are entering.
- cullen_commentary_phrase: That tells us which of the three main columns ... we should be using.
- cullen_worked_example: none
- formal_expression: null
- validation_rule: Benchmark only: do not arithmetic-validate until the Heaven/Earth/Man table convention is encoded separately.

Uncertainties:
- This is a named-sequence/table convention, not a standalone arithmetic relation under the current pilot scope.

### Proc.3.2.step.5

- backup_level: C_translation_explicit_operation
- operation_id: map_obscuration_quotient_to_jiazi_obscuration_counting_convention
- formalization_status: needs_human_review
- source_phrase: 所得数从甲子蔀起，算外，所入蔀也
- cullen_chinese_phrase: 所得數從甲子蔀起，筭外，[所入蔀也]
- cullen_translation_phrase: Number from the jiazi.1 Obscuration by how many you obtain, then outside your count, that is the Obscuration which is being entered.
- cullen_commentary_phrase: Each column has 20 rows, containing the sexagenary numbers of the first year of each of the 20 Obscurations that make up the relevant Era.
- cullen_worked_example: none
- formal_expression: null
- validation_rule: Benchmark only: do not arithmetic-validate until the row/column lookup convention is encoded separately.

Uncertainties:
- This remains a table-mediated naming step rather than a direct arithmetic expression.

### Proc.3.2.step.6

- backup_level: B_commentary_explicit_relation
- operation_id: count_forward_from_obscuration_entry_to_target_year_name
- formalization_status: needs_human_review
- source_phrase: 岁名命之，算上，即所求年太岁所在
- cullen_chinese_phrase: 歲名命之，筭上，即所求年太歲所在
- cullen_translation_phrase: Label that by the year-name ... then above the count, that is where the Great Year is in the year sought.
- cullen_commentary_phrase: We do this by finding the sexagenary number of the first year of the current Obscuration, and then counting forward.
- cullen_worked_example: none
- formal_expression: null
- validation_rule: Keep as benchmark-only human review until the Table 3.1 lookup and counting-above convention are formalized separately.

Uncertainties:
- This step depends on a table-driven sequence and should not be generalized from the Sifen benchmark to Santong examples.

