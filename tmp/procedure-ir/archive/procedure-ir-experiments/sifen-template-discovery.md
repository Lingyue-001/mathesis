# Sifen Template Discovery

> Template discovery only. This is not final extraction, gold data, or semantic naming. Meaning assignment happens later via LLM/human review.

## Summary

| Metric | Value |
| --- | --- |
| Translation units | 261 |
| Chinese clauses | 984 |
| English clauses | 824 |
| Chinese templates | 718 |
| English templates | 631 |
| Bilingual template pairs | 854 |
| Previously unnamed candidate pairs | 20 |
| Suspicious chunks | 98 |

## Top Chinese Templates

| Template | Count | Chunks | Examples |
| --- | --- | --- | --- |
| 以[OBJECT]乘之 | 17 | 17 | cullen:chunk:30:名之曰蔀. 以一歲日乘之; cullen:chunk:62:以章月乘之; cullen:chunk:63:以蔀日乘之 |
| [NUM]日 | 16 | 16 | cullen:chunk:200:二十五日; cullen:chunk:202:二十五日; cullen:chunk:214:十一日 |
| [NUM]日行[NUM]度 | 15 | 15 | cullen:chunk:198:五十八日行十一度; cullen:chunk:199:五十八日行九度; cullen:chunk:203:五十八日行九度 |
| 謂之[RESULT] | 15 | 4 | cullen:chunk:10:謂之合朔; cullen:chunk:10:謂之弦. 相與為衡; cullen:chunk:10:謂之望 |
| 置[OBJECT] | 12 | 12 | cullen:chunk:62:置入蔀年減一; cullen:chunk:63:置入蔀積月; cullen:chunk:65:置入蔀年減一 |
| 日行[NUM]分度之[NUM] | 10 | 10 | cullen:chunk:198:日行五十八分度之十一; cullen:chunk:201:日行七分度之一; cullen:chunk:212:日行二十三分度之十四 |
| 不盡為[RESULT] | 10 | 9 | cullen:chunk:68:不盡為沒餘; cullen:chunk:68:不盡為小餘; cullen:chunk:71:不盡為餘分 |
| 餘為[RESULT] | 10 | 7 | cullen:chunk:63:其餘為大餘; cullen:chunk:102:其餘為晝上水之數; cullen:chunk:102:餘為夜上水數 |
| 除伏逆 | 7 | 7 | cullen:chunk:206:除伏逆; cullen:chunk:220:除伏逆; cullen:chunk:232:除伏逆 |
| 留不行 | 7 | 7 | cullen:chunk:200:留不行; cullen:chunk:214:留不行; cullen:chunk:226:留不行 |
| 名為[RESULT] | 7 | 6 | cullen:chunk:62:名為積月; cullen:chunk:63:名為積日; cullen:chunk:68:名為積沒 |
| 行[NUM]度 | 7 | 7 | cullen:chunk:206:行二十八度; cullen:chunk:217:行四十八度; cullen:chunk:229:行六度 |
| 筭盡之外 | 6 | 6 | cullen:chunk:63:筭盡之外; cullen:chunk:65:筭盡之外; cullen:chunk:66:筭盡之外 |
| 而見東方 | 5 | 5 | cullen:chunk:197:而見東方; cullen:chunk:211:而見東方; cullen:chunk:224:而見東方 |
| 合積月 | 5 | 5 | cullen:chunk:112:合積月; cullen:chunk:125:合積月; cullen:chunk:139:合積月 |
| 日度法 | 5 | 5 | cullen:chunk:120:日度法; cullen:chunk:133:日度法; cullen:chunk:147:日度法 |
| 入月日 | 5 | 5 | cullen:chunk:118:入月日; cullen:chunk:131:入月日; cullen:chunk:145:入月日 |
| [OBJECT]除去之 | 5 | 4 | cullen:chunk:63:積日以六十 除去之; cullen:chunk:73:滿蔀日除去之; cullen:chunk:73:以宿次除去之 |
| 不滿為[RESULT] | 5 | 5 | cullen:chunk:62:不滿為閏餘; cullen:chunk:63:不滿為小餘; cullen:chunk:65:不滿為 小餘 |
| [NUM]日有[NUM]分 | 5 | 5 | cullen:chunk:208:三百九十八日有萬四千六百四十一分; cullen:chunk:222:七百七十九日有千八百七十二分; cullen:chunk:234:三百七十八日有二千一百六十三分 |
| 大餘 | 5 | 5 | cullen:chunk:115:大餘; cullen:chunk:128:大餘; cullen:chunk:142:大餘 |
| 日率 | 5 | 5 | cullen:chunk:111:日率; cullen:chunk:124:日率; cullen:chunk:138:日率 |
| 日餘 | 5 | 5 | cullen:chunk:44:日餘; cullen:chunk:119:日餘; cullen:chunk:132:日餘 |
| 小餘 | 5 | 5 | cullen:chunk:115:小餘; cullen:chunk:129:小餘; cullen:chunk:143:小餘 |
| 行[NUM]度[NUM]分 | 5 | 5 | cullen:chunk:196:行二度萬三千八百一十一分; cullen:chunk:207:行二度萬三千八百一十一分; cullen:chunk:245:行五十度二百八十一分 |
| 虛分 | 5 | 5 | cullen:chunk:117:虛分; cullen:chunk:130:虛分; cullen:chunk:144:虛分 |
| 月法 | 5 | 5 | cullen:chunk:114:月法; cullen:chunk:127:月法; cullen:chunk:141:月法 |
| 月餘 | 5 | 5 | cullen:chunk:113:月餘; cullen:chunk:126:月餘; cullen:chunk:140:月餘 |
| 周率 | 5 | 5 | cullen:chunk:110:周率; cullen:chunk:123:周率; cullen:chunk:137:周率 |
| [NUM]見[NUM]日 | 5 | 5 | cullen:chunk:206:一見三百六十六日; cullen:chunk:220:一見六百三十六日; cullen:chunk:244:一見二百四十六日 |

