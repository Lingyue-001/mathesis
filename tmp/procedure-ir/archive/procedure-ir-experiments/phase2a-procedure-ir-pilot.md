# Phase 2A Procedure IR Pilot

- Scope: Proc. 2.3 / 2.4 / 2.5 / 2.9 / 3.2 only
- Generated from Phase 1 confirmed source spans plus Cullen-led reconstruction outputs
- Writeback status: all items remain `do_not_writeback: true`

## Proc. 2.3 (pilot_positive_example)

- source_span_id: santong:L109
- procedure_title: 推正月朔
- confidence: high
- do_not_writeback: true
- procedure_goal: Predict the conjunction day of the standard month, then derive the next month's conjunction and the first-quarter/full-moon offsets from the same remainder pair.

### Source Text

推正月朔，以月法乘积月，盈日法得一，名曰积日，不盈者名曰小馀。小馀三十八以上，其月大。积日盈六十，除之，不盈者名曰大馀。数从统首日起，算外，则朔日也。求其次月，加大馀二十九，小馀四十三。小馀盈日法得一，从大馀，数除如法。求弦，加大馀七，小馀三十一。求望，倍弦。

### Cullen Support

- chinese_quote: 推正月朔， 以月法乘積月， 盈日法 得一， 名曰積日，不盈者名曰小餘 小餘 三十八以上， 其月大 積日盈六十， 除之， 不盈者名曰大餘 數從統首日起， 算 外， 則朔日也 求其次月， 加大餘二十九， 小餘四十三 小餘盈日法得一 從大 餘， 數除如法 求弦， 加大餘七， 小餘三十一 求望，倍弦
- english_translation_excerpt: To predict the conjunction of the Standard Month: §175 Multiply Accumulated Months by Lunation Factor [2392]. Count 1 for each filling of the Day Factor [81], and the name of this is Accumulated Days. What does not fill is called the Lesser Remainder. If the Lesser Remainder is 38 or above, the month is long. If the Accumulated Days fills 60, cast it out. What does not fill is called the Greater Remainder. Count starting from the Concordance Head, and outside the count is the day of conjunction. To seek the next month, add to the Greater Remainder 29, and to the Lesser Remainder 43. Count one for each time the Lesser Remainder fills the Day Factor [81], and let it go with the Greater Remainder. Then count and cast out according to the method. To seek the first quarter, add to the Greater Remainder 7, and to the Lesser Remainder 31. To seek full moon, double [the amounts] for the first quarter.
- commentary_excerpt: The example states that 24 × 2392 = 57,408 and 57,408/81 = 708 remainder 60, explaining why 29 and 43 advance the next conjunction and why 7 and 31 give the first-quarter increment.
- anchor_quality_tier: A_ready_for_phase2
- source_alignment: inferred_source_alignment
- note: Phase 1 reconstruction matches santong:L109 directly and preserves the quoted Chinese block.

### Inputs

- 积月 | source_text | Primary variable multiplied at the start.
- 统首日 | source_text | Base point for counting outside to the conjunction day.

### Constants

- 月法 | 2392 | Cullen translation | Lunation Factor used in the opening multiplication.
- 日法 | 81 | Cullen translation | Day Factor used for quotient/remainder.
- 小馀 long-month threshold | 38 | source_text + Cullen translation | Threshold for declaring a long month.
- sexagenary cycle | 60 | source_text + Cullen translation | Accumulated Days are cast out by 60.
- next-month increment | [29,43] | source_text + Cullen translation | Added to Greater/Lesser Remainders.
- first-quarter increment | [7,31] | source_text + Cullen translation | Added to Greater/Lesser Remainders.

### Operations

- multiply | source_text + Cullen translation | 以月法乘积月 / Multiply Accumulated Months by Lunation Factor [2392].
- count | Cullen translation | Count 1 for each filling of the Day Factor [81].
- cast out | source_text + Cullen translation | 积日盈六十，除之 / If the Accumulated Days fills 60, cast it out.
- count outside | source_text + Cullen translation | 数从统首日起，算外，则朔日也 / Count starting from the Concordance Head, and outside the count is the day of conjunction.
- add | source_text + Cullen translation | 加大馀二十九，小馀四十三；加大馀七，小馀三十一。
- double | source_text + Cullen translation | 求望，倍弦 / To seek full moon, double [the amounts] for the first quarter.

