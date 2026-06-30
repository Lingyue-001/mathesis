# Sifen Corpus Profile

> Exploratory corpus profiling only. This is not final extraction and does not define gold annotations.

## Summary

| Metric | Value |
| --- | ---: |
| Body chunks | 300 |
| section_intro | 39 |
| translation_unit | 261 |
| translation_unit missing source_text_zh | 14 |
| translation_unit missing translation_en | 0 |
| translation_unit with commentary_en | 91 |
| section_intro containing Chinese | 12 |
| Book page range | 139-234 |
| Average char_count | 550.2 |
| Quality verdict | good_for_exploratory_profile |

## Result Yield

- chunk_type and field separation are strong enough for field-aware corpus profiling
- translation_unit coverage is high enough to surface repeated operation and constant patterns
- source_text_zh and translation_en pairing is good enough for exploratory bilingual number candidates

## Quality Limits

- statistics are limited to Cullen book pages 138-234, not the full book
- table-like chunks, footnotes, and a small set of missing Chinese sources still require manual review
- pattern seeds are exploratory and must not be treated as gold extraction rules

## Section Distribution

| Section path | Chunks |
| --- | ---: |
| 3 > 3.2 > 3.2.7 | 92 |
| 3 > 3.2 > 3.2.5 | 73 |
| 3 > 3.2 > 3.2.4 | 47 |
| 3 > 3.2 > 3.2.1 | 23 |
| 3 > 3.2 > 3.2.6 | 19 |
| 3 > 3.2 > 3.2.2 | 18 |
| 3 > 3.2 > 3.2.3 | 7 |
| 3 > 3.2 > 3.2.11 | 5 |
| 3 > 3.2 > 3.2.9 | 5 |
| 3 > 3.2 > 3.2.8 | 3 |
| 3 | 1 |
| 3 > 3.1 > 3.1.2 | 1 |
| 3 > 3.1 > 3.1.3 | 1 |
| 3 > 3.1 > 3.1.4 | 1 |
| 3 > 3.1 > 3.1.5 | 1 |
| 3 > 3.1 > 3.1.6 | 1 |
| 3 > 3.2 | 1 |
| 3 > 3.2 > 3.2.10 | 1 |

## Operation Verb Candidates

| English operation cue | Count | Example chunks |
| --- | ---: | --- |
| Remainder | 187 | cullen:chunk:23, cullen:chunk:28, cullen:chunk:44, cullen:chunk:62, cullen:chunk:63 |
| Count | 64 | cullen:chunk:23, cullen:chunk:30, cullen:chunk:62, cullen:chunk:63, cullen:chunk:65 |
| Add | 54 | cullen:chunk:29, cullen:chunk:63, cullen:chunk:65, cullen:chunk:67, cullen:chunk:68 |
| Multiply | 51 | cullen:chunk:62, cullen:chunk:63, cullen:chunk:64, cullen:chunk:65, cullen:chunk:66 |
| Obtain | 38 | cullen:chunk:26, cullen:chunk:28, cullen:chunk:67, cullen:chunk:68, cullen:chunk:69 |
| Cast out | 36 | cullen:chunk:49, cullen:chunk:57, cullen:chunk:59, cullen:chunk:63, cullen:chunk:65 |
| Subtract | 31 | cullen:chunk:62, cullen:chunk:65, cullen:chunk:66, cullen:chunk:68, cullen:chunk:69 |
| Set out | 17 | cullen:chunk:62, cullen:chunk:63, cullen:chunk:65, cullen:chunk:68, cullen:chunk:71 |
| called | 15 | cullen:chunk:10, cullen:chunk:12, cullen:chunk:25, cullen:chunk:29, cullen:chunk:30 |
| Count one for each | 9 | cullen:chunk:62, cullen:chunk:63, cullen:chunk:65, cullen:chunk:66, cullen:chunk:68 |
| Divide | 6 | cullen:chunk:10, cullen:chunk:12, cullen:chunk:29, cullen:chunk:69, cullen:chunk:87 |
| Call this | 5 | cullen:chunk:62, cullen:chunk:68, cullen:chunk:71, cullen:chunk:88, cullen:chunk:99 |
| What does not fill | 3 | cullen:chunk:65, cullen:chunk:102, cullen:chunk:181 |

## Top Chinese Operation Segments

| Segment | Count | Example chunks |
| --- | ---: | --- |
| 除伏逆 | 7 | cullen:chunk:206, cullen:chunk:220, cullen:chunk:232, cullen:chunk:244, cullen:chunk:255 |
| 不盡為小餘 | 3 | cullen:chunk:68, cullen:chunk:185, cullen:chunk:188 |
| 不盡為餘分 | 3 | cullen:chunk:71, cullen:chunk:73, cullen:chunk:75 |
| 置入蔀年減一 | 3 | cullen:chunk:62, cullen:chunk:65, cullen:chunk:68 |
| 大餘滿六十除去之 | 2 | cullen:chunk:65, cullen:chunk:68 |
| 滿蔀日除去之 | 2 | cullen:chunk:73, cullen:chunk:75 |
| 滿蔀月得一 | 2 | cullen:chunk:63, cullen:chunk:72 |
| 滿日法得一 | 2 | cullen:chunk:68, cullen:chunk:188 |
| 名為積月 | 2 | cullen:chunk:62, cullen:chunk:88 |
| 其餘滿蔀法得一 | 2 | cullen:chunk:73, cullen:chunk:75 |
| 為積 度 | 2 | cullen:chunk:73, cullen:chunk:75 |
| 以蔀法乘之 | 2 | cullen:chunk:73, cullen:chunk:77 |
| 以除一歲日 | 2 | cullen:chunk:28, cullen:chunk:29 |
| 以月周乘之 | 2 | cullen:chunk:75, cullen:chunk:79 |
| 置入蔀積日之數 | 2 | cullen:chunk:73, cullen:chunk:75 |
| (術)[行]分母乘之 | 1 | cullen:chunk:281 |
| (為章閏)11 | 1 | cullen:chunk:41 |
| (一)[金、水]加晨得夕 | 1 | cullen:chunk:191 |
| (因為章閏).12 | 1 | cullen:chunk:43 |
| [大分]滿蔀月從度 | 1 | cullen:chunk:83 |
| [二為半 | 1 | cullen:chunk:291 |
| ]小飾滿蔀月得一 | 1 | cullen:chunk:192 |
| 〔合〕餘以周率除之 | 1 | cullen:chunk:179 |
| 不得焉退歲 | 1 | cullen:chunk:179 |
| 不盡]為月餘 | 1 | cullen:chunk:182 |
| 不盡名[為]合餘 | 1 | cullen:chunk:178 |
| 不盡為 閏餘 | 1 | cullen:chunk:183 |
| 不盡為度餘 | 1 | cullen:chunk:187 |
| 不盡為沒餘 | 1 | cullen:chunk:68 |
| 不盡為日餘 | 1 | cullen:chunk:186 |