## Top English Templates

| Template | Count | Chunks | Examples |
| --- | --- | --- | --- |
| Cast out [OBJECT] | 34 | 23 | cullen:chunk:49:If the rates are cast out, one gets one eclipse per 5 20/23 months.; cullen:chunk:57:§43 Cast out Origin Factor [4560] from accumulated years from Grand Origin.; cullen:chunk:59:§44 From the distance from High Origin cast out Origin Coincidence [41,040]. |
| Add [OBJECT] | 22 | 18 | cullen:chunk:63:To find the conjunction day of the next month, add 29 to the Greater Remainder, and 499 to the Lesser Remainder.; cullen:chunk:67:§51 T ake the numbers for the Greater and Lesser Remainders for this month, and in each case add to the Greater Remainder 7 and the Lesser Remainder 359¾.; cullen:chunk:67:Count one if the Lesser Remainder fills Obscuration Months [940], and add that to the Greater Remainder. |
| Multiply [OBJECT] by [OBJECT] | 17 | 16 | cullen:chunk:62:Multiply by Rule Months [235].; cullen:chunk:63:Multiply by Obscura - tion Days [27,759].; cullen:chunk:64:§48 Multiply the years by Greater Circuits [343,335]. |
| Set out [OBJECT] | 16 | 16 | cullen:chunk:62:§46 Set out the years into the Obscuration and subtract one.; cullen:chunk:63:§47 Set out the Accumulated Months into the Obscuration.; cullen:chunk:65:set out the years entered into the Obscuration and subtract one. |
| called [RESULT] | 14 | 7 | cullen:chunk:10:When they share a position, that is called a conjunction.; cullen:chunk:10:When they are one part near and three parts distant, that is called a crescent.; cullen:chunk:10:When they are opposite one another, so that they divide Heaven down the middle, that is called opposition. |
| Subtract [OBJECT] | 10 | 9 | cullen:chunk:66:§50 Subtract the Intercalation Remainder from Rule Factor [19].; cullen:chunk:74:§57 By the Lesser Remainder for the conjunction subtract from the du and parts for the conjunction, then that is where the sun is located at midnight.; cullen:chunk:76:Subtract the remainder from the parts, then that is the du where the moon is located at midnight. |
| The remainder is [RESULT] | 8 | 7 | cullen:chunk:62:The remainder is the Intercalation Remainder.; cullen:chunk:63:The remainder is the Lesser Remainder.; cullen:chunk:63:The remainder is the Greater Remainder. |
| It delays and does not move for [NUM] days. | 6 | 6 | cullen:chunk:214:§186 It delays and does not move for 11 days.; cullen:chunk:226:§198 It delays and does not move for 33 days.; cullen:chunk:238:§209 It delays and does not move for 8 days. |
| Conjunction Accumulated Lunations: | 5 | 5 | cullen:chunk:112:§88 Conjunction Accumulated Lunations:; cullen:chunk:125:§101 Conjunction Accumulated Lunations:; cullen:chunk:139:§114 Conjunction Accumulated Lunations: |
| Days of entry into month [NUM]. | 5 | 5 | cullen:chunk:118:§94 Days of entry into month 15.; cullen:chunk:131:§107 Days of entry into month 12.; cullen:chunk:145:§120 Days of entry into month 24. |
| Lunation Remainder: | 5 | 5 | cullen:chunk:113:§89 Lunation Remainder:; cullen:chunk:126:§102 Lunation Remainder:; cullen:chunk:140:§115 Lunation Remainder: |
| Greater Remainder [NUM]. | 5 | 5 | cullen:chunk:115:§91 Greater Remainder 23.; cullen:chunk:128:§104 Greater Remainder 47.; cullen:chunk:142:§117 Greater Remainder 54. |
| Lesser Remainder [NUM]. | 5 | 5 | cullen:chunk:116:§92 Lesser Remainder 847.; cullen:chunk:129:§105 Lesser Remainder 754.; cullen:chunk:143:§118 Lesser Remainder 348. |
| Day and Du Factor [NUM]. | 5 | 5 | cullen:chunk:120:§96 Day and Du Factor 17,308.; cullen:chunk:133:§109 Day and Du Factor 3516.; cullen:chunk:147:§122 Day and Du Factor 36,384. |
| Lunation Factor [NUM]. | 5 | 5 | cullen:chunk:114:§90 Lunation Factor 82,213.; cullen:chunk:127:§103 Lunation Factor 16,701.; cullen:chunk:141:§116 Lunation Factor 172,824. |
| Accumulated Du [NUM]. | 5 | 5 | cullen:chunk:121:§97 Accumulated Du 33.; cullen:chunk:135:§110 Accumulated Du 49.; cullen:chunk:148:§123 Accumulated Du 12. |
| Day Remainder [NUM]. | 5 | 5 | cullen:chunk:119:§95 Day Remainder 14,641.; cullen:chunk:132:§108 Day Remainder 1872.; cullen:chunk:146:§121 Day Remainder 2163. |
| Du Remainder [NUM]. | 5 | 5 | cullen:chunk:122:§98 Du Remainder 10,314.; cullen:chunk:136:§111 Du Remainder 114.; cullen:chunk:149:§124 Du Remainder 29,451. |
| V oid Parts [NUM]. | 5 | 5 | cullen:chunk:117:§93 V oid Parts 93.; cullen:chunk:130:§106 V oid Parts 186.; cullen:chunk:144:§119 V oid Parts 592. |
| Casting out invisibility and retrogradation, one Appearance is [NUM] days, and it moves [NUM] du. | 4 | 4 | cullen:chunk:244:§214 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du.; cullen:chunk:255:§225 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du.; cullen:chunk:265:§235 Casting out invisibility and retrogradation, one Appearance is 32 days, and it moves 32 du. |
| Cycle Rate: | 4 | 4 | cullen:chunk:103:Cycle Rate:; cullen:chunk:110:§86 Cycle Rate:; cullen:chunk:123:§99 Cycle Rate: |
| Call this [RESULT] | 4 | 4 | cullen:chunk:62:Call this Accu- mulated Months.; cullen:chunk:68:Call this the Greater Remainder.; cullen:chunk:71:Call this Accumulated Du. |
| Method: | 4 | 4 | cullen:chunk:65:§49 Method:; cullen:chunk:77:§60 Method:; cullen:chunk:79:§62 Method: |
| Count one for each [OBJECT] filled | 3 | 3 | cullen:chunk:62:Count one for each Rule Factor [19] filled.; cullen:chunk:63:Count one for each Obscuration Months [940] filled.; cullen:chunk:65:Count one for each Medial [Qi] factor [32] filled. |
| Solar Rate: | 3 | 3 | cullen:chunk:111:§87 Solar Rate:; cullen:chunk:124:§100 Solar Rate:; cullen:chunk:138:§113 Solar Rate: |
| Obtain [RESULT] | 3 | 3 | cullen:chunk:69:Obtain 1 as the remainder fills Extinction Factor [7], then that is the Extinction after the Celestial Standard [conjunction].; cullen:chunk:79:Obtain 1 for each time Accumulated Parts fills Obscuration Factor [76], and by that increase the midnight du, then that is the du where the moon is located at dawn.; cullen:chunk:102:Obtain one ke for each time it fills its factor. |
| When it becomes visible in the east, it is [NUM] du and a bit behind the Sun. | 2 | 2 | cullen:chunk:197:§170 When it becomes visible in the east, it is 13 du and a bit behind the Sun.; cullen:chunk:211:§183 When it becomes visible in the east, it is 16 du and a bit behind the Sun. |
| It becomes invisible at dawn, and in [NUM] days it retreats [NUM] du. | 2 | 2 | cullen:chunk:235:§206 It becomes invisible at dawn, and in 5 days it retreats 4 du.; cullen:chunk:258:§228 It becomes invisible at dawn, and in 9 days it retreats 7 du. |
| It returns to direct motion for [NUM] days, and moves [NUM] du. | 2 | 2 | cullen:chunk:217:§189 It returns to direct motion for 92 days, and moves 48 du.; cullen:chunk:229:§201 It returns to direct motion for 86 days, and moves 6 du. |
| What is not exhausted is the Lesser Remainder. | 2 | 2 | cullen:chunk:68:What is not exhausted is the Lesser Remainder.; cullen:chunk:185:What is not exhausted is the Lesser Remainder. |