### Outputs

- 积日 | source_text + Cullen translation
- 小馀 | source_text + Cullen translation
- 大馀 | source_text + Cullen translation
- 朔日 | source_text + Cullen translation
- 次月 remainder pair | source_text + Cullen translation
- 弦 remainder pair | source_text + Cullen translation
- 望 remainder pair | source_text + Cullen translation

### Ordered Steps

1. Multiply 积月 by 月法 to produce 积日 and a 小馀 under 日法.
2. If 小馀 is 38 or above, mark the month as long.
3. If 积日 fills 60, cast out 60 and retain 大馀.
4. Count from 统首日 and take the day outside the count as 朔日.
5. For the next month, add 29 to 大馀 and 43 to 小馀, then carry again by 日法 and cast out as before.
6. For the first quarter, add 7 to 大馀 and 31 to 小馀; for full moon, double the first-quarter increment.

### Arithmetic Validation Plan

- Verify that the pilot constants reproduce Cullen's example structure: 积月 × 2392, then divide by 81 to get quotient/remainder.
- Check that the long-month threshold is applied only to 小馀 and not to the 60-day cast-out step.
- Check that the 29/43 and 7/31 updates preserve the text order and operate on the Greater/Lesser Remainder pair rather than on a modernized timestamp.

### Uncertainties

- The source span compresses several derived subprocedures into one line, so the pilot keeps them in one item rather than splitting them into separate IR records.
- This pilot does not resolve whether later Phase 2 should separate conjunction, next-month, quarter, and full-moon branches into sub-items.

## Proc. 2.4 (pilot_positive_example)

- source_span_id: santong:L110
- procedure_title: 推闰馀所在
- confidence: needs_human_review
- do_not_writeback: true
- procedure_goal: Locate the medial qi at which the Intercalation Surplus completes, then judge whether the preceding month is intercalary.

### Source Text

推闰馀所在，以十二乘闰馀，加十得一。盈章中，数所得，起冬至，算外，则中至终闰盈。中气在朔若二日，则前月闰也。

### Cullen Support

- chinese_quote: 推閏餘所在， 以十二乘閏餘， 加(十)[七]得一 盈章中， 數所得，起冬至 算 外， 則中至終閏盈 中氣在朔若二日， 則前月閏也
- english_translation_excerpt: To seek where the Intercalation Surplus is located: §176 Multiply the Intercalation Surplus by 12. For an addition of seven, obtain 1, [until you] fill Rule Medial [Qi] [228]. With the number you get, start counting off from winter solstice. Outside the count, then the Medial [Qi] has reached the conclusion of the filling of the Intercalation [Surplus]. The Medial [Qi] is on the conjunction or the second day, so the preceding month is intercalary.
- commentary_excerpt: Cullen explains that there are 12 medial qi in a year, so the Intercalation Surplus in nineteenth-of-a-lunation units must first be rescaled to 228, then advanced by repeated additions of 7 until the total exceeds the medial-qi cycle.
- anchor_quality_tier: D_needs_human_review
- source_alignment: phase1_confirmed_mapping_override
- note: The pilot follows the confirmed Proc. 2.4 -> santong:L110 mapping without changing Phase 1 reconstruction outputs.

### Inputs

- 闰馀 | source_text + Cullen translation | Primary surplus being located.
- 冬至 | source_text + Cullen translation | Starting point for counting outside.

### Constants

- multiplier | 12 | source_text + Cullen translation + Cullen commentary | Rescales 闰馀 from nineteenth-of-a-lunation units.
- increment after multiplication | {"source_text":10,"cullen_reconstruction":7} | source_text + Cullen translation | This is the key boundary discrepancy and is not normalized away in the pilot.
- 章中 / Rule Medial [Qi] | 228 | Cullen translation + Cullen commentary | Filling threshold for the repeated advance.

### Operations