## English Term Candidates

| Term | Count | Example chunks |
| --- | ---: | --- |
| Lesser Remainder | 31 | cullen:chunk:63, cullen:chunk:65, cullen:chunk:67, cullen:chunk:68, cullen:chunk:69 |
| Greater Remainder | 29 | cullen:chunk:63, cullen:chunk:65, cullen:chunk:67, cullen:chunk:68, cullen:chunk:95 |
| Obscuration | 28 | cullen:chunk:30, cullen:chunk:49, cullen:chunk:61, cullen:chunk:62, cullen:chunk:63 |
| Du Factor | 25 | cullen:chunk:107, cullen:chunk:108, cullen:chunk:120, cullen:chunk:133, cullen:chunk:147 |
| Obscuration Months | 23 | cullen:chunk:35, cullen:chunk:63, cullen:chunk:64, cullen:chunk:67, cullen:chunk:71 |
| Accumulated Months | 13 | cullen:chunk:63, cullen:chunk:71, cullen:chunk:88, cullen:chunk:90, cullen:chunk:91 |
| Days | 13 | cullen:chunk:63, cullen:chunk:75, cullen:chunk:118, cullen:chunk:131, cullen:chunk:145 |
| Obscuration Factor | 13 | cullen:chunk:34, cullen:chunk:73, cullen:chunk:75, cullen:chunk:76, cullen:chunk:77 |
| Lunation Factor | 12 | cullen:chunk:104, cullen:chunk:114, cullen:chunk:127, cullen:chunk:141, cullen:chunk:154 |
| Lunation Remainder | 11 | cullen:chunk:88, cullen:chunk:104, cullen:chunk:113, cullen:chunk:126, cullen:chunk:140 |
| Origin | 11 | cullen:chunk:30, cullen:chunk:49, cullen:chunk:61, cullen:chunk:109, cullen:chunk:297 |
| Day Remainder | 10 | cullen:chunk:44, cullen:chunk:65, cullen:chunk:69, cullen:chunk:119, cullen:chunk:132 |
| High Origin | 9 | cullen:chunk:59, cullen:chunk:99, cullen:chunk:176, cullen:chunk:180, cullen:chunk:185 |
| Accumulated Days | 8 | cullen:chunk:63, cullen:chunk:73, cullen:chunk:75, cullen:chunk:94, cullen:chunk:185 |
| Circuits | 8 | cullen:chunk:38, cullen:chunk:64, cullen:chunk:72, cullen:chunk:108, cullen:chunk:181 |
| Du Remainder | 8 | cullen:chunk:122, cullen:chunk:136, cullen:chunk:149, cullen:chunk:162, cullen:chunk:175 |
| Intercalation Remainder | 8 | cullen:chunk:62, cullen:chunk:64, cullen:chunk:66, cullen:chunk:72, cullen:chunk:183 |
| Obscuration Days | 8 | cullen:chunk:40, cullen:chunk:67, cullen:chunk:73, cullen:chunk:75, cullen:chunk:98 |
| Rule | 8 | cullen:chunk:30, cullen:chunk:61, cullen:chunk:91, cullen:chunk:183 |
| Months | 7 | cullen:chunk:62, cullen:chunk:71, cullen:chunk:76, cullen:chunk:182, cullen:chunk:191 |
| Obscuration Coincidence | 7 | cullen:chunk:51, cullen:chunk:87, cullen:chunk:88 |
| Remainder | 7 | cullen:chunk:71, cullen:chunk:73, cullen:chunk:75, cullen:chunk:91, cullen:chunk:189 |
| Rule Factor | 7 | cullen:chunk:36, cullen:chunk:62, cullen:chunk:66, cullen:chunk:104 |
| Rule Months | 7 | cullen:chunk:37, cullen:chunk:62, cullen:chunk:90, cullen:chunk:91, cullen:chunk:104 |
| Lunar Circuits | 5 | cullen:chunk:48, cullen:chunk:75, cullen:chunk:79, cullen:chunk:80 |
| Month Number | 5 | cullen:chunk:54, cullen:chunk:88, cullen:chunk:99 |
| The Lesser Remainder | 5 | cullen:chunk:65, cullen:chunk:69, cullen:chunk:74, cullen:chunk:98, cullen:chunk:102 |
| Day Factor | 4 | cullen:chunk:39, cullen:chunk:68, cullen:chunk:107, cullen:chunk:188 |
| Eclipse Factor | 4 | cullen:chunk:55, cullen:chunk:88, cullen:chunk:99 |
| Eclipse Remainder | 4 | cullen:chunk:87, cullen:chunk:99 |