## Top Bilingual Template Pairs

| ZH template | EN template | Count | Chunks | Best strength | Preset |
| --- | --- | --- | --- | --- | --- |
| 以[OBJECT]乘之 | Multiply [OBJECT] by [OBJECT] | 7 | 7 | targeted_prespecified_same_unit | yes |
| 留不行 | It delays and does not move for [NUM] days. | 6 | 6 | near_ordinal_aligned | no |
| 大餘 | Greater Remainder [NUM]. | 5 | 5 | single_zh_single_en | no |
| 合積月 | Conjunction Accumulated Lunations: | 5 | 5 | single_zh_single_en | no |
| 日度法 | Day and Du Factor [NUM]. | 5 | 5 | single_zh_single_en | no |
| 入月日 | Days of entry into month [NUM]. | 5 | 5 | single_zh_single_en | no |
| 虛分 | V oid Parts [NUM]. | 5 | 5 | single_zh_single_en | no |
| 月法 | Lunation Factor [NUM]. | 5 | 5 | single_zh_single_en | no |
| 月餘 | Lunation Remainder: | 5 | 5 | single_zh_single_en | no |
| 除伏逆 | Casting out invisibility and retrogradation, one Appearance is [NUM] days, and it moves [NUM] du. | 4 | 4 | near_ordinal_aligned | no |
| 度餘 | Du Remainder [NUM]. | 4 | 4 | single_zh_single_en | no |
| 積度 | Accumulated Du [NUM]. | 4 | 4 | single_zh_single_en | no |
| 日餘 | Day Remainder [NUM]. | 4 | 4 | single_zh_single_en | no |
| 小餘 | Lesser Remainder [NUM]. | 4 | 4 | single_zh_single_en | no |
| 日率 | Solar Rate: | 3 | 3 | single_zh_single_en | no |
| 周率 | Cycle Rate: | 3 | 3 | single_zh_single_en | no |
| [NUM]日行[NUM]度 | In [NUM] days it moves [NUM] du, and speeds up. | 2 | 2 | ordinal_aligned | no |
| [NUM]日行[NUM]度 | In a day it moves [NUM]/[NUM] du, and in [NUM] days it moves [NUM] du. | 2 | 2 | same_unit_cooccurrence | no |
| 大餘命如前 | Add [OBJECT] | 2 | 2 | one_to_many_ambiguous | no |
| 而見東方 | When it becomes visible in the east, it is [NUM] du and a bit behind the Sun. | 2 | 2 | same_unit_cooccurrence | no |
| 求望、下弦 | Cast out [OBJECT] | 2 | 2 | one_to_many_ambiguous | no |
| 日率 | Solar Rate [NUM]. | 2 | 2 | single_zh_single_en | no |
| 日行[NUM]分度之[NUM] | In a day it moves [NUM]/[NUM] du, and in [NUM] days it moves [NUM] du. | 2 | 2 | near_ordinal_aligned | no |
| 以[OBJECT]乘之 | Cast out [OBJECT] | 2 | 2 | near_ordinal_aligned | no |
| 周率 | Cycle Rate [NUM]. | 2 | 2 | single_zh_single_en | no |
| ([NUM])[金、水]加晨得夕 | Add [OBJECT] | 1 | 1 | same_unit_cooccurrence | no |
| ([NUM])[金、水]加晨得夕 | If the Months of Entry into the Year fill [NUM], cast it out, reckoning into that any intercalary month. | 1 | 1 | same_unit_cooccurrence | no |
| ([NUM])[金、水]加晨得夕 | As for the remainder, count off as before, and outside the count, that is the month of the next conjunction. | 1 | 1 | same_unit_cooccurrence | no |
| ([NUM])[金、水]加晨得夕 | For Venus and Mercury, if one adds to a dawn appearance one gets a dusk appearance, and if one adds to a dusk appearance one gets a dawn appearance. | 1 | 1 | same_unit_cooccurrence | no |
| (如)[加]大餘 | Add [OBJECT] | 1 | 1 | one_to_many_ambiguous | no |