- multiply | source_text + Cullen translation | 以十二乘闰馀 / Multiply the Intercalation Surplus by 12.
- add | source_text + Cullen translation | 加十得一 vs. Cullen's 加七得一.
- count | source_text + Cullen translation | 盈章中，数所得 / obtain counts until filling Rule Medial [Qi] [228].
- count outside | source_text + Cullen translation | 起冬至，算外 / start from winter solstice; outside the count...
- classify | source_text + Cullen translation | 中气在朔若二日，则前月闰也 / if the medial qi is on conjunction or day two, the preceding month is intercalary.

### Outputs

- 中至终闰盈的中气位置 | source_text + Cullen translation
- 前月是否为闰月 | source_text + Cullen translation

### Ordered Steps

1. Multiply 闰馀 by 12.
2. Advance the result by the stated increment until 章中 is filled, recording how many advances are obtained.
3. Count from winter solstice and take the qi outside the count as the qi where the intercalation surplus completes.
4. If that medial qi falls on conjunction day or day two, mark the preceding month as intercalary.

### Arithmetic Validation Plan

- Validate the unit conversion logic Cullen states explicitly: 12 × 19 = 228, so the multiplier must be preserving the commentary's rescaling argument.
- Keep the source's 加十 and Cullen's 加七 side by side and verify later by page-level evidence rather than silently choosing one.
- Test the counting rule only as an ordered procedure over qi positions; do not yet promote it into a finalized calendar-month writeback rule.

### Uncertainties

- The source span reads 加十得一, while the Phase 1 Cullen reconstruction preserves the emended reading 加(十)[七]得一.
- Current automated alignment has not closed a direct anchor, so this pilot relies on the confirmed Phase 1 mapping rather than on existing bound claims.
- The exact operational meaning of 盈章中 and whether it is best modeled as repeated addition or quotient/remainder remains for human review.

## Proc. 2.5 (pilot_positive_example)

- source_span_id: santong:L111
- procedure_title: 推冬至
- confidence: medium
- do_not_writeback: true
- procedure_goal: Predict the winter-solstice day for the target year from years into the concordance and the reckoning surplus.

### Source Text

推冬至，以算馀乘人统岁数，盈统法得一，名曰大馀，不盈者名曰小馀。除数如法，则所求冬至日也。

### Cullen Support

- chinese_quote: 推冬至， 以(算)[策]餘乘(人)[入]統歲數， 盈統法 得一， 名曰大餘， 不盈者名曰 小餘 除數如法， 則所求冬至日也
- english_translation_excerpt: To predict winter solstice: §177 By Reckoning Surplus [8080] multiply the number of years into the Concordance, obtaining 1 for each filling of the Concordance Factor [1539]. [This] is called the Greater Remainder. What does not fill is called the Lesser Remainder. Cast out and count off according to the method, then that is the winter solstice day of the year sought.
- commentary_excerpt: Cullen notes that 8080 is the number of days by which the days in a Concordance of 1539 years exceed a multiple of 360, and that the rest of the procedure follows the already established counting method.
- anchor_quality_tier: A_ready_for_phase2
- source_alignment: inferred_source_alignment
- note: Phase 1 reconstruction matches santong:L111 directly, but downstream executable parsing remains incomplete.

### Inputs

- 入统岁数 | source_text + Cullen translation | Years into the concordance.
- 算馀 | source_text + Cullen translation | Reckoning Surplus multiplier.

### Constants

- 算馀 / Reckoning Surplus | 8080 | Cullen translation + Cullen commentary | Introduced explicitly by Cullen.
- 统法 / Concordance Factor | 1539 | Cullen translation + Cullen commentary | Filling threshold for quotient/remainder.

### Operations

- multiply | source_text + Cullen translation | 以算馀乘人统岁数 / By Reckoning Surplus multiply the number of years into the Concordance.
- count | Cullen translation | obtaining 1 for each filling of the Concordance Factor [1539].
- cast out | source_text + Cullen translation | 除数如法 / Cast out and count off according to the method.
- count outside | Cullen translation | the winter solstice day is recovered by the same established counting method.

### Outputs

- 大馀 | source_text + Cullen translation
- 小馀 | source_text + Cullen translation
- 冬至日 | source_text + Cullen translation

### Ordered Steps