## Bilingual Number Candidates

| chunk | unit | book page | Chinese | English | Value |
| --- | --- | --- | --- | --- | ---: |
| cullen:chunk:10 | §3 | 143-143 | 朔． 舒先速後， 近一遠三， 謂之弦. 相與為衡， | §3 ‘The sun an | 3 |
| cullen:chunk:16 | §8 | 146-147 | ， 晨夕生焉． 日、月、五緯各有終原， 而七元生 | g), chapter 5. evens out; | 5 |
| cullen:chunk:25 | §14 | 150-151 | 在上章， 陰在執徐， 冬十有一月甲子夜半朔 旦冬至 | enth of its 10 posi- tions | 10 |
| cullen:chunk:25 | §14 | 150-151 | 章， 陰在執徐， 冬十有一月甲子夜半朔 旦冬至， | , day jiazi.1, at midnigh | 1 |
| cullen:chunk:26 | §15 | 151-151 | 歲， 然其景不復， 四周千四百六十一日， 而景復初， 是則日 | r circuits, 1461 days, and s | 1461 |
| cullen:chunk:28 | §16 | 151-152 | 二百五十四周， 復會于端， 是則月 | s travelled 254 circuits, t | 254 |
| cullen:chunk:28 | §16 | 151-152 | 周減之， 餘十二十九分之七， 則月行過周及日行之數 | inder of 12 7/19 which is | 7 |
| cullen:chunk:29 | §17 | 152-153 | 月(大)四時推移， 故置十二中以定 | (365 ¼) /2 4 = 15 7⁄32 T | 4 |
| cullen:chunk:29 | §17 | 152-153 | 月(大)四時推移， 故置十二中以定月位． 有朔而無中 | ets out the 12 Medial [Qi] | 12 |
| cullen:chunk:29 | §17 | 152-153 | 日) [曰]節， 與中為二十四氣． 以除一歲日， 為一 | se make the 24 qi. If by t | 24 |
| cullen:chunk:29 | §17 | 152-153 | 之分積如其 法得一日， 四歲而終． | (365 ¼) /2 4 = 15 7⁄32 T | 4 |
| cullen:chunk:30 | §18 | 153-153 | 成閏， 閏七而盡， 其歲十九， 名之曰章． 章首分盡 | e years are 19, which is c | 19 |
| cullen:chunk:30 | §18 | 153-153 | 日數也． 以甲子命之， 二十而復其初， 是以二十蔀為 | ing [after] 20. So 20 Obsc | 20 |
| cullen:chunk:30 | §18 | 153-153 | ， 二十而復其初， 是以二十蔀為 紀 ．紀歲青龍未終 | ing [after] 20. So 20 Obsc | 20 |
| cullen:chunk:30 | §18 | 153-153 | 紀 ．紀歲青龍未終， 三終歲後復青龍為元． | lie ji jie 3, 125–126) a | 3 |
| cullen:chunk:31 | §19 | 154-154 | 元法， 四千五百六十． | gin Factor: 4560. | 4560 |
| cullen:chunk:32 | §20 | 154-154 | 紀法， 千五百二十． | Era Factor: 1520. | 1520 |
| cullen:chunk:33 | §21 | 154-154 | 紀月， 萬八千八百． | Era Months: 18,800. | 18800 |
| cullen:chunk:34 | §22 | 154-154 | 蔀法， 七十六． | ion Factor: 76. | 76 |
| cullen:chunk:35 | §23 | 154-155 | 蔀月， 九百四十． | ion Months: 940. | 940 |
| cullen:chunk:36 | §24 | 155-155 | 章法， 十九． | ule Factor: 19. | 19 |
| cullen:chunk:37 | §25 | 155-155 | 章月， 二百三十五． | ule Months: 235. | 235 |
| cullen:chunk:38 | §26 | 155-155 | 周天， 千四百六十一． | of Heaven: 1461. | 1461 |
| cullen:chunk:39 | §27 | 155-156 | 日法， 四． | Day Factor: 4. | 4 |
| cullen:chunk:40 | §28 | 156-156 | 蔀日， 二萬七千七百五十九． | ation Days: 27,759. | 27759 |
| cullen:chunk:41 | §29 | 156-156 | 沒數， 二十一． (為章閏)11 | ion Number: 21. | 21 |
| cullen:chunk:42 | §30 | 156-156 | 通法， 四百八十七． | ity Factor: 487. | 487 |
| cullen:chunk:43 | §31 | 156-156 | 沒法， 七， (因為章閏).12 | ion Factor: 7. | 7 |
| cullen:chunk:44 | §32 | 156-156 | 日餘， 百六十八． | Remainder: 168. | 168 |
| cullen:chunk:47 | §34 | 157-157 | 大周， 三十四萬三千三百三十五． | r Circuits: 343,335. | 343335 |
| cullen:chunk:48 | §35 | 157-157 | 月周千一十六． | r Circuits: 1016. | 1016 |
| cullen:chunk:49 | §36 | 157-159 | ， 乃記月食之既者． 率二十三食而復既， 其月(食)百 | that after 23 eclipses to | 23 |
| cullen:chunk:49 | §36 | 157-159 | 三食而復既， 其月(食)百三十五， 率 之相除， 得五( | months are 135. If the rat | 135 |
| cullen:chunk:49 | §36 | 157-159 | 十五， 率 之相除， 得五(百)[月]二十三之二十 | eclipse per 5 20/23 month | 5 |
| cullen:chunk:49 | §36 | 157-159 | 相除， 得五(百)[月]二十三之二十而一食． 以除一歲 | that after 23 eclipses to | 23 |
| cullen:chunk:49 | §36 | 157-159 | 得五(百)[月]二十三之二十而一食． 以除一歲之月， | lipse per 5 20/23 months. | 20 |
| cullen:chunk:49 | §36 | 157-159 | 除一歲之月， 得歲有再食五 百一十三分之五十[五] | eclipse per 5 20/23 month | 5 |
| cullen:chunk:49 | §36 | 157-159 | 食五 百一十三分之五十[五]也． 分終其法， 因以 | eclipse per 5 20/23 month | 5 |
| cullen:chunk:49 | §36 | 157-159 | 法， 因以與蔀相約， 得四與二十七， 互之， 會二 | n, one gets 4 and 27. Cha | 4 |
| cullen:chunk:49 | §36 | 157-159 | 因以與蔀相約， 得四與二十七， 互之， 會二千五十二 | gets 4 and 27. Changing i | 27 |
| cullen:chunk:49 | §36 | 157-159 | 四與二十七， 互之， 會二千五十二， 二十而與元會． | [occurs at] 2052, and in 20 | 2052 |
| cullen:chunk:49 | §36 | 157-159 | 互之， 會二千五十二， 二十而與元會． | lipse per 5 20/23 months. | 20 |
| cullen:chunk:50 | §37 | 159-159 | 元會， 四萬一千四十． | oincidence: 41,040. | 41040 |
| cullen:chunk:52 | §39 | 159-159 | 歲數， 五百一十三． | ear Number: 513. | 513 |
| cullen:chunk:53 | §40 | 159-159 | 食數， 千八十一． | pse Number: 1081. | 1081 |
| cullen:chunk:62 | §46 | 164-165 | 為積月， 不滿為閏餘， 十二以上, 其歲有閏． | r. If it is 12 or more, th | 12 |
| cullen:chunk:63 | §47 | 165-166 | ， 不滿為小餘， 積日以六十 除去之， 其餘為大餘， | r. Cast out 60 from the Ac | 60 |
| cullen:chunk:63 | §47 | 165-166 | 正十一月朔日 也． 小餘四百四十一以上， 其月大． 求後月 | emainder is 441 or greater, | 441 |
| cullen:chunk:63 | §47 | 165-166 | 大． 求後月朔， 加大餘二十九， 小餘四百九十 [九] | month, add 29 to the Grea | 29 |
| cullen:chunk:65 | §49 | 167-167 | 不滿為 小餘， 大餘滿六十除去之， 其餘以蔀名命之 | ultiples of 60 have been c | 60 |

## Pattern Seeds

### zh_term_number ↔ en_term_number

Count: 34

- cullen:chunk:31 §19 p.154-154: 四千五百六十 ↔ Origin Factor: 4
  - zh: 元法， 四千五百六十．
  - en: §19 Origin Factor: 4560.
- cullen:chunk:32 §20 p.154-154: 千五百二十 ↔ Era Factor: 1
  - zh: 紀法， 千五百二十．
  - en: §20 Era Factor: 1520.
- cullen:chunk:33 §21 p.154-154: 萬八千八百 ↔ Era Months: 1
  - zh: 紀月， 萬八千八百．
  - en: §21 Era Months: 18,800.
- cullen:chunk:34 §22 p.154-154: 七十六 ↔ Obscuration Factor: 7
  - zh: 蔀法， 七十六．
  - en: §22 Obscuration Factor: 76.
- cullen:chunk:35 §23 p.154-155: 九百四十 ↔ Obscuration Months: 9
  - zh: 蔀月， 九百四十．
  - en: §23 Obscuration Months: 940.

### 謂之X ↔ called Y

Count: 3

- cullen:chunk:10 §3 p.143-143: 謂之合朔 ↔ called a conjunction
  - zh: 日月相推， 日舒月速， 當其同[所]， 謂之合朔． 舒先速後， 近一遠三， 謂之弦. 相與為衡， 分天之中， 謂之望． 以速及舒， 光盡體伏， 謂之晦． 晦朔合離， 斗建 移辰， 謂之[月]．
  - en: §3 ‘The sun and moon push one another on’. The sun is slow and the moon is fast. When they share a position, that is called a conjunction. The slow [i.e. the sun] is ahead and the…
- cullen:chunk:12 §4 p.143-144: 謂之春 ↔ called winter
  - zh: 日月之(術)[行]， 則有冬有夏 ；冬夏之閒， 則有春有秋． 是故日行北陸謂之 冬， 西陸謂之春， 南陸謂之夏， 東陸謂之秋． 日道發南， 去極彌遠， 其景彌長, 遠長乃極， 冬乃至焉． 日道斂北， 去極彌近， 其景彌短， 近短乃極， 夏乃至焉. 二至之中， 道齊景正， 春秋分焉．
  - en: §4 Through the motion of the sun and moon, there is winter and there is sum - mer. Between winter and summer, there is spring and there is autumn. Thus when the sun moves through …
- cullen:chunk:25 §14 p.150-151: 謂之漢曆 ↔ called the Han System
  - zh: 當漢高皇帝受命四十有五歲， 陽在上章， 陰在執徐， 冬十有一月甲子夜半朔 旦冬至， 日月閏積之數皆自此始， 立元正朔， 謂之漢曆． 又上兩元， 而月食五 星之元， 並發端焉．
  - en: §14 In the forty-fifth year after the High Sovereign Emperor of Han received the mandate, when the Yang was at shangzhang [the seventh of its 10 posi- tions], and the Yin was at z…

### 置X ↔ Set out X

Count: 12

- cullen:chunk:62 §46 p.164-165: 置入蔀年減一 ↔ Set out
  - zh: 推天正術， 置入蔀年減一， 以章月乘之， 滿章法得一， 名為積月， 不滿為閏餘， 十二以上, 其歲有閏．
  - en: §46 Set out the years into the Obscuration and subtract one. Multiply by Rule Months [235]. Count one for each Rule Factor [19] filled. Call this Accu- mulated Months. The remaind…
- cullen:chunk:63 §47 p.165-166: 置入蔀積月 ↔ Set out
  - zh: 推天正朔日， 置入蔀積月， 以蔀日乘之， 滿蔀月得一， 名為積日， 不滿為小餘， 積日以六十 除去之， 其餘為大餘， 以所入蔀名命之， 筭盡之外， 則前年天正十一月朔日 也． 小餘四百四十一以上， 其月大． 求後月朔， 加大餘二十九， 小餘四百九十 [九]， 小餘滿蔀月得一， 上加大餘， 命之如前．
  - en: §47 Set out the Accumulated Months into the Obscuration. Multiply by Obscura - tion Days [27,759]. Count one for each Obscuration Months [940] filled. Call that Accumulated Days. …
- cullen:chunk:65 §49 p.167-167: 置入蔀年減一 ↔ set out
  - zh: 推二十四氣 術曰：置入蔀年減一， 以(月)[日]餘乘之， 滿中法得一， 名曰大餘， 不滿為 小餘， 大餘滿六十除去之， 其餘以蔀名命之， 筭盡之外， 則前年冬至之日也. 求次氣， 加大餘十五， 小餘七， 除命之如前， 小寒日也．
  - en: §49 Method: set out the years entered into the Obscuration and subtract one. Multiply by the Day Remainder [168]. Count one for each Medial [Qi] factor [32] filled. Call that the …
- cullen:chunk:68 §52 p.170-172: 置入蔀年減一 ↔ Set out
  - zh: 推沒滅術， 置入蔀年減一， 以沒數乘之， 滿日法得一， 名為積沒， 不盡為沒餘． 以通法乘 積沒， 滿沒法得一， 名為大餘， 不盡為小餘． 大餘滿六十除去之， 其餘以蔀名 命之， 筭盡之外， 前年冬至前沒日也． 求後沒， 加大餘六十九， 小餘四， 小餘滿 沒法， 從大餘， 命之如前， 無分為滅．
  - en: §52 Set out years of entry into the Obscuration and subtract one. Multiply by Extinction Number [21], and obtain one for each filling of the Day Factor [4]. Called this Accumulate…
- cullen:chunk:73 §56 p.174-175: 置入蔀積日之數 ↔ Set out
  - zh: 推日所在度， 置入蔀積日之數， 以蔀法乘之， 滿蔀日除去之， 其餘滿蔀法得一， 為積 度， 不盡為餘分． 積度加斗二十一度， 加十九分， 以宿次除去之， 則夜半日所 在宿度也． 求次日， 加一度． 求次月， 大加三十度， 小加二十九度， 經斗除十 [九]分．
  - en: §56 Set out the number of Accumulated Days entered into the Obscuration, and multiply it by Obscuration Factor [76]. Cast out and discard Obscuration Days [27,759], and obtain 1 f…

### 以X乘之 ↔ Multiply by X

Count: 15

- cullen:chunk:62 §46 p.164-165: 以章月乘之 ↔ Multiply
  - zh: 推天正術， 置入蔀年減一， 以章月乘之， 滿章法得一， 名為積月， 不滿為閏餘， 十二以上, 其歲有閏．
  - en: §46 Set out the years into the Obscuration and subtract one. Multiply by Rule Months [235]. Count one for each Rule Factor [19] filled. Call this Accu- mulated Months. The remaind…
- cullen:chunk:63 §47 p.165-166: 以蔀日乘之 ↔ Multiply
  - zh: 推天正朔日， 置入蔀積月， 以蔀日乘之， 滿蔀月得一， 名為積日， 不滿為小餘， 積日以六十 除去之， 其餘為大餘， 以所入蔀名命之， 筭盡之外， 則前年天正十一月朔日 也． 小餘四百四十一以上， 其月大． 求後月朔， 加大餘二十九， 小餘四百九十 [九]， 小餘滿蔀月得一， 上加大餘， 命之如前．
  - en: §47 Set out the Accumulated Months into the Obscuration. Multiply by Obscura - tion Days [27,759]. Count one for each Obscuration Months [940] filled. Call that Accumulated Days. …
- cullen:chunk:66 §50 p.167-169: 以十二乘之 ↔ Multiply
  - zh: 推閏月所在， 以閏餘減章法， 餘以十二乘之， 滿章閏數得一， 滿四以上亦得一筭之數， 從前 年十一月起， 筭盡之外， 閏月也． 或進退， 以中氣定之．
  - en: §50 Subtract the Intercalation Remainder from Rule Factor [19]. Multiply the remainder by 12. Count one for each completed Rule Intercalation Number [7]; for a completed four also…
- cullen:chunk:67 §51 p.169-170: 以百刻乘之 ↔ multiply
  - zh: 推弦、望日， 因其月朔大小餘之數， 皆加大餘七， 小餘三百五十九四分三， 小餘滿蔀月 得一， 加大餘， 大餘命如法， 得上弦． 又加得望， 次下弦， 又後月朔． 其弦、望 小餘二百六十以下， 每以百刻乘之， 滿蔀月得一刻， 不滿其(數)[所]近節氣 夜漏之半者， 以筭上為日．
  - en: §51 T ake the numbers for the Greater and Lesser Remainders for this month, and in each case add to the Greater Remainder 7 and the Lesser Remainder 359¾. Count one if the Lesser …
- cullen:chunk:68 §52 p.170-172: 以沒數乘之 ↔ Multiply
  - zh: 推沒滅術， 置入蔀年減一， 以沒數乘之， 滿日法得一， 名為積沒， 不盡為沒餘． 以通法乘 積沒， 滿沒法得一， 名為大餘， 不盡為小餘． 大餘滿六十除去之， 其餘以蔀名 命之， 筭盡之外， 前年冬至前沒日也． 求後沒， 加大餘六十九， 小餘四， 小餘滿 沒法， 從大餘， 命之如前， 無分為滅．
  - en: §52 Set out years of entry into the Obscuration and subtract one. Multiply by Extinction Number [21], and obtain one for each filling of the Day Factor [4]. Called this Accumulate…

### 滿X得一 / 如X得一 ↔ Count one for each X filled

Count: 19

- cullen:chunk:62 §46 p.164-165: 滿章法得一 ↔ Count one for each
  - zh: 推天正術， 置入蔀年減一， 以章月乘之， 滿章法得一， 名為積月， 不滿為閏餘， 十二以上, 其歲有閏．
  - en: §46 Set out the years into the Obscuration and subtract one. Multiply by Rule Months [235]. Count one for each Rule Factor [19] filled. Call this Accu- mulated Months. The remaind…
- cullen:chunk:63 §47 p.165-166: 滿蔀月得一 ↔ Count one for each
  - zh: 推天正朔日， 置入蔀積月， 以蔀日乘之， 滿蔀月得一， 名為積日， 不滿為小餘， 積日以六十 除去之， 其餘為大餘， 以所入蔀名命之， 筭盡之外， 則前年天正十一月朔日 也． 小餘四百四十一以上， 其月大． 求後月朔， 加大餘二十九， 小餘四百九十 [九]， 小餘滿蔀月得一， 上加大餘， 命之如前．
  - en: §47 Set out the Accumulated Months into the Obscuration. Multiply by Obscura - tion Days [27,759]. Count one for each Obscuration Months [940] filled. Call that Accumulated Days. …
- cullen:chunk:65 §49 p.167-167: 滿中法得一 ↔ Count one for each
  - zh: 推二十四氣 術曰：置入蔀年減一， 以(月)[日]餘乘之， 滿中法得一， 名曰大餘， 不滿為 小餘， 大餘滿六十除去之， 其餘以蔀名命之， 筭盡之外， 則前年冬至之日也. 求次氣， 加大餘十五， 小餘七， 除命之如前， 小寒日也．
  - en: §49 Method: set out the years entered into the Obscuration and subtract one. Multiply by the Day Remainder [168]. Count one for each Medial [Qi] factor [32] filled. Call that the …
- cullen:chunk:66 §50 p.167-169: 滿章閏數得一 ↔ Count one for each
  - zh: 推閏月所在， 以閏餘減章法， 餘以十二乘之， 滿章閏數得一， 滿四以上亦得一筭之數， 從前 年十一月起， 筭盡之外， 閏月也． 或進退， 以中氣定之．
  - en: §50 Subtract the Intercalation Remainder from Rule Factor [19]. Multiply the remainder by 12. Count one for each completed Rule Intercalation Number [7]; for a completed four also…
- cullen:chunk:67 §51 p.169-170: 滿蔀月得一 ↔ for each
  - zh: 推弦、望日， 因其月朔大小餘之數， 皆加大餘七， 小餘三百五十九四分三， 小餘滿蔀月 得一， 加大餘， 大餘命如法， 得上弦． 又加得望， 次下弦， 又後月朔． 其弦、望 小餘二百六十以下， 每以百刻乘之， 滿蔀月得一刻， 不滿其(數)[所]近節氣 夜漏之半者， 以筭上為日．
  - en: §51 T ake the numbers for the Greater and Lesser Remainders for this month, and in each case add to the Greater Remainder 7 and the Lesser Remainder 359¾. Count one if the Lesser …

### 不滿為X ↔ what does not fill ... is X

Count: 0


## Suspicious Chunks For Review

| Reason | chunk | unit | book page | Excerpt |
| --- | --- | --- | --- | --- |
| translation_unit_missing_source_text_zh | cullen:chunk:46 | §33 | 157-157 | §33 Medial [Qi] Factor: 32. There are 1461/4 days in a solar cycle, so the interval between two of the 24 qi into which the cycle is divided is: 1,461/ (4 × 24… |
| translation_unit_missing_source_text_zh | cullen:chunk:57 | §43 | 160-161 | §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how ma… |
| translation_unit_missing_source_text_zh | cullen:chunk:59 | §44 | 161-162 | §44 From the distance from High Origin cast out Origin Coincidence [41,040]. From the remainder, cast out Obscuration Coincidence [2052], and multiply what you… |
| translation_unit_missing_source_text_zh | cullen:chunk:61 | §45 | 163-164 | §45 [T able of year-names] Table 3.2 T able of year-names Celestial Era year-name Terrestrial Era year-name Anthropic Era year-name Obscuration head sexagenary… |
| translation_unit_missing_source_text_zh | cullen:chunk:82 | §64 | 179-179 | §64 Set out the number of the du and parts at conjunction, and add 7 du and (359 + ¾) parts. Cast out the Lodges in succession, and that is the du and parts of… |
| section_intro_footnote_page_or_label_like | cullen:chunk:6 |  | 141-141 | The following text follows the version in Hou Han shu 後漢書 (History of Eastern Han dynasty), Fan Ye 范曄 (398–445 ce), Zhonghua, Beijing: punctuated edition of 19… |
| section_intro_footnote_page_or_label_like | cullen:chunk:7 |  | 141-141 | – 3055 – History of the Later Han dynasty: monograph 3 Pitchpipes and [astronomical] systems: B 1 For a discussion of this table, see Christopher Cullen (2007a… |
| section_intro_footnote_page_or_label_like | cullen:chunk:18 |  | 147-147 | – 3057 – |
| section_intro_contains_chinese | cullen:chunk:1 |  | 139-139 | was introduced, in part we are told because it was not yet possible to decide on a system origin li yuan 曆元 to replace that used by the Triple Concordance. So … |
| section_intro_contains_chinese | cullen:chunk:2 |  | 139-139 | As noted below, the text translated here comes from the third of the monographs originally written by Sima Biao 司馬彪 (c. 240–c. 306 ce), and later incorporated … |

## Longest 20 Chunks

| chunk | type | unit | book page | chars | Excerpt |
| --- | --- | --- | --- | ---: | --- |
| cullen:chunk:66 | translation_unit | §50 | 167-169 | 5268 | 推閏月所在， 以閏餘減章法， 餘以十二乘之， 滿章閏數得一， 滿四以上亦得一筭之數， 從前 年十一月起， 筭盡之外， 閏月也． 或進退， 以中氣定之． §50 Subtract the Intercalation Remainder from Rule Factor [19]. Multiply the remainder by 12. Count one… |
| cullen:chunk:99 | translation_unit | §76 | 184-185 | 3808 | 一術， 以歲數去上元， 餘以為積月， 以百一十二乘之， 滿月數去之， 餘滿食法得一, 則天正後食． §76 Cast out Year Number [513] from [the years since] High Origin. [From the] remainder make Accumulated Months, and multiply by … |
| cullen:chunk:291 | translation_unit | §253 | 224-225 | 3722 | 一刻， 以相增損． 昏明之生， 以天度乘晝漏， 夜漏減(三)[之， 二]百而一， 為 定度． 以減天度， 餘為明；加定度一為昏． 其餘四之， 如法為少． [二為半， 三 為太， ]不盡， 三之， 如法為強， 餘半法以上以成強． 強三為少， 少四為度， 其 強二為少弱也． 又以日度餘為少強， 而各加焉． [一] §253 For producing the … |
| cullen:chunk:71 | translation_unit | §54 | 173-174 | 3578 | 名為積度， 不盡為餘分． 積度加斗二十一度， 加二百三十五分， 以宿次除之, 不滿宿， 則日月合朔所在 (星)[宿] 度也． 求後合朔， 加度二十九， 加分四百九 十九， 分滿蔀月得一度， 經斗除二百三十五分． §54 Set out the Accumulated Months of entry into the Obscuration, multipl… |
| cullen:chunk:4 | section_intro |  | 140-141 | 3477 | Unlike the specification of the Triple Concordance system in the Han shu, the divi- sions of the text, though evident by their content, are not generally marked by any kind of hea… |
| cullen:chunk:57 | translation_unit | §43 | 160-161 | 3122 | §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how many you obtain, then … |
| cullen:chunk:63 | translation_unit | §47 | 165-166 | 3023 | 推天正朔日， 置入蔀積月， 以蔀日乘之， 滿蔀月得一， 名為積日， 不滿為小餘， 積日以六十 除去之， 其餘為大餘， 以所入蔀名命之， 筭盡之外， 則前年天正十一月朔日 也． 小餘四百四十一以上， 其月大． 求後月朔， 加大餘二十九， 小餘四百九十 [九]， 小餘滿蔀月得一， 上加大餘， 命之如前． §47 Set out the Accumulated … |
| cullen:chunk:75 | translation_unit | §58 | 175-177 | 2983 | 推月所在度， 置入蔀積日之數， 以月周乘之， 滿蔀日除去之， 其餘滿蔀法得一， 為積 度， 不盡為餘分． 積度加斗二十一十[九]分， 除如上法， 則所求之日夜半月 所在宿度也． 求次日， 加十三度二十八分． 求次月， 大加三十五度六十一分， 月小二十二度三十三分， 分滿法得一度， 經斗除十九分． 其冬下旬月在張、 心署之， 謂(盡)[晝]漏分後盡漏盡也． … |
| cullen:chunk:28 | translation_unit | §16 | 151-152 | 2939 | 二百五十四周， 復會于端， 是則月行之終也． 以日周除月周， 得一歲周天 之數． 以日一周減之， 餘十二十九分之七， 則月行過周及日行之數也， 為一 歲之月． 以除一歲日， 為一月之數． 月之餘分積滿其法， 得一月， 月成則其 歲[大]． §16 If one examines the sun and moon as together they leave… |
| cullen:chunk:62 | translation_unit | §46 | 164-165 | 2934 | 推天正術， 置入蔀年減一， 以章月乘之， 滿章法得一， 名為積月， 不滿為閏餘， 十二以上, 其歲有閏． §46 Set out the years into the Obscuration and subtract one. Multiply by Rule Months [235]. Count one for each Rule Factor [19… |
| cullen:chunk:298 | translation_unit | §258 | 232-233 | 2840 | 天難諶斯， 是以五、三迄于來今， 各有改作， 不通用． 故黃帝造曆， 元起辛卯， 而顓頊用乙卯， 虞用戊午， 夏用丙寅， 殷用甲寅， 周用丁巳， 魯用庚子． 漢興 承秦， 初用乙卯， 至武帝元封， 不與天合， 乃會術士作太初曆， 元以丁丑． 王莽 之際， 劉歆作三統， 追太初前(世)[卅]一元， 得五星會庚戌之歲， 以為上元． §258 ‘Heaven i… |
| cullen:chunk:23 | translation_unit | §13 | 149-150 | 2828 | 斗之二十一度， 去極至遠也， 日在焉而冬至， 羣物於是乎生． 故律首黃鍾， 曆 始冬至， 月先建子， 時平夜半． §13 The twenty-first du of Dipper is [the position of the Sun when it is at] the maximum distance from the pole. When the … |
| cullen:chunk:68 | translation_unit | §52 | 170-172 | 2804 | 推沒滅術， 置入蔀年減一， 以沒數乘之， 滿日法得一， 名為積沒， 不盡為沒餘． 以通法乘 積沒， 滿沒法得一， 名為大餘， 不盡為小餘． 大餘滿六十除去之， 其餘以蔀名 命之， 筭盡之外， 前年冬至前沒日也． 求後沒， 加大餘六十九， 小餘四， 小餘滿 沒法， 從大餘， 命之如前， 無分為滅． §52 Set out years of entry int… |
| cullen:chunk:67 | translation_unit | §51 | 169-170 | 2783 | 推弦、望日， 因其月朔大小餘之數， 皆加大餘七， 小餘三百五十九四分三， 小餘滿蔀月 得一， 加大餘， 大餘命如法， 得上弦． 又加得望， 次下弦， 又後月朔． 其弦、望 小餘二百六十以下， 每以百刻乘之， 滿蔀月得一刻， 不滿其(數)[所]近節氣 夜漏之半者， 以筭上為日． §51 T ake the numbers for the Greater an… |
| cullen:chunk:49 | translation_unit | §36 | 157-159 | 2727 | 月食數之生也， 乃記月食之既者． 率二十三食而復既， 其月(食)百三十五， 率 之相除， 得五(百)[月]二十三之二十而一食． 以除一歲之月， 得歲有再食五 百一十三分之五十[五]也． 分終其法， 因以與蔀相約， 得四與二十七， 互之， 會二千五十二， 二十而與元會． §36 In producing the numbers for lunar eclip… |
| cullen:chunk:59 | translation_unit | §44 | 161-162 | 2663 | §44 From the distance from High Origin cast out Origin Coincidence [41,040]. From the remainder, cast out Obscuration Coincidence [2052], and multiply what you obtain by 27. Cast … |
| cullen:chunk:13 | translation_unit | §5 | 144-145 | 2659 | 日周于天， 一寒一暑， 四時備成， 萬物畢改， 攝提遷次， 青龍移辰， 謂之歲．歲 首至也， 月首朔也． 至朔同日謂之章， 同在日首謂之蔀， 蔀終六旬謂之紀，歲 朔又復謂之元． 是故日以實之， 月以閏之， 時以分之，歲以周之， 章以明之， 蔀以部之， 紀以記之， 元以原之． 然後雖有變化萬殊， 贏朒無方， 莫不結系于 此而稟正焉． §5 The sun c… |
| cullen:chunk:19 | translation_unit | §10 | 147-148 | 2419 | 而敗之者， 其亡也忽焉． 巍巍乎若道天地之綱紀， 帝王之壯事， 是以聖人寶 焉， 君子勤之． §10 It was Chongli [= Zhuanxu 顓頊, grandson of the Yellow Emperor] who was the first to bestow his august patronage on these methods,… |
| cullen:chunk:300 | translation_unit | §260 | 234-234 | 2322 | 光和元年中， 議郎蔡邕、郎中劉洪補續律曆志， 邕能著文， 清濁鍾律， 洪能為 筭， 述敘三光． 今考論其業， 義指博通， 術數略舉， 是以集錄為上下篇， 放續前 志， 以備一家． §260 In the first year of the Guanghe period [178 ce], the Gentleman for Consulta- tion C… |
| cullen:chunk:289 | section_intro |  | 223-224 | 2241 | Table 3.8 Lodges on the equator and the ecliptic Lodge Equatorial width Advance/retardation Ecliptic width Dou 斗 ‘Dipper’ 26¼ −2 24¼ Niu 牛 ‘Ox’ 8 0 7 Nu 女 ‘Woman’ 12 1 11 Xu 虛 ‘Ba… |

## Shortest 20 Chunks

| chunk | type | unit | book page | chars | Excerpt |
| --- | --- | --- | --- | ---: | --- |
| cullen:chunk:96 | section_intro |  | 183-183 | 2 | 日． |
| cullen:chunk:18 | section_intro |  | 147-147 | 8 | – 3057 – |
| cullen:chunk:27 | section_intro |  | 151-151 | 8 | – 3058 – |
| cullen:chunk:58 | section_intro |  | 161-161 | 8 | eclipse: |
| cullen:chunk:70 | section_intro |  | 173-173 | 8 | – 3064 – |
| cullen:chunk:89 | section_intro |  | 181-181 | 8 | – 3066 – |
| cullen:chunk:101 | section_intro |  | 186-186 | 8 | – 3067 – |
| cullen:chunk:134 | section_intro |  | 194-194 | 8 | – 3068 – |
| cullen:chunk:190 | section_intro |  | 205-205 | 8 | – 3070 – |
| cullen:chunk:210 | section_intro |  | 209-209 | 8 | – 3071 – |
| cullen:chunk:240 | section_intro |  | 213-213 | 8 | – 3072 – |
| cullen:chunk:270 | section_intro |  | 217-217 | 8 | – 3073 – |
| cullen:chunk:290 | section_intro |  | 224-224 | 8 | – 3076 – |
| cullen:chunk:81 | section_intro |  | 179-179 | 10 | full moon: |
| cullen:chunk:84 | section_intro |  | 179-179 | 10 | full moon: |
| cullen:chunk:56 | section_intro |  | 160-160 | 12 | Obscuration: |
| cullen:chunk:93 | section_intro |  | 182-182 | 16 | a lunar eclipse: |
| cullen:chunk:97 | section_intro |  | 183-183 | 17 | the [actual] day: |
| cullen:chunk:39 | translation_unit | §27 | 155-156 | 26 | 日法， 四． §27 Day Factor: 4. |
| cullen:chunk:172 | translation_unit | §147 | 197-197 | 26 | §147 Day Remainder 44,805. |