### 以[OBJECT]乘之 ↔ Multiply [OBJECT] by [OBJECT]

Count: 7; distinct chunks: 7; best strength: targeted_prespecified_same_unit; preset: yes

- cullen:chunk:62 §46 p.164-165 Proc. 3.5 [targeted_prespecified_same_unit]
  - zh: 以章月乘之
  - en: Multiply by Rule Months [235].
- cullen:chunk:63 §47 p.165-166 Proc. 3.6 [targeted_prespecified_same_unit]
  - zh: 以蔀日乘之
  - en: Multiply by Obscura - tion Days [27,759].
- cullen:chunk:65 §49 p.167 Proc. 3.8 [targeted_prespecified_same_unit]
  - zh: 以(月)[日]餘乘之
  - en: Multiply by the Day Remainder [168].
- cullen:chunk:66 §50 p.167-169 Proc. 3.9 [targeted_prespecified_same_unit]
  - zh: 餘以十二乘之
  - en: Multiply the remainder by 12.
- cullen:chunk:68 §52 p.170-172 Proc. 3.11 [targeted_prespecified_same_unit]
  - zh: 以沒數乘之
  - en: Multiply by Extinction Number [21], and obtain one for each filling of the Day Factor [4].

### 留不行 ↔ It delays and does not move for [NUM] days.

Count: 6; distinct chunks: 6; best strength: near_ordinal_aligned; preset: no

- cullen:chunk:214 §186 p.209  [near_ordinal_aligned]
  - zh: 留不行
  - en: §186 It delays and does not move for 11 days.
- cullen:chunk:226 §198 p.211  [near_ordinal_aligned]
  - zh: 留不行
  - en: §198 It delays and does not move for 33 days.
- cullen:chunk:238 §209 p.213  [near_ordinal_aligned]
  - zh: 留不行
  - en: §209 It delays and does not move for 8 days.