1. Multiply 入统岁数 by 算馀.
2. For each filling of 统法, obtain one unit and name the quotient 大馀.
3. Name the remainder 小馀.
4. Cast out and count according to the previously established method to get the winter-solstice day.

### Arithmetic Validation Plan

- Check Cullen's commentary equation linking 8080 and 1539 before trusting any later quotient/remainder implementation.
- Verify that the pilot keeps this procedure dependent on an earlier counting convention rather than inventing a new standalone day-cycle base.
- Confirm later whether the source variants 算/策 and 人/入 affect only orthography or also downstream normalization rules.

### Uncertainties

- The source phrase 除数如法 presupposes an earlier counting method not restated in this line, so the pilot does not over-specify the final count base.
- The Phase 1 executable step parse for this line is still mechanically rough, so the pilot relies on source text plus Cullen rather than on current step parsing.

## Proc. 2.9 (pilot_positive_example)

- source_span_id: santong:L116
- procedure_title: 推其日夜半所在星
- confidence: medium
- do_not_writeback: true
- procedure_goal: Predict the sun's midnight lodge/du position by backing off from the conjunction mark-point using the month's Lesser Remainder.

### Source Text

推其日夜半所在星，以章岁乘月小馀，以减合晨度。小馀不足者，破全度。

### Cullen Support

- chinese_quote: 推其日夜半所在星，以章歲乘月小餘，以減合晨度 小餘不足者，破全度
- english_translation_excerpt: To predict the star where the sun is located at midnight: §182 Multiply the Lesser Remainder of the month by Rule Years [19], and by that diminish the du of the mark-point for the conjunction. If the Lesser Remainder is insufficient, break a whole du [into parts].
- commentary_excerpt: Cullen explains that the month's Lesser Remainder is a day-fraction on an 81-part scale; multiplying by 19 converts it to the 1539-part scale used for fractions of a du, and subtraction from the conjunction mark-point gives the preceding midnight position.
- anchor_quality_tier: B_needs_source_alignment
- source_alignment: phase1_confirmed_mapping_override
- note: The pilot accepts the confirmed Proc. 2.9 -> santong:L116 mapping while keeping alignment uncertainty explicit.

### Inputs

- 月小馀 | source_text + Cullen translation | Fractional part of the month used as the time offset.
- 合晨度 | source_text + Cullen translation | Conjunction mark-point in du/parts.

### Constants

- 章岁 / Rule Years | 19 | source_text + Cullen translation + Cullen commentary | Multiplier for converting the time fraction.
- fractional day scale | 81 | Cullen commentary | Scale of the monthly Lesser Remainder.
- 统法 / Concordance Factor | 1539 | Cullen commentary | 19 × 81, used for du fractions.

### Operations

- multiply | source_text + Cullen translation | 以章岁乘月小馀 / Multiply the Lesser Remainder of the month by Rule Years [19].
- subtract | source_text + Cullen translation | 以减合晨度 / diminish the du of the mark-point for the conjunction.
- break whole degree into parts | source_text + Cullen translation | 小馀不足者，破全度 / If the Lesser Remainder is insufficient, break a whole du [into parts].

### Outputs

- 日夜半所在星/度 | source_text + Cullen translation

### Ordered Steps

1. Take the month's 小馀.
2. Multiply 小馀 by 章岁.
3. Subtract the resulting amount from 合晨度.
4. If the available remainder is insufficient for subtraction, break one whole degree into parts and continue the subtraction.

### Arithmetic Validation Plan

- Verify Cullen's scale-conversion explanation explicitly: 19 × 81 = 1539.
- Check that subtraction is modeled as backing off from conjunction toward the preceding midnight rather than as a forward advance.
- Keep the borrow step ('break a whole du into parts') explicit and separate from any later generalized borrow logic.

### Uncertainties

- The current Phase 1 anchor inventory does not bind this proc directly even though reconstruction matches santong:L116 well.
- The quoted translation in reconstruction trims immediately before Proc. 2.10, so this pilot must keep a strict boundary at the Proc. 2.9 procedural clause.
- The exact representation of 合晨度 as lodge+du+parts is left open in the pilot.

## Proc. 3.2 (benchmark_do_not_touch)