- cullen:chunk:252 §222 p.215  [near_ordinal_aligned]
  - zh: 留不行
  - en: §222 It delays and does not move for 8 days.
- cullen:chunk:261 §231 p.216  [near_ordinal_aligned]
  - zh: 留不行
  - en: §231 It delays and does not move for 2 days.

### 大餘 ↔ Greater Remainder [NUM].

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:115 §91 p.190 Proc. 3.36 [near_ordinal_aligned]
  - zh: 大餘
  - en: §91 Greater Remainder 23.
- cullen:chunk:128 §104 p.193 Proc. 3.36 [single_zh_single_en]
  - zh: 大餘
  - en: §104 Greater Remainder 47.
- cullen:chunk:142 §117 p.194-195 Proc. 3.36 [single_zh_single_en]
  - zh: 大餘
  - en: §117 Greater Remainder 54.
- cullen:chunk:155 §130 p.195-196 Proc. 3.36 [single_zh_single_en]
  - zh: 大餘
  - en: §130 Greater Remainder 25.
- cullen:chunk:168 §143 p.197 Proc. 3.36 [single_zh_single_en]
  - zh: 大餘
  - en: §143 Greater Remainder 29.

### 合積月 ↔ Conjunction Accumulated Lunations:

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:112 §88 p.190 Proc. 3.36 [single_zh_single_en]
  - zh: 合積月
  - en: §88 Conjunction Accumulated Lunations:
- cullen:chunk:125 §101 p.193 Proc. 3.36 [single_zh_single_en]
  - zh: 合積月
  - en: §101 Conjunction Accumulated Lunations:
- cullen:chunk:139 §114 p.194 Proc. 3.36 [single_zh_single_en]
  - zh: 合積月
  - en: §114 Conjunction Accumulated Lunations:
- cullen:chunk:152 §127 p.195 Proc. 3.36 [single_zh_single_en]
  - zh: 合積月
  - en: §127 Conjunction Accumulated Lunations:
- cullen:chunk:165 §140 p.196 Proc. 3.36 [single_zh_single_en]
  - zh: 合積月
  - en: §140 Conjunction Accumulated Lunations:

### 日度法 ↔ Day and Du Factor [NUM].

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:120 §96 p.192 Proc. 3.36 [single_zh_single_en]
  - zh: 日度法
  - en: §96 Day and Du Factor 17,308.
- cullen:chunk:133 §109 p.194 Proc. 3.36 [single_zh_single_en]
  - zh: 日度法
  - en: §109 Day and Du Factor 3516.
- cullen:chunk:147 §122 p.195 Proc. 3.36 [single_zh_single_en]
  - zh: 日度法
  - en: §122 Day and Du Factor 36,384.
- cullen:chunk:160 §135 p.196 Proc. 3.36 [single_zh_single_en]
  - zh: 日度法
  - en: §135 Day and Du Factor 23,320.
- cullen:chunk:173 §148 p.197 Proc. 3.36 [near_ordinal_aligned]
  - zh: 日度法
  - en: §148 Day and Du Factor 47,632.

### 入月日 ↔ Days of entry into month [NUM].

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:118 §94 p.191-192 Proc. 3.36 [single_zh_single_en]
  - zh: 入月日
  - en: §94 Days of entry into month 15.
- cullen:chunk:131 §107 p.194 Proc. 3.36 [near_ordinal_aligned]
  - zh: 入月日
  - en: §107 Days of entry into month 12.
- cullen:chunk:145 §120 p.195 Proc. 3.36 [near_ordinal_aligned]
  - zh: 入月日
  - en: §120 Days of entry into month 24.
- cullen:chunk:158 §133 p.196 Proc. 3.36 [single_zh_single_en]
  - zh: 入月日
  - en: §133 Days of entry into month 26.
- cullen:chunk:171 §146 p.197 Proc. 3.36 [near_ordinal_aligned]
  - zh: 入月日
  - en: §146 Days of entry into month 28.

### 虛分 ↔ V oid Parts [NUM].

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:117 §93 p.191 Proc. 3.36 [single_zh_single_en]
  - zh: 虛分
  - en: §93 V oid Parts 93.
- cullen:chunk:130 §106 p.193-194 Proc. 3.36 [single_zh_single_en]
  - zh: 虛分
  - en: §106 V oid Parts 186.
- cullen:chunk:144 §119 p.195 Proc. 3.36 [single_zh_single_en]
  - zh: 虛分
  - en: §119 V oid Parts 592.
- cullen:chunk:157 §132 p.196 Proc. 3.36 [single_zh_single_en]
  - zh: 虛分
  - en: §132 V oid Parts 209.
- cullen:chunk:170 §145 p.197 Proc. 3.36 [near_ordinal_aligned]
  - zh: 虛分
  - en: §145 V oid Parts 441.

### 月法 ↔ Lunation Factor [NUM].

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:114 §90 p.190 Proc. 3.36 [single_zh_single_en]
  - zh: 月法
  - en: §90 Lunation Factor 82,213.
- cullen:chunk:127 §103 p.193 Proc. 3.36 [single_zh_single_en]
  - zh: 月法
  - en: §103 Lunation Factor 16,701.
- cullen:chunk:141 §116 p.194 Proc. 3.36 [single_zh_single_en]
  - zh: 月法
  - en: §116 Lunation Factor 172,824.
- cullen:chunk:154 §129 p.195 Proc. 3.36 [near_ordinal_aligned]
  - zh: 月法
  - en: §129 Lunation Factor 110,770.
- cullen:chunk:167 §142 p.196 Proc. 3.36 [single_zh_single_en]
  - zh: 月法
  - en: §142 Lunation Factor 226,252.

### 月餘 ↔ Lunation Remainder:

Count: 5; distinct chunks: 5; best strength: single_zh_single_en; preset: no

- cullen:chunk:113 §89 p.190 Proc. 3.36 [single_zh_single_en]
  - zh: 月餘
  - en: §89 Lunation Remainder:
- cullen:chunk:126 §102 p.193 Proc. 3.36 [single_zh_single_en]
  - zh: 月餘
  - en: §102 Lunation Remainder:
- cullen:chunk:140 §115 p.194 Proc. 3.36 [single_zh_single_en]
  - zh: 月餘
  - en: §115 Lunation Remainder:
- cullen:chunk:153 §128 p.195 Proc. 3.36 [single_zh_single_en]
  - zh: 月餘
  - en: §128 Lunation Remainder:
- cullen:chunk:166 §141 p.196 Proc. 3.36 [ordinal_aligned]
  - zh: 月餘
  - en: §141 Lunation Remainder:

### 除伏逆 ↔ Casting out invisibility and retrogradation, one Appearance is [NUM] days, and it moves [NUM] du.

Count: 4; distinct chunks: 4; best strength: near_ordinal_aligned; preset: no

- cullen:chunk:244 §214 p.213-214  [near_ordinal_aligned]
  - zh: 除伏逆
  - en: §214 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du.
- cullen:chunk:255 §225 p.215  [one_to_many_ambiguous]
  - zh: 除伏逆
  - en: §225 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du.
- cullen:chunk:265 §235 p.216  [near_ordinal_aligned]
  - zh: 除伏逆
  - en: §235 Casting out invisibility and retrogradation, one Appearance is 32 days, and it moves 32 du.
- cullen:chunk:277 §245 p.218  [near_ordinal_aligned]
  - zh: 除伏逆
  - en: §245 Casting out invisibility and retrogradation, one Appearance is 32 days, and it moves 32 du.

## Potentially Interesting Patterns Not Previously Named

| ZH template | EN template | Count | Chunks | Best strength |
| --- | --- | --- | --- | --- |
| 留不行 | It delays and does not move for [NUM] days. | 6 | 6 | near_ordinal_aligned |
| 大餘 | Greater Remainder [NUM]. | 5 | 5 | single_zh_single_en |
| 合積月 | Conjunction Accumulated Lunations: | 5 | 5 | single_zh_single_en |
| 日度法 | Day and Du Factor [NUM]. | 5 | 5 | single_zh_single_en |
| 入月日 | Days of entry into month [NUM]. | 5 | 5 | single_zh_single_en |
| 虛分 | V oid Parts [NUM]. | 5 | 5 | single_zh_single_en |
| 月法 | Lunation Factor [NUM]. | 5 | 5 | single_zh_single_en |
| 月餘 | Lunation Remainder: | 5 | 5 | single_zh_single_en |
| 除伏逆 | Casting out invisibility and retrogradation, one Appearance is [NUM] days, and it moves [NUM] du. | 4 | 4 | near_ordinal_aligned |
| 度餘 | Du Remainder [NUM]. | 4 | 4 | single_zh_single_en |
| 積度 | Accumulated Du [NUM]. | 4 | 4 | single_zh_single_en |
| 日餘 | Day Remainder [NUM]. | 4 | 4 | single_zh_single_en |
| 小餘 | Lesser Remainder [NUM]. | 4 | 4 | single_zh_single_en |
| 日率 | Solar Rate: | 3 | 3 | single_zh_single_en |
| 周率 | Cycle Rate: | 3 | 3 | single_zh_single_en |
| [NUM]日行[NUM]度 | In [NUM] days it moves [NUM] du, and speeds up. | 2 | 2 | ordinal_aligned |
| 日率 | Solar Rate [NUM]. | 2 | 2 | single_zh_single_en |
| 日行[NUM]分度之[NUM] | In a day it moves [NUM]/[NUM] du, and in [NUM] days it moves [NUM] du. | 2 | 2 | near_ordinal_aligned |
| 以[OBJECT]乘之 | Cast out [OBJECT] | 2 | 2 | near_ordinal_aligned |
| 周率 | Cycle Rate [NUM]. | 2 | 2 | single_zh_single_en |

## Low-Frequency Repeated Templates

### Chinese