- source_span_id: sifen:L66
- procedure_title: 推入蔀術曰
- confidence: high
- do_not_writeback: true
- procedure_goal: Find the entered Era and Obscuration, then recover the sexagenary year-name position for the target year.

### Source Text

推入蔀術曰：以元法除去上元，其餘以紀法除之，所得數從天紀，筭外則所入紀也。不滿紀法者，入紀年數也。以蔀法除之，所得數從甲子蔀起，筭外，所入紀歲名命之，筭上，即所求年太歲所在。

### Cullen Support

- chinese_quote: 推入蔀術曰 160 以元法除去上元， 其餘以紀法除之， 所得數從天紀， 筭外則所入紀也 不滿 紀法者， 入紀年數也 以蔀法除之， 所得數從甲子蔀起 筭外 [所入蔀也 不滿蔀法者入蔀年數也各以]所入(紀)[蔀] 歲名命之， 筭上， 即所求年太歲 所在
- english_translation_excerpt: To find [the sexagenary year number of] entry into the Obscuration: §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how many you obtain, then outside the count is the Era you are entering. As for what does not amount to an Era Factor [1520], it is the number of years entered into the Era. Cast out Obscuration Factor [76] from it. Number from the jiazi.1 Obscuration by how many you obtain, then outside your count, [that is the Obscuration which is being entered. As for what does not amount to an Obscuration Factor [76], that is the number of years into the Obscuration.]
- commentary_excerpt: Cullen states that the aim is to find the sexagenary number of the year now beginning by first locating the current Era and Obscuration from repeating cycles, then counting forward from the row and column data supplied in Table 3.1.
- anchor_quality_tier: A_ready_for_phase2
- source_alignment: manual_or_high_confidence_source_alignment
- note: This is retained as the benchmark_do_not_touch item for Phase 2A, not a writeback target.

### Inputs

- 上元积年 | source_text + Cullen translation | Accumulated years from Grand Origin.

### Constants

- 元法 / Origin Factor | 4560 | source_text + Cullen translation | First cycle cast-out.
- 纪法 / Era Factor | 1520 | source_text + Cullen translation | Second cycle cast-out.
- 蔀法 / Obscuration Factor | 76 | source_text + Cullen translation | Third cycle cast-out.
- 天纪 | undefined | source_text + Cullen translation | Reference sequence for numbering the Era.
- 甲子蔀 | undefined | source_text + Cullen translation | Reference sequence for numbering the Obscuration.

### Operations

- cast out | source_text + Cullen translation | 以元法除去上元；其馀以纪法除之；以蔀法除之。
- number from | source_text + Cullen translation | 所得数从天纪；所得数从甲子蔀起。
- count outside | source_text + Cullen translation | 算外则所入纪也；算外，所入蔀也。
- label | source_text + Cullen translation | 所入...岁名命之。
- count above | source_text + Cullen translation | 算上，即所求年太岁所在。

### Outputs

- 所入纪 | source_text + Cullen translation
- 入纪年数 | source_text + Cullen translation
- 所入蔀 | source_text + Cullen translation
- 入蔀年数 | Cullen translation
- 所求年太岁所在 | source_text + Cullen translation

### Ordered Steps

1. Cast out whole Origins from accumulated years from Grand Origin.
2. Cast out Era Factor from the remainder to determine the entered Era and the years into that Era.
3. Cast out Obscuration Factor from the years-into-Era remainder to determine the entered Obscuration and the years into that Obscuration.
4. Label the entry point by the relevant year-name sequence.
5. Count upward from that labeled entry to locate the Great Year / year-name of the target year.

### Arithmetic Validation Plan

- Check the nested cycle structure explicitly: 4560 -> 1520 -> 76, without collapsing them into a single modulus.
- Validate later against Cullen's Table 3.1 usage only after the lookup-table representation is stable.
- Keep this item as a benchmark reference for Phase 2A and do not generalize its table-driven counting behavior to other procedures yet.

### Uncertainties

- Cullen notes that the end of the text is slightly garbled and depends on emendation, so the last labeling/count-above step remains text-critical.
- The source span is shorter than Cullen's reconstructed procedural explanation, so some suboutputs are only explicit in Cullen's translation/commentary.