| Template | Count | Examples |
| --- | --- | --- |
| 通率日行[NUM]分之[NUM] | 3 | cullen:chunk:208:通率日行四千七百二十五分之三百九十八; cullen:chunk:222:通率日行千八百七十六分之九百九十七 |
| 日行[NUM]度[NUM]分度之[NUM] | 3 | cullen:chunk:249:日行一度九十一分度之二十二; cullen:chunk:263:日行一度四分度之一 |
| 命之如前 | 3 | cullen:chunk:63:命之如前; cullen:chunk:68:命之如前 |
| 在日前[NUM]度 | 3 | cullen:chunk:248:在日前九度; cullen:chunk:254:在日前九度 |
| [OBJECT]滿[NUM]除去之 | 3 | cullen:chunk:65:大餘滿六十除去之; cullen:chunk:68:大餘滿六十除去之 |
| 其餘滿蔀法得[NUM] | 2 | cullen:chunk:73:其餘滿蔀法得一; cullen:chunk:75:其餘滿蔀法得一 |
| 在日後[NUM]度有奇 | 2 | cullen:chunk:197:在日後十三度有奇; cullen:chunk:224:在日後十五度有奇 |
| 在日前[NUM]度有奇 | 2 | cullen:chunk:205:在日前十三度有奇; cullen:chunk:219:在日前十六度有奇 |
| 大餘命如前 | 2 | cullen:chunk:95:大餘命如前; cullen:chunk:192:大餘命如前 |
| 而晨伏東方 | 2 | cullen:chunk:243:而晨伏東方; cullen:chunk:264:而晨伏東方 |
| 積度加斗[NUM]度 | 2 | cullen:chunk:71:積度加斗二十一度; cullen:chunk:73:積度加斗二十一度 |
| 通率日行[NUM]度 | 2 | cullen:chunk:257:通率日行一度; cullen:chunk:278:通率日行一度 |
| 而與 日合 | 2 | cullen:chunk:207:而與 日合; cullen:chunk:221:而與 日合 |
| 求望、下弦 | 2 | cullen:chunk:83:求望、下弦; cullen:chunk:86:求望、下弦 |
| 經斗除[NUM]分 | 2 | cullen:chunk:71:經斗除二百三十五分; cullen:chunk:75:經斗除十九分 |
| 滿蔀月得[NUM] | 2 | cullen:chunk:63:滿蔀月得一; cullen:chunk:72:滿蔀月得一 |
| 以除[NUM]歲日 | 2 | cullen:chunk:28:以除一歲日; cullen:chunk:29:以除一歲日 |
| 求次日 | 2 | cullen:chunk:73:求次日; cullen:chunk:75:求次日 |
| 求次月 | 2 | cullen:chunk:73:求次月; cullen:chunk:75:求次月 |
| 日行[NUM]度[NUM]分 | 2 | cullen:chunk:242:日行一度二十二分; cullen:chunk:250:日行一度十五分 |

### English

| Template | Count | Examples |
| --- | --- | --- |
| Count one for each [OBJECT] filled | 3 | cullen:chunk:62:Count one for each Rule Factor [19] filled.; cullen:chunk:63:Count one for each Obscuration Months [940] filled. |
| Solar Rate: | 3 | cullen:chunk:111:§87 Solar Rate:; cullen:chunk:124:§100 Solar Rate: |
| Obtain [RESULT] | 3 | cullen:chunk:69:Obtain 1 as the remainder fills Extinction Factor [7], then that is the Extinction after the Celestial Standard [conjunction].; cullen:chunk:79:Obtain 1 for each time Accumulated Parts fills Obscuration Factor [76], and by that increase the midnight du, then that is the du where the moon is located at dawn. |
| When it becomes visible in the east, it is [NUM] du and a bit behind the Sun. | 2 | cullen:chunk:197:§170 When it becomes visible in the east, it is 13 du and a bit behind the Sun.; cullen:chunk:211:§183 When it becomes visible in the east, it is 16 du and a bit behind the Sun. |
| It becomes invisible at dawn, and in [NUM] days it retreats [NUM] du. | 2 | cullen:chunk:235:§206 It becomes invisible at dawn, and in 5 days it retreats 4 du.; cullen:chunk:258:§228 It becomes invisible at dawn, and in 9 days it retreats 7 du. |
| It returns to direct motion for [NUM] days, and moves [NUM] du. | 2 | cullen:chunk:217:§189 It returns to direct motion for 92 days, and moves 48 du.; cullen:chunk:229:§201 It returns to direct motion for 86 days, and moves 6 du. |
| What is not exhausted is the Lesser Remainder. | 2 | cullen:chunk:68:What is not exhausted is the Lesser Remainder.; cullen:chunk:185:What is not exhausted is the Lesser Remainder. |
| In a day it moves [NUM]/[NUM] du, and in [NUM] days it moves [NUM] du. | 2 | cullen:chunk:251:§221 In a day it moves 33/46 du, and in 46 days it moves 33 du.; cullen:chunk:273:§241 In a day it moves 8/9 du, and in 9 days it moves 8 du. |
| See Cullen (forthcoming), chapter [NUM]. | 2 | cullen:chunk:25:See Cullen (forthcoming), chapter 3.; cullen:chunk:300:See Cullen (forthcoming), chapter 6. |
| In [NUM] days it moves [NUM] du, and speeds up. | 2 | cullen:chunk:239:In 46 days it moves 33 du, and speeds up.; cullen:chunk:262:In 9 days it moves 8 du, and speeds up. |
| It delays once more, for [NUM] days. | 2 | cullen:chunk:216:§188 It delays once more, for 11 days.; cullen:chunk:228:§200 It delays once more, for 33 days. |
| As in Triple Concordance. | 2 | cullen:chunk:215:As in Triple Concordance.; cullen:chunk:239:As in Triple Concordance. |
| What does not fill [OBJECT] is [RESULT] | 2 | cullen:chunk:65:What does not fill [a Medial [Qi] factor [32]] is the Lesser Remainder.; cullen:chunk:181:§156 What does not fill Cycle Rate, subtract back [from Cycle Rate], and the remainder is Du Parts. |
| Cycle Rate [NUM]. | 2 | cullen:chunk:150:§125 Cycle Rate 5830.; cullen:chunk:163:§138 Cycle Rate 11,908. |
| Solar Rate [NUM]. | 2 | cullen:chunk:151:§126 Solar Rate 4661.; cullen:chunk:164:§139 Solar Rate 1889. |

## Suspicious Chunks For Chunker Fix

| Reason | Chunk | Unit | Book page | Excerpt |
| --- | --- | --- | --- | --- |
| text_contains_page_garbage | cullen:chunk:12 | §4 | 143-144 | 日月之(術)[行]， 則有冬有夏 ；冬夏之閒， 則有春有秋． 是故日行北陸謂之 冬， 西陸謂之春， 南陸謂之夏， 東陸謂之秋． 日道發南， 去極彌遠， 其景彌長, 遠長乃極， 冬乃至焉． 日道斂北， 去極彌近， 其景彌短， 近短乃極， 夏乃至焉. 二至之中， 道齊景正， 春秋分焉． §4 Through the motion of the sun and moon, there is winter and there is sum -… |
| many_zh_clauses_few_en_clauses | cullen:chunk:14 | §6 | 145-146 | 極建其中， 道營于外， 琁衡追日， 以察[發]斂， 光道生焉． 孔壺為漏， 浮箭為 刻， 下漏數刻， 以考中星， 昏明生焉． §6 The pole is established in the centre, and the Roads are constructed outside. The Xuan and Heng pursue the sun, 3 and by investigating its outwards and i… |
| many_zh_clauses_few_en_clauses | cullen:chunk:22 | §12 | 149 | 帝王之大司備矣， 天下之能事畢矣． 過此而往， 羣忌苟禁， 君子未之或 知也． §12 The Great Task sustains it, and good and evil fortune come forth from it. Therefore, when the gentleman is to undertake some new matter, he looks into it in order to be able t… |
| table_like_chunk | cullen:chunk:30 | §18 | 153 | 月分成閏， 閏七而盡， 其歲十九， 名之曰章． 章首分盡， 四之俱終， 名之曰蔀. 以一歲日乘之， 為蔀之日數也． 以甲子命之， 二十而復其初， 是以二十蔀為 紀 ．紀歲青龍未終， 三終歲後復青龍為元． §18 The fractions of a lunation complete an intercalation, and these intercalations are exhausted after seven. The ye… |
| text_contains_page_garbage | cullen:chunk:32 | §20 | 154 | 紀法， 千五百二十． §20 Era Factor: 1520. 1520 = 25 × 60 + 20, so the sexagenary name of the year advances by 20 after Era Factor years. However the sexagenary day name remains the same, and Era Factor years after System Origin,… |
| translation_unit_missing_source_text_zh | cullen:chunk:46 | §33 | 157 | §33 Medial [Qi] Factor: 32. There are 1461/4 days in a solar cycle, so the interval between two of the 24 qi into which the cycle is divided is: 1,461/ (4 × 24) days = 487⁄32 days = 15 7⁄32 days So that is 487 days at a… |
| table_like_chunk | cullen:chunk:49 | §36 | 157-159 | 月食數之生也， 乃記月食之既者． 率二十三食而復既， 其月(食)百三十五， 率 之相除， 得五(百)[月]二十三之二十而一食． 以除一歲之月， 得歲有再食五 百一十三分之五十[五]也． 分終其法， 因以與蔀相約， 得四與二十七， 互之， 會二千五十二， 二十而與元會． §36 In producing the numbers for lunar eclipses, one records instances where the lun… |
| translation_unit_missing_source_text_zh | cullen:chunk:57 | §43 | 160-161 | §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how many you obtain, then outside the count is the Era you are ent… |
| table_like_chunk | cullen:chunk:57 | §43 | 160-161 | §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how many you obtain, then outside the count is the Era you are ent… |
| translation_unit_missing_source_text_zh | cullen:chunk:59 | §44 | 161-162 | §44 From the distance from High Origin cast out Origin Coincidence [41,040]. From the remainder, cast out Obscuration Coincidence [2052], and multiply what you obtain by 27. Cast out what fills 60, and from the number y… |

