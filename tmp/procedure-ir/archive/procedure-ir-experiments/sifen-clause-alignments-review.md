# Sifen Clause Alignments Review

> Clause alignment only. This is not extraction, not gold, and not an interpretation of algorithmic meaning. Commentary clauses are listed separately and are not used in main translation alignment.

## Summary

| Metric | Value |
| --- | ---: |
| Chunks processed | 261 |
| Successful alignments | 715 |
| High confidence | 158 |
| Medium confidence | 247 |
| Low confidence | 310 |
| Unmatched Chinese clauses | 0 |
| Unmatched English clauses | 36 |
| Commentary clauses, not aligned | 484 |

## Chunks To Review First

| chunk | unit | page | procedure | zh | en | low | unmatched zh | unmatched en |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| cullen:chunk:98 | §75 | 183 | Proc. 3.32 | 0 | 10 | 0 | 0 | 10 |
| cullen:chunk:298 | §258 | 232-233 |  | 23 | 15 | 14 | 0 | 0 |
| cullen:chunk:94 | §73 | 182 | Proc. 3.30 | 0 | 5 | 0 | 0 | 5 |
| cullen:chunk:99 | §76 | 184-185 | Proc. 3.33 | 6 | 32 | 3 | 0 | 0 |
| cullen:chunk:16 | §8 | 146-147 |  | 18 | 11 | 11 | 0 | 0 |
| cullen:chunk:293 | §254 | 227-228 | Proc. 3.52 | 0 | 4 | 0 | 0 | 4 |
| cullen:chunk:12 | §4 | 143-144 |  | 19 | 12 | 10 | 0 | 0 |
| cullen:chunk:300 | §260 | 234 |  | 12 | 19 | 10 | 0 | 0 |
| cullen:chunk:13 | §5 | 144-145 |  | 24 | 2 | 2 | 0 | 0 |
| cullen:chunk:19 | §10 | 147-148 |  | 6 | 17 | 6 | 0 | 0 |
| cullen:chunk:23 | §13 | 149-150 |  | 8 | 17 | 7 | 0 | 0 |
| cullen:chunk:66 | §50 | 167-169 | Proc. 3.9 | 10 | 17 | 8 | 0 | 0 |
| cullen:chunk:85 | §66 | 179 | Proc. 3.25 | 0 | 3 | 0 | 0 | 3 |
| cullen:chunk:15 | §7 | 146 |  | 12 | 10 | 10 | 0 | 0 |
| cullen:chunk:28 | §16 | 151-152 |  | 14 | 14 | 11 | 0 | 0 |
| cullen:chunk:294 | §255 | 228-231 | Proc. 3.53 | 18 | 16 | 10 | 0 | 0 |
| cullen:chunk:297 | §257 | 232 |  | 14 | 8 | 8 | 0 | 0 |
| cullen:chunk:299 | §259 | 233-234 |  | 18 | 9 | 6 | 0 | 0 |
| cullen:chunk:26 | §15 | 151 |  | 15 | 9 | 7 | 0 | 0 |
| cullen:chunk:25 | §14 | 150-151 |  | 10 | 13 | 8 | 0 | 0 |

## Alignments By Chunk

### cullen:chunk:8 §1 p.142 

Clauses: zh=10, en=2, commentary=12

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | many_to_one | 昔者聖人之作曆也 / 觀琁璣之運 / 三光之行 / 道之發斂 / 景之長短 | §1 When in former times the sages created [astronomical] systems, they watched the turning of the xuan ji, the motions of the Three Luminaries, the expansion and contraction of the Roads, the growing and shrinking of the shadow, the establishment of the Dipper mainstay, and the orbit of the Caerulean Dragon. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 38 | many_to_one | 斗綱 (之)[所]建 / 青龍所躔 / 參伍以變 / 錯綜其數 / 而制術焉 | The Three [Luminaries] and the Five [Planets] changed [their positions], and they wove together the numbers, so that they were able to make them into methods [for calculation]. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This introduction underlines a radical difference of approach between its authors and Liu Xin, creator of the Triple Concordance system.
- Whereas he claimed to have derived the constants of his system from cosmological con- siderations, this system claims that its basic data are drawn from observation.
- This approach, it is claimed, represents a return to the practice of the ancient sages who created human culture in the mythical past.
- Some of the terms used here require a little explanation.
- ‘ Xuan ji’ refers to the pole star of the Han period, β Ursae minoris;

### cullen:chunk:9 §2 p.142-143 

Clauses: zh=11, en=5, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | many_to_one | 天之動也 / 一晝一夜而運過周 | §2 In the movement of Heaven, the turning in one day and night is more than a circuit. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 45 | many_to_one | 星從天而西 / 日違天而東 | The stars follow Heaven in moving westwards, while the sun goes against Heaven in moving eastwards. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 日之所行與運周 / 在 天成度 | The motion of the sun and its turning round its circuit forms the du in Heaven and the days in the system. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 在曆成日 / 居以列宿 | It dwells in the ordered lodges, which terminate in four sevens; | sequential_baseline_alignment, order_proximity |
| aligned | low | 42 | many_to_one | 終于四七 / 受以甲乙 / 終于六旬 | it is received in the cyclical signs, which terminate in six decades. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- The expression ‘one day and night’ refers to a complete solar day, in which the sun returns to the same position relative to the observer.
- If we count from the moment of noon, this is the interval between two instants when the sun is on the meridian due south of the observer.
- If we count from the moment of midnight, the sun is still crossing the meridian line, but below the horizon in the north.
- The statement that ‘the turning in one day and night is more than a circuit’ refers to the fact that since the sun is moving from west to east against the background of the celestial sphere with the fixed stars (which turns from east to west), it follows that from one noon to the next (or one midnight to the next), since the sun has returned to the same position relative to the observe, the celestial sphere has turned a full revolution, plus the sun’s daily motion, which is in fact 1 du.

### cullen:chunk:10 §3 p.143 

Clauses: zh=15, en=8, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | many_to_one | 謂之合朔 / 舒先速後 | When they share a position, that is called a conjunction. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | medium | 54 | many_to_one | 近一遠三 / 謂之弦. 相與為衡 | The slow [i.e. the sun] is ahead and the fast [i.e. the moon] is behind. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | many_to_one | 分天之中 / 謂之望 | When they are one part near and three parts distant, that is called a crescent. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | medium | 54 | many_to_one | 謂之晦 / 晦朔合離 | When the fast reaches the slow, so that its bril - liance is exhausted and its form is hidden, that is called darkening [as on the last day of a lunar month]. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | medium | 54 | many_to_one | 斗建 移辰 / 謂之[月] | When darkening and conjunction have joined and separated, and the Dipper Establishment shifts by a sign, that is called a month. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | low | 46 | one_to_one | 日月相推 | §3 ‘The sun and moon push one another on’. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 日舒月速 / 當其同[所] | The sun is slow and the moon is fast. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 以速及舒 / 光盡體伏 | When they are opposite one another, so that they divide Heaven down the middle, that is called opposition. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- The first sentence refers to the Book of Change, which contains the following passage:

### cullen:chunk:12 §4 p.143-144 

Clauses: zh=19, en=12, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 55 | many_to_one | 是故日行北陸謂之 冬 / 西陸謂之春 | through the western regions it is called spring; | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | medium | 55 | one_to_one | 南陸謂之夏 | through the southern regions it is called summer, and through the eastern regions it is called autumn. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | low | 46 | one_to_one | 日月之(術)[行] | §4 Through the motion of the sun and moon, there is winter and there is sum - mer. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 則有冬有夏 / 冬夏之閒 | Between winter and summer, there is spring and there is autumn. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 則有春有秋 | Thus when the sun moves through the northern regions, that is called winter; | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 東陸謂之秋 / 日道發南 | When the sun’s path extends out southwards, it goes ever further from the pole, and the shadow becomes ever longer, and when distance and length reach their extreme, then winter culminates there. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 去極彌遠 / 其景彌長, 遠長乃極 | When the sun’s path draws in towards the north, it goes ever closer to the pole, and the shadow is ever shorter, and when nearness and shortness reach their extreme, then summer culminates there. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 冬乃至焉 | Between the two extremes [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 日道斂北 / 去極彌近 | ‘solstices’], the path is even and the shadow is true, and spring and autumn are divided there. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 其景彌短 | The ‘regions’ through which the sun moves are the four quarters of the heavenly sphere corresponding to its position during the four seasons. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 近短乃極 / 夏乃至焉. 二至之中 | The labelling as ‘north’ and so forth in the third sentence is conventional rather than directional. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 道齊景正 / 春秋分焉 | The meaning becomes literal in the rest of the section, where it is stated that when the sun is at its northernmost the season is summer, and when it is at its southernmost the seasons is winter. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:13 §5 p.144-145 

Clauses: zh=24, en=2, commentary=22

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 39 | many_to_one | 日周于天 / 一寒一暑 / 四時備成 / 萬物畢改 / 攝提遷次 / 青龍移辰 / 謂之歲 / 歲 首至也 / 月首朔也 / 至朔同日謂之章 / 同在日首謂之蔀 / 蔀終六旬謂之紀 | §5 The sun circuits round Heaven: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 39 | many_to_one | 歲 朔又復謂之元 / 是故日以實之 / 月以閏之 / 時以分之 / 歲以周之 / 章以明之 / 蔀以部之 / 紀以記之 / 元以原之 / 然後雖有變化萬殊 / 贏朒無方 / 莫不結系于 此而稟正焉 | there is one cold and one heat, the four seasons are all complete, the myriad creatures are all changed, the sheti [i.e. the 12 cyclical characters referring to years] shift their station, and the Cae - rulean Dragon [i.e. the sexagenary name of the year] moves its mark-point. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

Commentary, not aligned:
- This is called a sui.
- The head of the sui is the [winter] solstice, and the head of the yue is the conjunction.
- When the solstice and the conjunction fall on the same day, that is called a Rule [Head].When this takes place at the head of a day [i.e. midnight], this is called an Obscuration [Head].
- When an Obscuration has terminated the six decades, that is called an Era [Head].
- When the sui and the conjunction both return, that is called an Origin [Head].

### cullen:chunk:14 §6 p.145-146 

Clauses: zh=10, en=1, commentary=13

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 38 | many_to_one | 極建其中 / 道營于外 / 琁衡追日 / 以察[發]斂 / 光道生焉 / 孔壺為漏 / 浮箭為 刻 / 下漏數刻 / 以考中星 / 昏明生焉 | §6 The pole is established in the centre, and the Roads are constructed outside. | sequential_baseline_alignment, definition_make_or_is |

Commentary, not aligned:
- The Xuan and Heng pursue the sun, 3 and by investigating its outwards and inwards [displacement], the Brilliant Road is created.
- The perforated vessel performs its dripping, and the floating arrow makes its divisions.
- One lets the drips go down and counts the divisions, and by examining the centred stars, dusk and dawn are created.
- Here and in the next section, ‘Brilliant Road’ is an alternative name for the ecliptic, elsewhere referred to as huang dao 黃道 ‘The Yellow Road’.
- The ‘perforated ves - sel’ is a simple outflow clepsydra, with the aid of which we are to time the 3 On these terms, see again Christopher Cullen and Anne S.

### cullen:chunk:15 §7 p.146 

Clauses: zh=12, en=10, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 日有光道 | §7 The sun has its Brilliant Road, and the Moon has its Nine Ways. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 月有九行 | The Nine Ways go out and in, and the Nodes are produced thereby. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 九行出入而交生焉 | When the meeting at conjunction and the diametricality at opposition are near to the position of the Nodes, then waning and concealment [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 朔會望衡 | solar or lunar eclipses] are produced thereby. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 鄰於所交 / 虧薄生焉 | The Moon has its darkening and conjunction; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 月 有晦朔 | stars [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 星有合見 | plan- ets] have their conjunction and appearance; | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 月有弦望 | the Moon has its crescent and full, stars [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 星有留逆 | planets] have their stationary points and retrogradation. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 其歸一也 / 步術生焉 | They all go back to a single [basis], and predictive methods are produced thereby. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- In this section, the jiu dao 九道 ‘Nine Roads’ clearly refer to the moon, whereas in the Triple Concordance they appeared to refer to the sun.
- The topic of the nodes (the points where the moon’s path crosses the ecliptic) does not recur later in this text.
- See however the discussion in relation to Jia Kui’s work c. 100 ce, in the document collection of Cai Yong and Liu Hong elsewhere in the Hou Han shu, translated later in this book in Chapt er 5.

### cullen:chunk:16 §8 p.146-147 

Clauses: zh=18, en=11, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 金、水承陽 | §8 Metal [Mercury] and Water [Venus] sustain Yang, and precede and follow beneath the sun. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 先後日下 / 速則先日 | When they are fast they precede the sun, and when they are slow they begin to lag. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 遲而後留 | When they lag they retrograde, and retrograding they transgress against the sun. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 留而後逆 / 逆與日違 | After retrograding they speed up, and speeding up they go neck and neck with the sun, and after going neck and neck they precede the sun again. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 違而後速, 速與日競 / 競又先日 | Slowing and speeding up, direct and retrograde motion, dawn and dusk [visibility] are thereby produced. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 遲速順逆 | The Sun, Moon and Five Wefts [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 晨夕生焉 / 日、月、五緯各有終原 | planets] each have their terminations and starting points, and the Seven Origins are thereby produced. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 而七元生 焉 / 見伏有日 | Appearance and disappearance [of plan- ets] have their days, stationary points and movement have their degrees, and the numerical proportions are thereby produced. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 留行有度 | That which not uniform one 4 See also Cullen (forthcoming), chapter 5. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 而率數生焉 / 參差齊之 | evens out; | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 多少均之 / 會終生焉 | that which is greater or lesser one equalises, and compatibility and completion is produced thereby. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- The reference in the last sentence is apparently to the ways in which observational data are evaluated to produce constants for the mean movements of planets, as specified later in this text.

### cullen:chunk:17 §9 p.147 

Clauses: zh=9, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 42 | many_to_one | 引而伸之 / 觸而長之 / 探賾索隱 | §9 So [as in the words of the Book of Change] one ‘draws forth the general [from the particular], and on coming across some [category] 5 one expands it’; | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 鉤深致遠 / 無幽辟潛伏 / 而不以其精者 然.故陰陽有分 | ‘one seeks out the profound and draws forth the obscure, hooks out the deep and brings near the distant’, so that there is nothing that is recondite or hidden, whatever its subtlety may be. | sequential_baseline_alignment, order_proximity |
| aligned | low | 42 | many_to_one | 寒暑有節 / 天地貞觀 / 日月貞明 | So Yin and Yang have their division, cold and heat have their regularities, ‘Heaven and Earth are made authentically manifest, and the Sun and Moon are made authentically brilliant.’ | sequential_baseline_alignment, order_proximity |

### cullen:chunk:19 §10 p.147-148 

Clauses: zh=6, en=17, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 44 | one_to_many | 而敗之者 | §10 It was Chongli [= Zhuanxu 顓頊, grandson of the Yellow Emperor] who was the first to bestow his august patronage on these methods, inaugurate this heritage and make the Heavenly brilliance pure and radiant. / It was Xi and He who played a glorious part in taking up the Sage Lord’s command to accord with august Heaven, to set up canons, sequences and counterparts for the Three Markers [the sun, moon and stars], in order to grant their tasks to the people, setting up intercalations to correct the seasons, and thus completing the year’s accomplishments. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 其亡也忽焉 | It was [King] Tang and [King] Wu 5 The text of the Book of Change, from which this quotation is drawn, has 類 here: / see Zhou yi, Xi ci A, 7, 22b–23a in edition of Ruan Yuan 阮元 (1973 reprint of original of 1815) Shi san jing zhu shu 十三經註疏 (The thirteen classics with commentaries and subcommentaries) . / Taipei, Yiwen Press, 153–154. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 巍巍乎若道天地之綱紀 | who achieved complete success in taking Metal and Fire as their counterparts,6 changing the Mandate and creating ordinances, regulating the calendar and making clear the seasons, being responsive to Heaven and making the people amenable. / But then it came to the time of decay of kingly virtue, when above there was disorder by rulers who lacked the Way, and below stupid Clerks lost [the thread]. / In the time of Xiahou [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_many | 帝王之壯事 | the Xia dynasty], the Xi and He officials were debauched by wine, abandoning the seasons and disordering the days, whereupon [the marquis of] Yin proceeded against them. / Tchou 7 [last Ruler of the Shang dynasty] was debauched and tyran - nous, abandoning the sexagenary sequence of days, and King Wu punished him. / For one who is able to clarify these matters authentically, their rise is swift; | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_many | 是以聖人寶 焉 | for those who turn back and do harm, their fall is sudden. / How great it is, like telling of the sustaining cords of Heaven and Earth, and the solid work of Lords and Kings. / Thus the Sage treasures these things, and the Gentlemen exerts his diligence therein. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_many | 君子勤之 | The basis element of this story, which takes us from mythical rulers of High Antiquity down to the undoubtedly historical early kings of the Zhou dynasty c. 1 046 bce, are repeated in a number of accounts such as the present one. / See also the material from the Han shu translated in Chap ter 5. / The point being made is that good and effective rulers ensure that effective astronomical systems are adopted. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:20 §11 p.148 

Clauses: zh=7, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 夫曆有聖人之德六焉 | §11 There are six ways in which the virtue of the Sage is contained in an [astronomical] system. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 以本氣者尚其體 | By taking the qi as basic, it exalts the form [of Heaven]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以綜數者尚其文 | By threading together the numbers, it exalts the patterns [of Heaven]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以考類者尚其 象 | By examining the categories, it exalts the counterparts [of Heaven]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以作事者尚其時 | By carrying out its task, it exalts the seasons [of Heaven]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以占往者尚其源 | By divining from what is past, it exalts the source, [which is Heaven]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以知來者尚其流 | By knowing what is to come, it exalts the onwards movement [of Heaven]. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:22 §12 p.149 

Clauses: zh=5, en=1, commentary=5

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 33 | many_to_one | 帝王之大司備矣 / 天下之能事畢矣 / 過此而往 / 羣忌苟禁 / 君子未之或 知也 | §12 The Great Task sustains it, and good and evil fortune come forth from it. | sequential_baseline_alignment |

Commentary, not aligned:
- Therefore, when the gentleman is to undertake some new matter, he looks into it in order to be able to carry on his work;
- he accepts the Mandate and does not go against it.
- For making use of Heaven and basing oneself upon Earth, for judging the seasons and proclaiming the teaching, so that it can be told forth in the Hall of Holiness, to be the people’s Ultimate, nothing is greater than the Monthly Ordinances.
- 8 [In them] the great charges of emperors and kings are complete, and all the most demanding affairs of the Empire are accomplished.
- If one goes outside these [limits], fears and confusions abound intolerably and no gentleman has ever known of it.

### cullen:chunk:23 §13 p.149-150 

Clauses: zh=8, en=17, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | one_to_many | 斗之二十一度 | §13 The twenty-first du of Dipper is [the position of the Sun when it is at] the maximum distance from the pole. / When the sun is situated there it is the winter solstice: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 45 | one_to_many | 去極至遠也 | that is the time when all things begin to be produced. / Thus the head of the pitch-pipes is Yellow Bell, [astronomical] systems begin from winter solstice, the months give precedence to the establishment zi [the 11th month in the ‘Xia’ count used today, the first Celestial month], and time of day is made even with midnight. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 日在焉而冬至 | The Triple Concordance system placed the sun at the start of the lodge Ox at the winter solstice. / This would have corresponded closely to reality around 450 bce, when the two bright stars of Ox, β and α Capricorni, would have been close to longitude 270°, and hence on the winter solsticial colure. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 羣物於是乎生 | It is however important to realise that the winter solstice position of the sun is not directly observable by the naked eye, but can only be deduced indirectly, by (for instance) observing the stars crossing the meridian at midnight at the summer solstice, an observation which is crucially dependent on accurate time measurement. / It would therefore be unsafe to assume that the use of Ox as a winter solstice marker reflects actual observation in the mid-fifth-century bce. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 故律首黃鍾 | By around 50 ce precession had changed the longitude of these stars to about 277°, since the winter solstice position had 8 T exts under the name of Yue ling 月令 ‘Monthly Ordinances’ are known from the pre-imperial age. / See for instance Lü shi chun qiu 呂氏春秋 (Mr. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 曆 始冬至 | Lü’ s Spring and Autumn [Annals]), where a series of chapters give ritual observances appropriate to the 12 lunar months of the civil year, preceded by statements of astronomical conditions, including the lodge in which the sun is to be found in that month, and which lodges are ‘centred’ at dawn and dusk. / If the prescribed observances are not followed, we are told, misfortune for the state will follow. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 月先建子 | Since a lunar month can shift by up to 30 days in relation to the seasons (hence the necessity for intercalation), the stated astronomical condi- tions will only apply approximately to any given month. / shifted westwards to the preceding lodge, Dipper. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_many | 時平夜半 | Dipper was (according to the Han Quarter Remainder system) 26¼ du in width, so that the position given here was not a bad estimate, since it implied that the winter solstice was about 5 du (close to 5º) to the west of the start of Ox, and the actual distance was similar, at about 7 du. / The fact that that Liu Xin still used the position at the start of Ox when he constructed the Triple Concordance suggests that this datum was accepted on the basis of tradition rather than observation. / In 92 ce Jia Kui noted that different systems had used different winter solstice positions: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:25 §14 p.150-151 

Clauses: zh=10, en=13, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 當漢高皇帝受命四十有五歲 | §14 In the forty-fifth year after the High Sovereign Emperor of Han received the mandate, when the Yang was at shangzhang [the seventh of its 10 posi- tions], and the Yin was at zhixu [its fifth position out of 12], in winter, the eleventh month, day jiazi.1, at midnight, the moment of conjunction [occurred at the same time as] the winter solstice. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | one_to_one | 而月食五 星之元 | See Cullen (forthcoming), chapter 3. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 陽在上章 | The reckonings of the sun, moon and accumulation of intercalations starts from this point. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 陰在執徐 | It establishes the origin and standardises the conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 冬十有一月甲子夜半朔 旦冬至 | This is called the Han System. / Going back a further two Origins, then that is the origin for lunar eclipses and the five planets, which all start from this point. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 日月閏積之數皆自此始 | The instant of System Origin here defined is December 25, 162 bce, at midnight local time at Luoyang (longitude 112° 37.8’ E), Julian Day Number 1,662,610.18750. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 立元正朔 | Two Origins back takes us to Luoyang midnight beginning December 25, 9281 bce, Julian Day Number −1,668,469.81250. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 謂之漢曆 | Shangzhang is the seventh of 10 possible positions for Yang, corresponding to the stem geng 庚, while zhixu corresponds to 9 Thes e are five of the ‘six ancient systems’ that by the end of Western Han were thought to have been in use in pre-imperial times, together with the Zhuan Xu system. / The latter was named after supposed ancestor of the Qin royal house, who was the grandson of the mythical Yellow Emperor. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 又上兩元 | However it is unlikely that these systems date back to pre-imperial times, rather than being more recent creations. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 並發端焉 | the seventh of 12 possible Yin positions, corresponding to the branch chen 辰. / The sexagenary name of the year is thus gengchen.17, which is indeed the name cor- responding to the civil year that began in spring of 161 bce, after the winter solstice at system origin in late 162 bce. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:26 §15 p.151 

Clauses: zh=15, en=9, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | one_to_one | 日發其 端,周而為歲 | The sun sets out from that starting point, and makes a sui when it has circuited. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | many_to_one | 得三百六十五四分度之一 / 為歲之日數 | The sun moves one du in a day, so [this figure] is also the du in [a circuit of] the heavens. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 曆數之生也 | §15 In the process of producing the numbers of the astronomical system, one sets up [armillary] instruments and gnomons,10 in order to compare the solar shadows. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 乃立儀、表 / 以校日景 | When the shadow is longest the sun is most distant; | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 景長則日遠 / 天度之端也 | this is the starting point for the degrees of heaven. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 然其景不復 / 四周千四百六十一日 | However the shadow does not return: | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 而景復初 / 是則日行之終 | the shadow returns to its starting point after four circuits, 1461 days, and so this represents the termination of the sun’s motion. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 以周除日 | Casting out circuits from the days, one obtains 365 and ¼, which is the number of days in a sui. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 日日行一度 / 亦為天度 | ‘Sui’ here clearly means ‘solar cycle’ rather than ‘year’. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:28 §16 p.151-152 

Clauses: zh=14, en=14, commentary=9

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 二百五十四周 | §16 If one examines the sun and moon as together they leave the starting point for du, when the sun has travelled 19 circuits, and the moon has travelled 254 circuits, they meet once more at the starting point. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 54 | one_to_one | 餘十二十九分之七 | New York, Cambridge University Press, 103. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 56 | one_to_one | 月之餘分積滿其法 | Casting out one solar circuit from that leaves a remainder of 12 7/19 which is the number of times the moon moves through more than a circuit and meets the sun, which is the number of lunations in a solar cycle. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | low | 46 | one_to_one | 復會于端 | When this [happens], 10 I t would be possible to take yi biao 儀表 as a single expression ‘instrumental gnomons’, rather than punctuating to produce two separate things that are to be ‘set up’, since nothing else but a gnomon is required for the purpose in hand. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 是則月行之終也 | At one point the Zhou bi book, assembled around the end of the Western Han, refers to a movable gnomon used to establish a sight line as a you yi 游儀 ‘movable instrument’; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以日周除月周 | see Christopher Cullen (1996) Astronomy and mathematics in ancient China: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 得一歲周天 之數 | the Zhou bi suan jing. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以日一周減之 | Cambridge; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 則月行過周及日行之數也 | But in Proc. 3.51, the same expression occurs in a context where north polar distance is to be measured, which does require an armillary instrument; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 為一 歲之月 | hence the rendering chosen here. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以除一歲日 | it is the termination of lunar motion. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 為一月之數 | Casting out solar circuits from lunar circuits, one obtains the number of [lunar] circuits in a solar cycle. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 得一月 | If [by that quan- tity] one casts out from the days in a solar cycle, that makes the number [of days in] a lunation. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 月成則其 歲[大] | When the remainder parts of lunations [in a solar cycle] fill the factor, one gets a month, and when a month is formed the year is a large one [i.e. with an intercalary month]. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This section describes the astronomical basis and implications of the Rule Cycle, which will be referred to in section § 18, and is also used in the other two systems translated in this book.
- Since the moon will actually move past the sun 254 − 19 = 235 times, the implication is that 19 solar cycles are precisely equal in duration to 235 lunations.
- Since 235 = 19 in 12 + 7, we must insert seven intercalary lunar months in the course of 19 civil years in order to maintain correspondence between the months and the seasons.
- 254/19 = 13 + 7⁄19, the number of lunar circuits of heaven in a solar cycle.
- Thus 12 + 7⁄19 is the number of lunations in a solar cycle.

### cullen:chunk:29 §17 p.152-153 

Clauses: zh=14, en=12, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 月(大)四時推移 | §17 In the case of months, the four seasons shift [in relation to them], and so one sets out the 12 Medial [Qi] in order to fix the places of the months. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 55 | one_to_one | 有朔而無中者為閏月 | The start of a Medial [Qi] is called a Nodal [Qi], and together with the Medials these make the 24 qi. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 55 | one_to_one | 與中為二十四氣 | If the fractions accu- mulate to complete one day, that makes an Extinction. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | many_to_one | 以除一歲日 / 為一氣之日數也 | If one adds up the fractions of the qi of a year, then if these accord with their factor, that makes one Year Extinction. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 56 | one_to_one | 其分積而成日為 沒 | The Extinction fractions are divided amongst the terminating Medials; | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 55 | one_to_one | 如法為一歲沒 | When the fractions at the winter solstice accumulate to accord with their factor, one gets one day, and this is concluded after four years. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 69 | many_to_one | 冬至之分積如其 法得一日 / 四歲而終 | (365 ¼) /2 4 = 15 7⁄32 The meaning and application of the term ‘Extinction’ is made clear in detail in Proc. 3.11. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 故置十二中以定月位 | When a conjunction occurs without a Medial [Qi], that makes an intercalary month. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 中之始(日) [曰]節 | If by this one casts out from the days of one year, that makes the number of days in one qi. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 并歲氣之分 | the Medials are terminated at the winter solstice. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 沒分于終中 | We have already met the ‘no medial qi’ rule for intercalation in the Triple Concor- dance system. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 中終于冬至 | The number of days in one Qi is: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:30 §18 p.153 

Clauses: zh=13, en=16, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 閏七而盡 | The years are 19, which is called a Rule. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 54 | one_to_one | 四之俱終 | So 20 Obscurations make an Era. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 55 | one_to_one | 為蔀之日數也 | In the first two sentences, we are reminded that seven intercalations take place in a Rule cycle of 19 years. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 56 | one_to_many | 以甲子命之 | Since however 19 solar cycles are 365¼ days × 19 = 6939¾ days we shall have to finish four Rules – an Obscuration, 76 years – before we have a whole number of days, and winter solstice and conjunction once more coincide at midnight. / Since an Obscuration contains 27,759 days, we shall need 20 Obscurations – an Era, 1520 years – before the days elapsed are a multiple of 60 and the sexagenary day name repeats. | sequential_baseline_alignment, order_proximity, operation_count_or_name |
| aligned | medium | 54 | one_to_one | 二十而復其初 | But since 1520 is not a multiple of 60, we need three Eras – an Origin, 4560 years – before the sexagenary year number returns to system origin conditions. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 55 | one_to_one | 是以二十蔀為 紀 | This section makes it plain that the term ‘Caerulean Dragon’ is being used as a name for the sexagenary year-name. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 69 | one_to_many | 三終歲後復青龍為元 | see (Huai nan hong lie ji jie 3, 125–126) and (Major, John S., with an appendix by Christopher Cullen 1993: / 133–135). | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 月分成閏 | §18 The fractions of a lunation complete an intercalation, and these intercalations are exhausted after seven. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 其歲十九 | When the fractions at the head of a Rule are exhausted, and the fours are all terminated, this is called an Obscuration. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 名之曰章 | If one multiplies by the days of one year, this is the number of days of an Obscuration. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 章首分盡 | If one counts off by the sexagenary day name [lit. / ‘the jiazi’], it returns to the beginning [after] 20. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 名之曰蔀. 以一歲日乘之 | In the years of an Era the Caerulean Dragon is not yet concluded, so after three completions of [this number of] years one returns to the Caerulean Dragon, making an Origin. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 紀歲青龍未終 | This usage can be traced back to the Huai nan zi book in the second century bce: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:31 §19 p.154 

Clauses: zh=2, en=2, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四千五百六十 | 4560. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 元法 | §19 Origin Factor: | sequential_baseline_alignment, order_proximity, term_origin_factor |

Commentary, not aligned:
- 4560 = 76 × 60, so the sexagenary name of the year repeats after Origin Factor years.
- 4560 × 365¼ = 1,665,540 = 27,759 × 60, so the sexagenary day name repeats after Origin Factor solar cycles, which is a whole number of days.
- 4560 × 235/19 = 56,400, so this period also contains a whole number of luna - tions, ensuring that Origin Factor years after System Origin, winter solstice and conjunction once more coincide at midnight.

### cullen:chunk:32 §20 p.154 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 千五百二十 | 1520. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 紀法 | §20 Era Factor: | sequential_baseline_alignment, order_proximity, term_era_factor |

Commentary, not aligned:
- 1520 = 25 × 60 + 20, so the sexagenary name of the year advances by 20 after Era Factor years.
- However the sexagenary day name remains the same, and Era Factor years after System Origin, winter solstice and conjunction once more coincide at midnight.

### cullen:chunk:33 §21 p.154 

Clauses: zh=2, en=2, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 萬八千八百 | 18,800. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 紀月 | §21 Era Months: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- As in the Triple Concordance, we assume that 235 lunations is equal to 19 solar cycles.
- So in Era Factor [1520] years, there are:
- 1520 × 235/19 = 18,800 months

### cullen:chunk:34 §22 p.154 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 七十六 | 76. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 蔀法 | §22 Obscuration Factor: | sequential_baseline_alignment, order_proximity, term_obscuration_factor |

Commentary, not aligned:
- 76 × 365¼ = 27,759, so Obscuration Factor solar cycles is a whole number of days.
- Thus Obscuration Factor years after System Origin, winter solstice once more falls at midnight.

### cullen:chunk:35 §23 p.154-155 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 九百四十 | 940. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 蔀月 | §23 Obscuration Months: | sequential_baseline_alignment, order_proximity, term_rule_months |

Commentary, not aligned:
- 76 × 235/19 = 940 so Obscuration Factor solar cycles is a whole number of lunations.
- Thus Obscuration Factor years after System Origin, conjunction once more coincides with winter solstice at midnight.

### cullen:chunk:36 §24 p.155 

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 十九 | 19. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 章法 | §24 Rule Factor: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Both this constant and the next are the same as those in the Triple Concordance, and function to define the placing of intercalary months.

### cullen:chunk:37 §25 p.155 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 二百三十五 | 235. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 章月 | §25 Rule Months: | sequential_baseline_alignment, order_proximity, term_rule_months |

Commentary, not aligned:
- This is the number of lunations precisely equivalent to Rule Factor [19] solar cycles;
- we may also say that 19 civil years contain 235 months, of which 235 − 19 × 12 = 7 will be intercalary

### cullen:chunk:38 §26 p.155 

Clauses: zh=2, en=2, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 千四百六十一 | 1461. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 周天 | §26 Circuits of Heaven: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- 1461 = 365¼ × 4 This is the number of days in a solar cycle at a scale of Day Factor [4] – or alterna- tively the number of days in 4 solar cycles, which is a whole number.
- Since an Obscuration is 4 × 19 = 76 years, which contain 4 × 235 = 940 lunations, an Obscuration contains 19 × 1461 days.
- Thus the mean length of a lunation is 19 × 1461/940 days = 29 499⁄940 days.
- Each (1/19) of a month is clearly 1461/940 days, so multiplying by Circuits of Heaven [1461] converts months at a scale of 19 to days at a scale of 940.

### cullen:chunk:39 §27 p.155-156 

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四 | 4. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 日法 | §27 Day Factor: | sequential_baseline_alignment, order_proximity, term_day_factor |

### cullen:chunk:40 §28 p.156 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 二萬七千七百五十九 | 27,759. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 蔀日 | §28 Obscuration Days: | sequential_baseline_alignment, order_proximity, term_rule_days |

Commentary, not aligned:
- This is the number of days in Obscuration Factor [76] solar cycles, or Obscuration Factor [76] civil years:
- see section § 22.

### cullen:chunk:41 §29 p.156 

Clauses: zh=3, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 二十一 / (為章閏)11 | 21. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 沒數 | §29 Extinction Number: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- For the use of this factor, see Proc. 3.11.

### cullen:chunk:42 §30 p.156 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四百八十七 | 487. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 通法 | §30 Compatibility Factor: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This is Circuits of Heaven [1461] divided by 3, which is 4/3 the number of days in a year.
- For its use, see Proc. 3.11 and Proc. 3.12.

### cullen:chunk:43 §31 p.156 

Clauses: zh=3, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 七 / (因為章閏).12 | 7. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 沒法 | §31 Extinction Factor: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- See Proc. 3.11.

### cullen:chunk:44 §32 p.156 

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 百六十八 | 168. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 68 | one_to_one | 日餘 | §32 Day Remainder: | sequential_baseline_alignment, order_proximity, term_day_remainder, result_remainder |

Commentary, not aligned:
- See Proc. 3.8 for the use of this factor.

### cullen:chunk:46 §33 p.157 

Clauses: zh=0, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §33 Medial [Qi] Factor: |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | 32. |  |

Commentary, not aligned:
- There are 1461/4 days in a solar cycle, so the interval between two of the 24 qi into which the cycle is divided is:
- 1,461/ (4 × 24) days = 487⁄32 days = 15 7⁄32 days So that is 487 days at a scale of Medial Qi Factor.

### cullen:chunk:47 §34 p.157 

Clauses: zh=2, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 三十四萬三千三百三十五 | 343,335. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 大周 | §34 Greater Circuits: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This is the number of days in a year at a scale of Obscuration Months [940], since 343,335/940 = 365 + ¼.
- This figure is convenient when dealing with cal - culations involving days and months, since the factor for days in months is also Obscuration Months [940].

### cullen:chunk:48 §35 p.157 

Clauses: zh=1, en=2, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | one_to_many | 月周千一十六 | §35 Lunar Circuits: / 1016. | sequential_baseline_alignment, number_exact_match |

Commentary, not aligned:
- This is the number of circuits of Heaven performed by the moon in one Obscuration.
- It is found from the fact that there are 235 mean conjunctions in a Rule, during which the sun performs 19 circuits of Heaven, so the lunar circuits are 235 + 19 = 254.
- and there are four Rules of 19 years in each Obscuration of 76 years.
- 4 × 254 = 1016.

### cullen:chunk:49 §36 p.157-159 Proc. 3.1

Clauses: zh=14, en=6, commentary=20

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 75 | many_to_one | 率二十三食而復既 / 其月(食)百三十五 | The rate is that after 23 eclipses totality returns, and the months are 135. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | high | 100 | many_to_one | 率 之相除 / 得五(百)[月]二十三之二十而一食 / 以除一歲之月 | If the rates are cast out, one gets one eclipse per 5 20/23 months. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, number_exact_match, operation_cast_out_or_divide, operation_obtain |
| aligned | high | 86 | many_to_one | 因以與蔀相約 / 得四與二十七 | When the fractions terminate their factor, and one makes this compatible with the Obscuration, one gets 4 and 27. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, operation_obtain |
| aligned | high | 85 | many_to_one | 互之 / 會二千五十二 / 二十而與元會 | Changing it round, the Concidence [occurs at] 2052, and in 20 of these there is Coincidence with the Origin. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, term_coincidence |
| aligned | medium | 53 | many_to_one | 得歲有再食五 百一十三分之五十[五]也 / 分終其法 | If by that one casts out from the months of a year, one finds that in a year there are 2 55/513 eclipses. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 44 | many_to_one | 月食數之生也 / 乃記月食之既者 | §36 In producing the numbers for lunar eclipses, one records instances where the lunar eclipse is total. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This is how the figures work out:
- The notion of a cycle of 23 lunar eclipses in 135 months predates the Eastern Han.
- The cycle begins with a lunar eclipse at the full moon of the first month of the cycle, and the last eclipse falls at the full moon of the 131st month.
- The next lunar eclipse is at full moon of the first month of the next 135- month cycle.
- 135/23 = 5 + 20/23, so this is the mean number of months between eclipses – although actual eclipses must of course be separated by whole numbers of months, since they must fall at full moon.

### cullen:chunk:50 §37 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四萬一千四十 | 41,040. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 元會 | §37 Origin Coincidence: | sequential_baseline_alignment, order_proximity, term_coincidence |

Commentary, not aligned:
- 41,040 = 20 × Obscuration Coincidences [2052]

### cullen:chunk:51 §38 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 蔀會 | §38 Obscuration Coincidence: | sequential_baseline_alignment, order_proximity, term_coincidence |
| aligned | medium | 54 | one_to_one | (三)[二]千五十(三)[二] | 2052. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

Commentary, not aligned:
- 2052 = 27 × Obscuration Factor [76] = 27 × 4 × 19

### cullen:chunk:52 §39 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 五百一十三 | 513. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 歲數 | §39 Y ear Number: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- 513 = [Month Number [135]] × 47 × 19/235

### cullen:chunk:53 §40 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 千八十一 | 1081. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 食數 | §40 Eclipse Number: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- 1081 = 47 × Eclipse Factor [23]

### cullen:chunk:54 §41 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 月數 | §41 Month Number: | sequential_baseline_alignment, order_proximity, term_month_number |
| aligned | medium | 54 | one_to_one | 百(二)[三]十五 | 135. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

Commentary, not aligned:
- 135 = 5 × 27

### cullen:chunk:55 §42 p.159 Proc. 3.1

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 二十(二)[三] | 23 | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 食法 | §42 Eclipse Factor: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:57 §43 p.160-161 Proc. 3.2

Clauses: zh=0, en=1, commentary=28

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. |  |

Commentary, not aligned:
- Cast out Era Factor [1520] from the remainder.
- Number from the Heaven Era by how many you obtain, then outside the count is the Era you are entering.
- As for what does not amount to an Era Factor [1520], it is the number of years entered into the Era.
- Cast out Obscuration Factor [76] from it.
- Number from the jiazi.1 Obscuration by how many you obtain, then outside your count, [that is the Obscuration which is being entered.

### cullen:chunk:59 §44 p.161-162 Proc. 3.3

Clauses: zh=0, en=1, commentary=18

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §44 From the distance from High Origin cast out Origin Coincidence [41,040]. |  |

Commentary, not aligned:
- From the remainder, cast out Obscuration Coincidence [2052], and multiply what you obtain by 27.
- Cast out what fills 60, and from the number you obtain cast out 20.
- Start from the Heaven Era, and outside the exhausted count, that is the Era entered.
- With what does not fill 20, count starting from the jiazi.1 Obscuration, and outside the count, that is the Obscuration entered.
- What initially did not fill Obscuration Coincidence is the number of years by which the Obscuration Coincidence is entered.

### cullen:chunk:61 §45 p.163-164 Proc. 3.4

Clauses: zh=0, en=2, commentary=11

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §45 [T able of year-names] Table 3.2 T able of year-names Celestial Era year-name Terrestrial Era year-name Anthropic Era year-name Obscuration head sexagenary day Number of Obscurations in Era 17 37 57 1 1 33 53 13 40 2 49 9 29 19 3 5 25 45 58 4 21 41 1 37 5 37 57 17 16 6 53 13 33 55 7 9 29 49 34 8 25 45 5 13 9 41 1 21 52 10 57 17 37 31 11 13 33 53 10 12 29 49 9 49 13 45 5 25 28 14 1 21 41 7 15 17 37 57 46 16 33 53 13 25 17 49 9 29 4 18 5 25 45 43 19 21 41 1 22 20 How does this table work? We begin in the year designated gengchen.17, whose first day is jiazi.1. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | This is the head of an Origin [4560], an Era [1520], an Obscuration [76] and a Rule [19]. |  |

Commentary, not aligned:
- Since 1520 = 25 × 60 + 20, then one Era later the year-name will have increased by 20, to become gengzi.37;
- another Era later it will be gengshen.57.
- The next Era will start again in year gengchen.17.
- However, 1520 × 365.25 = 7980 = 133 × 60.
- So a whole number of sexagenary day cycles has elapsed from the start of one Era to the next, and the day name of the first day of the Rule that begins the first Obscuration of each new Era in the sequence is unchanged.

### cullen:chunk:62 §46 p.164-165 Proc. 3.5

Clauses: zh=7, en=6, commentary=16

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 79 | many_to_one | 不滿為閏餘 / 十二以上, 其歲有閏 | If it is 12 or more, this year has an intercalation. | sequential_baseline_alignment, order_proximity, number_exact_match, definition_make_or_is |
| aligned | medium | 53 | one_to_one | 置入蔀年減一 | Multiply by Rule Months [235]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 54 | one_to_one | 名為積月 | The remainder is the Intercalation Remainder. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 推天正術 | §46 Set out the years into the Obscuration and subtract one. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 以章月乘之 | Count one for each Rule Factor [19] filled. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_one | 滿章法得一 | Call this Accu- mulated Months. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This section and the next aim to predict the sexagenary day name of the first day of the first month of the current year according to the Celestial count.
- We start from the beginning of the current Obscuration, at which we are guaranteed that midnight, conjunction beginning the first Celestial month and winter solstice coin- cide.
- We already know (from Proc. 3.3) the sexagenary day name with which the Obscuration begins.
- Here we aim to find how many whole months have elapsed since the start of the Obscuration, and to predict whether the current civil year has an intercalary month or not.
- The first procedure deals with the fact that ‘years into the obscuration’ 入 蔀 年 means the ordinal number of year in the Obscuration.

### cullen:chunk:63 §47 p.165-166 Proc. 3.6

Clauses: zh=19, en=13, commentary=14

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 77 | many_to_one | 以蔀日乘之 / 滿蔀月得一 | Count one for each Obscuration Months [940] filled. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_rule_months, operation_fill_count |
| aligned | high | 77 | many_to_one | 不滿為小餘 / 積日以六十 除去之 | The remainder is the Lesser Remainder. | sequential_baseline_alignment, order_proximity, term_lesser_remainder, definition_make_or_is, result_remainder |
| aligned | high | 92 | many_to_one | 小餘四百四十一以上 / 其月大 | If the Lesser Remainder is 441 or greater, the month is long. | sequential_baseline_alignment, order_proximity, number_exact_match, term_lesser_remainder, result_remainder |
| aligned | high | 75 | many_to_one | 加大餘二十九 / 小餘四百九十 [九] | Count one each time the Lesser Remainder fills Obscuration Months [940]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_lesser_remainder, result_remainder |
| aligned | medium | 58 | one_to_one | 名為積日 | Call that Accumulated Days. | sequential_baseline_alignment, order_proximity, term_accumulated_days |
| aligned | medium | 58 | one_to_one | 求後月朔 | To find the conjunction day of the next month, add 29 to the Greater Remainder, and 499 to the Lesser Remainder. | sequential_baseline_alignment, order_proximity, operation_find |
| aligned | medium | 56 | one_to_one | 小餘滿蔀月得一 | Take that unit up to the Greater Remainder. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 57 | many_to_one | 上加大餘 / 命之如前 | Count off as before. | sequential_baseline_alignment, order_proximity, operation_count_or_name |
| aligned | low | 46 | one_to_one | 推天正朔日 | §47 Set out the Accumulated Months into the Obscuration. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 置入蔀積月 | Multiply by Obscura - tion Days [27,759]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 其餘為大餘 | Cast out 60 from the Accumulated Days. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 以所入蔀名命之 / 筭盡之外 | The remainder is the Greater Remainder. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 則前年天正十一月朔日 也 | Count off from the [sexagenary] name of the Obscuration, and outside the exhausted count will be the day of Celestial Standard Conjunction in the eleventh [civil] month preceding the [civil] year. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- We now use the previous result to find the actual day of the Celestial Standard Conjunction, which begins the first Celestial month.
- First we convert the Accu- mulated Months into days by using the fact that 27,759 days are precisely equal to 940 months.
- The whole days resulting from this procedure tell us how many whole days have elapsed from the midnight commencing the current Obscuration up to midnight beginning the current year.
- Since we are interested in sexagenary day names, we can usefully cast out 60 from this amount to form the Greater Remainder as specified in order to find the sexagenary day name of the first day of the current year.
- To take an example:

### cullen:chunk:64 §48 p.166-167 Proc. 3.7

Clauses: zh=5, en=4, commentary=7

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 一術 | §48 Multiply the years by Greater Circuits [343,335]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 45 | one_to_one | 以大周乘年 | Diminish it by Circuits of Heaven [1461] multiplied by Intercalation Remainder. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_one | 周天乘[閏餘]減之 | As for the remain- der, [find] the amount of filled Obscuration Months [940]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 餘滿蔀(日)[月] / 則天正朔日也 | Then that is the day of the Celestial Standard Conjunction. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Greater Circuits [343,335] is the number of days in a solar cycle (i.e. winter solstice to winter solstice) at a scale of Obscuration Months [940].
- Thus the first multiplica- tion gives the number of days elapsed from the start of the Obscuration up to the current winter solstice at a scale of 940.
- Now the Intercalation Remainder as already noted is the amount by which the start of the new year is in advance of its ideal date, which should coincide with winter solstice.
- It is in months, at a scale of Rule Factor [19].
- We need to convert this to days and change the scale to 940 to make this compatible with the previ- ous result.

### cullen:chunk:65 §49 p.167 Proc. 3.8

Clauses: zh=14, en=11, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | one_to_one | 置入蔀年減一 | set out the years entered into the Obscuration and subtract one. | sequential_baseline_alignment, order_proximity, operation_set_out, operation_subtract |
| aligned | high | 75 | one_to_one | 大餘滿六十除去之 | What does not fill [a Medial [Qi] factor [32]] is the Lesser Remainder. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_fill_count, result_remainder |
| aligned | high | 87 | one_to_one | 加大餘十五 | To predict the location of the next qi, add fifteen to the Greater Remainder, to the Lesser Remain - der 7, cast out and count off as before, and that is the day of Lesser Cold. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_greater_remainder, operation_add, result_remainder |
| aligned | medium | 54 | one_to_one | 推二十四氣 術曰 | §49 Method: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 67 | one_to_one | 以(月)[日]餘乘之 | Multiply by the Day Remainder [168]. | sequential_baseline_alignment, order_proximity, operation_multiply, result_remainder |
| aligned | medium | 64 | many_to_one | 滿中法得一 / 名曰大餘 | Count one for each Medial [Qi] factor [32] filled. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_fill_count |
| aligned | medium | 56 | one_to_one | 不滿為 小餘 | Call that the Greater Remainder. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 55 | one_to_one | 其餘以蔀名命之 | Cast out mul - tiples of sixty from the Greater Remainder. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 63 | one_to_one | 小餘七 | The Day Remainder [168] is the extra days in the annual cycle of qi when multiples of 60 have been cast out, at a scale of Medial [Qi] factor [32], so for each year after the start of the Obscuration we have to add this amount to the day number of the initial day of the Obscuration (which is a winter solstice) to find the sexa - genary day name of the winter solstice preceding the start of the current civil year. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, result_remainder |
| aligned | low | 44 | many_to_one | 筭盡之外 / 則前年冬至之日也. 求次氣 | With what is left, count off from the Obscuration name, then outside the exhausted count, that is the day of the winter solstice preceding this year. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 除命之如前 / 小寒日也 | The Lesser Remainder is the fraction of a day that the qi begins after midnight, at a scale of Medial [ Qi] factor [32]. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Note that once again we subtract one from the ordinal number of an event in a series to find the interval from the start of the first event in a series to the start of this event.

### cullen:chunk:66 §50 p.167-169 Proc. 3.9

Clauses: zh=10, en=17, commentary=23

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 55 | one_to_many | 以閏餘減章法 | Multiply the remainder by 12. / Count one for each completed Rule Intercalation Number [7]; | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 52 | one_to_many | 滿四以上亦得一筭之數 | [Thus] there may be adjustments back and forth, and these are determined by [the position of] the Medial qi. / In Proc. 3.5, it was determined whether the current year contains an intercalary month. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推閏月所在 | §50 Subtract the Intercalation Remainder from Rule Factor [19]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 餘以十二乘之 | for a completed four also get one count. / Start from the eleventh month preceding this year; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 滿章閏數得一 | the month outside the exhausted count is the intercalary month. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 從前 年十一月起 | If there is an intercalary month, this procedure finds where it will come in the sequence of months. / The key to making this decision is to look for a luna - tion within which no medial qi is located. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 筭盡之外 | That lunation normally corresponds to an intercalary month – with, as we shall see, a slight adjustment to allow for certain borderline conditions. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 閏月也 | We begin by finding Intercalation Remainder, the remainder from: / (Years into Obscuration) × 235/19. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 或進退 | The whole number result of this division is the total number of whole mean lunations elapsed from the start of the current Obscuration up to the conjunc - tion which began the current (Celestial) year, which will include some lunations corresponding to intercalations in previous years. / The remainder represents the amount in (1/19) of a mean lunation by which the winter solstice near the beginning of this year lags behind the conjunction of the first Celestial month, and this increases by (7/19) of a lunation from one winter solstice to the next. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 以中氣定之 | Now there are 12 medial qi in a year. / So the lag between a medial qi and its preceding conjunction must increase steadily from medial qi to medial qi by (7/19) / (12) = 7/228 of a mean lunation. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since we are counting up the increasing lag in units of (1/228) of a mean lunation, and the Intercalation Remainder is in (1/19) of a lunation, it is clear that the initial multiplication by 12 is needed to convert the Intercalation Remainder to the correct scale, since 12 × 19 = 228.
- When the total lag for a given medial qi builds up to greater than 228/228 of a mean lunation, then that medial qi falls after the next mean conjunction, and the lunation preceding that medial qi contains no medial qi at all, since the previous medial qi fell just before the previous mean conjunction.
- The month corresponding to that lunation is therefore counted as intercalary;
- it bears the same number as the preceding month, with the prefix run 閏 ‘intercalary’.
- We then find how many times we need to add 7 to the scaled up Intercalation Remainder until we reach a total exceeding 228.

### cullen:chunk:67 §51 p.169-170 Proc. 3.10

Clauses: zh=16, en=9, commentary=13

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 99 | many_to_one | 因其月朔大小餘之數 / 皆加大餘七 | Count one if the Lesser Remainder fills Obscuration Months [940], and add that to the Greater Remainder. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_greater_remainder, term_lesser_remainder, operation_add, result_remainder |
| aligned | high | 76 | many_to_one | 每以百刻乘之 / 滿蔀月得一刻 | [Obscuration Days [27,759]]/[Obscuration Months [940]] Taking a quarter of this, we obtain: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_rule_months, operation_obtain |
| aligned | medium | 55 | many_to_one | 小餘三百五十九四分三 / 小餘滿蔀月 得一 | Count off the Greater Remainder according to the method, and that is the [sexagenary day name] of the first crescent. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 52 | many_to_one | 又後月朔 / 其弦、望 小餘二百六十以下 | The length of the mean lunation is (29 + 499/940) days, defined by: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推弦、望日 | §51 T ake the numbers for the Greater and Lesser Remainders for this month, and in each case add to the Greater Remainder 7 and the Lesser Remainder 359¾. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 加大餘 / 大餘命如法 | A further addition gives full moon, the next gives the last crescent, and again after that the next conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 得上弦 | If the Lesser Remainders for crescents and full moon are 260 or less, in each case multiply by 100 ke, and count one ke for each filling of Obscuration Months [940]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 又加得望 / 次下弦 | Where this does not fill half the night clepsydra run for the nearest Nodal qi, then count one back to find the day [in whose night this event occurs]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 不滿其(數)[所]近節氣 夜漏之半者 / 以筭上為日 | (7 + (359 + ¾) / 940) days for the interval between the events considered here. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Hence the additions specified to the Greater and Lesser Remainders, with allow - ance for a whole extr a day mounting up as the factor of 940 is filled.
- The final section deals with the timing of the phase during the day.
- It seems, however, that specialists in li did not naturally think of their timings as starting from midnight, but preferred to think how much of the night was past, starting from dusk (when the night clepsydra was started) and running to dawn (when the day clepsydra was started).
- The night lengths given later for the principal seasons (see Table 3.11) are summarised in Table 3.3.
- The Lesser Remainders correspond to half the night length, 940 representing a whole day and night:

### cullen:chunk:68 §52 p.170-172 Proc. 3.11

Clauses: zh=21, en=11, commentary=14

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 91 | many_to_one | 小餘滿 沒法 / 從大餘 | To predict the next Extinction, add 69 to the Greater Remainder, and 4 to the Lesser Remainder, and as the Lesser Remainder fills the Extinction Factor [7], let that go with the Greater Remainder, and count off as before. | sequential_baseline_alignment, order_proximity, term_greater_remainder, term_lesser_remainder, operation_fill_count, result_remainder |
| aligned | medium | 65 | many_to_one | 置入蔀年減一 / 以沒數乘之 | Multiply by Extinction Number [21], and obtain one for each filling of the Day Factor [4]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_multiply |
| aligned | medium | 55 | many_to_one | 滿日法得一 / 名為積沒 | Called this Accumulated Extinctions. | sequential_baseline_alignment, order_proximity, definition_called |
| aligned | medium | 69 | many_to_one | 不盡為沒餘 / 以通法乘 積沒 | What is not exhausted is Extinction Remainder. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_not_exhausted_or_not_fill, result_remainder |
| aligned | medium | 65 | many_to_one | 滿沒法得一 / 名為大餘 | Multiply Accumulated Extinctions by Compat - ibility Factor [487], and count one for each filling of Extinction Factor [7]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_fill_count |
| aligned | medium | 67 | many_to_one | 不盡為小餘 / 大餘滿六十除去之 | Call this the Greater Remainder. | sequential_baseline_alignment, order_proximity, term_greater_remainder, result_remainder |
| aligned | medium | 55 | many_to_one | 其餘以蔀名 命之 / 筭盡之外 | What is not exhausted is the Lesser Remainder. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 55 | many_to_one | 命之如前 / 無分為滅 | When there are no fractions, that is Obliteration. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 推沒滅術 | §52 Set out years of entry into the Obscuration and subtract one. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 前年冬至前沒日也 / 求後沒 | As the Greater Remainder fills 60, cast it out, and count off the remainder from the Obscuration [sexagenary day] name. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 加大餘六十九 / 小餘四 | Outside the exhausted count, that is the Extinction Day before the winter solstice of the preceding [civil] year. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since the interval from one winter solstice to the next is 1461/4 days, and this is equal to 360 + 5¼ = 360 + 21/4 days winter solstices do not all occur on the same sexagenary day.
- It would however be very convenient if they did.
- To deal with this problem, we do something akin to intercalation, by considering a ‘basic’ solar cycle of 360 days, in which all qi are assumed to fall on the same cyclical day as the preceding year.
- We then allow for the fact that extra days do in fact accumulate at the rate of 21/4 per solar cycle, so that the cyclical days on which qi fall shift further through the sexage - nary sequence.
- The total number of whole extra days accumulated to date is the Accumulated Extinctions.

### cullen:chunk:69 §53 p.172 Proc. 3.12

Clauses: zh=5, en=4, commentary=12

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | one_to_one | 以(為)[十]五乘冬至小餘 | Obtain 1 as the remainder fills Extinction Factor [7], then that is the Extinction after the Celestial Standard [conjunction]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, definition_make_or_is, result_remainder |
| aligned | medium | 54 | one_to_one | 一術 | §53 Multiply the Lesser Remainder of the winter solstice by 15, and subtract from Compatibility Factor [487]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 51 | many_to_one | 餘滿沒法得一 / 則天正後沒也 | It takes on the values 0,8,16 and 24 over a four-year cycle. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 43 | one_to_one | 以減通法 | The Lesser Remainder of the winter solstice is the remainder when years into the Obscuration are multiplied by Day Remainder [168] and divided by Medial [ Qi] factor [32]. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since one year contributes 21/4 days towards an Extinction, each of the 24 qi contributes (21/4) / 24 = 7/32 days.
- So .
- .
- .
- each of the 15 days of a qi may be taken as contributing 7 / (15 × 32) days).

### cullen:chunk:71 §54 p.173-174 Proc. 3.13

Clauses: zh=11, en=7, commentary=19

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 98 | many_to_one | 分滿蔀月得一度 / 經斗除二百三十五分 | To seek the next conjunction, add to the du 29, and add to the Parts 499, obtaining 1 du as the Parts fill Obscuration Months [940], and casting out 235 Parts as you pass through Dipper. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, term_rule_months, operation_fill_count |
| aligned | medium | 63 | many_to_one | 不盡為餘分 / 積度加斗二十一度 | As for the remainder, obtain 1 for each filling of Obscu- ration Months [940]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, result_remainder |
| aligned | medium | 54 | many_to_one | 以宿次除之, 不滿宿 / 則日月合朔所在 (星)[宿] 度也 | What is not exhausted is Remainder Parts. | sequential_baseline_alignment, order_proximity, result_not_exhausted_or_not_fill |
| aligned | medium | 52 | many_to_one | 加度二十九 / 加分四百九 十九 | When it does not fill a Lodge, then that is the du of the Lodge 13 at which the sun and moon are located at their conjunction. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 名為積度 | §54 Set out the Accumulated Months of entry into the Obscuration, multiply by Obscuration days [27,759], and cast out and discard what fills Greater Circuits [343,335]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 加二百三十五分 | Call this Accumulated Du. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 求後合朔 | To the Accumulated Du, add the 21 du of Dipper, with [its] 235 parts, and then for each Lodge cast out in succession. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Accumulated Months have already been calculated for the conjunction of the first Celestial (and hence subsequent) months in Proc. 3.6.
- Obscuration Days [27,759] is the number of days in a month at a scale of Obscuration Months [940], so the multiplication specified produces the number of days elapsed at the instant of conjunction (and hence number of du moved by the sun), including fractional parts, at a scale of Obscuration Months [940].
- Greater Circuits [343,335] = 365¼ × 940, so this represents the du in a complete circuit at the same scale.
- Casting this out gives the number of du moved by the sun past its starting point at winter solstice – which is also the du moved by the moon at the time of the conjunction, since its position coincides with that of the sun.
- If we want to locate the present position of the sun and moon in the lodge system, then we have to take account of the fact that in the system used by the Han Quarter Remainder, winter solstice position of the sun is at 21¼ du of the lodge Dipper.

### cullen:chunk:72 §55 p.174 Proc. 3.14

Clauses: zh=6, en=5, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 一術 | §55 Multiply Circuits of Heaven [1461] by Intercalation Remainder, and by that subtract from Greater Circuits [343,335], obtaining 1 as the remainder fills Obscuration Months [940]. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 54 | one_to_one | 以減大周餘 | Intercalation Remainder is the fraction of a month at a scale of 19 by which the conjunction of Celestial New Year falls in advance of the winter solstice. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 51 | many_to_one | 合以斗二十一度四分一 / 則天正合 朔日月所在度 | 19 × Circuits of Heaven [1461]/Obscuration Months [940]. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 45 | one_to_one | 以閏餘乘周天 | Join with it the 21 du ¼ of Dipper, and this is the du where the sun and moon are located at the Celestial Standard conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_one | 滿蔀月得一 | Now the days in a lunation (and hence the du moved by the sun between conjunctions) are given by: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since as before the number of du in a whole circuit is represented by Greater Circuits [343,335]/Obscuration Months [940], the procedure described here moves us backwards from the sun’s winter solstice position to its location at the preceding conjunction, as required.

### cullen:chunk:73 §56 p.174-175 Proc. 3.15

Clauses: zh=17, en=11, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 其餘滿蔀法得一 / 為積 度 | To seek the next day, add 1 du. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 57 | many_to_one | 置入蔀積日之數 / 以蔀法乘之 | Cast out and discard Obscuration Days [27,759], and obtain 1 for each time the remainder fills Obscuration Factor [76], which is Accumulated Du, while what is not exhausted is Remainder Parts. | sequential_baseline_alignment, order_proximity, term_obscuration_factor |
| aligned | medium | 58 | one_to_one | 滿蔀日除去之 | To the Accumulated Du add the 21 du of Dipper and add 19 parts, then cast out and discard the Lodges in sequence, and that is the degree of the Lodges where the sun is located at midnight. | sequential_baseline_alignment, order_proximity, operation_cast_out_or_divide |
| aligned | medium | 69 | many_to_one | 積度加斗二十一度 / 加十九分 | When passing through Dipper cast out the 19 parts. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 52 | many_to_one | 求次月 / 大加三十度 | Obscuration Days [27,759]/Obscuration Factor [76] = 365¼, The procedure given yields the du from winter solstice moved by the sun in the current cycle, and the rest follows. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 52 | many_to_one | 小加二十九度 / 經斗除十 [九]分 | ‘19 parts’ here are 19/76 = ¼. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推日所在度 | §56 Set out the number of Accumulated Days entered into the Obscuration, and multiply it by Obscuration Factor [76]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 不盡為餘分 | To seek the next month, add 30 du for a long [month] and 29 du for a short [month]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 以宿次除去之 | At the beginning of an Obscuration cycle, the sun is at winter solstice. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 則夜半日所 在宿度也 / 求次日 | Each day thereafter it moves 1 du. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 加一度 | Since the days in a solar cycle, and hence the du moved in that cycle, are given by: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:74 §57 p.175 Proc. 3.16

Clauses: zh=4, en=5, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 一術 | §57 By the Lesser Remainder for the conjunction subtract from the du and parts for the conjunction, then that is where the sun is located at midnight. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 68 | one_to_many | 其分(三)[二]百(二)[三]十五約之, 十九乘之 | It will be recalled that the factor giving the scale of Parts in the calculation of the sun’s midnight position was 76. / To convert to this from a scale of 940 requires a multiplication of the parts by 235/19, as specified. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 45 | one_to_one | 以朔小餘減合[朔]度分 | As for the parts simplify them by 235, multiplying by 19. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_one | 即日夜半所在 | The Lesser Remainder is the fraction of a day, at the scale of Obscuration Months [940] by which the conjunction falls after midnight, and hence it gives the angular movement of the sun between these instants. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:75 §58 p.175-177 Proc. 3.17

Clauses: zh=19, en=12, commentary=10

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 滿蔀日除去之 | To Accumulated Du add the 21 [ du] and 19 parts of Dipper, and cast out according to the method above, then that is the degree of the Lodges where the moon is located at midnight on the day sought. | sequential_baseline_alignment, order_proximity, operation_cast_out_or_divide |
| aligned | medium | 53 | many_to_one | 其餘滿蔀法得一 / 為積 度 | To seek the next day, add 13 du and 28 parts. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 55 | one_to_one | 不盡為餘分 | To seek the next month, for a long [month] add 35 du and 61 parts, but if the month is small add 22 du 33 parts. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 64 | many_to_one | 積度加斗二十一十[九]分 / 除如上法 | If the parts fill the factor obtain 1 du, and in passing through Dipper cast out 19 parts. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_cast_out_or_divide |
| aligned | medium | 52 | many_to_one | 求次月 / 大加三十五度六十一分 | Lunar Circuits [1016] is the number of circuits of Heaven made by the moon in an Obscuration, during which the sun only makes 76 circuits. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | one_to_one | 月小二十二度三十三分 | So 1016/76 gives the factor by which the moon’s speed is greater than the sun’s. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推月所在度 | §58 Set out the number of Accumulated Days entered into the Obscuration, and multiply them by Lunar Circuits [1016]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 置入蔀積日之數 / 以月周乘之 | Cast out and discard what fills Obscuration Days [27,759], and obtain 1 for each time the remainder fills Obscuration Factor [76], which is Accumulated Du, while what is not exhausted is Remainder Parts. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 則所求之日夜半月 所在宿度也 / 求次日 | When in the last ten days of winter the Moon is in Spread and Heart, take note of it; | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 加十三度二十八分 | this refers to the time between the [end] boundary of the day clepsydra up to the end of the [night] clepsydra. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 分滿法得一度 / 經斗除十九分 | Since Accumulated Days is the number of du moved by the sun since the start of the Obscuration, multiplying by this factor gives the du moved by the moon. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 其冬下旬月在張、 心署之 / 謂(盡)[晝]漏分後盡漏盡也 | Subtraction of Obscura- tion Days [27,759] before dividing by Obscuration Factor [76] removes the whole circuits from the result. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Clearly the lunar motion for one day is 1016/76 du = 13 du and 28 parts.
- From this we may find that the motion for 30 days is:
- 30 × 1016/76 du = 401 du and 4 parts.
- Casting out a whole circuit at 365 du and 19 parts, we reach the figure of 35 du and 61 parts given in the text for 30 days, from which the figure for a short 29 day month follows immediately.
- An error is of course introduced by the assump - tion that the month is a whole number of days long.

### cullen:chunk:76 §59 p.177 Proc. 3.18

Clauses: zh=5, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 一術 | §59 Cast out Obscuration Factor [76] from the Lesser Remainder for the con - junction, and by what you obtain subtract from the midnight du of the sun. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 55 | one_to_one | 以蔀法除朔小餘 | Subtract the remainder from the parts, then that is the du where the moon is located at midnight. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | low | 44 | one_to_many | 所得以減日〔夜〕半度也 | At midnight, the Lesser Remainder represents the time before the moon catches up with the sun in days at a scale of Obscuration Months [940]. / In that time the sun has moved an equal number of du. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 餘以減分 | We need the motion of the moon relative to the sun while the sun makes this much absolute movement. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 即月夜半所在 度也 | But the number of revolutions of the moon relative to the sun is precisely Obscu- ration Months [940] while the sun makes Obscuration Factor [76] absolute revo - lutions of Heaven. / Thus dividing the sun’s du moved at a scale of 940 by 76 produces the motion of the moon relative to the sun in du as required. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:77 §60 p.177-178 Proc. 3.19

Clauses: zh=8, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 置其月節氣夜漏之數 | set out the number for the night clepsydra for the Nodal qi of that month, and multiply it by Obscuration Factor [76]. | sequential_baseline_alignment, order_proximity, operation_set_out |
| aligned | medium | 69 | one_to_one | 得一分 | Clepsydra runs are given in 刻 ke, each of which is 1/100 day. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 54 | many_to_one | 以增夜半日所在度分 / 為明所在度分也 | Since the sun moves 1 du in a day, these are parts of du as stated. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 推日明所入度分 術曰 | §60 Method: | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 以蔀法乘之 | Cast out 200 from it, obtaining 1 part [for each complete 200], then this is the parts moved [by the sun] from midnight until dawn. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 二百除之 | If you increase by this the du and parts where the sun is located at midnight, that is the du and parts where it is located at dawn. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_one | 即夜半到明所 行分也 | So the process described takes half of the night ke, and converts it to parts of a day at a scale of 76. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:78 §61 p.178 Proc. 3.20

Clauses: zh=5, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 67 | many_to_one | 求昏日所入度 / 以夜半到明日所行分(分)減蔀法 | §61 By the parts moved by the sun from midnight to dawn, subtract from Obscuration Factor [76], and the remainder is the parts moved from midnight to dusk. | sequential_baseline_alignment, order_proximity, term_obscuration_factor, operation_subtract |
| aligned | medium | 62 | many_to_one | 其餘即夜半到昏所行分也 / 以加夜半所在 度分 / 為昏日所在度也 | If you add this to the du and parts where the sun is located at midnight, this is the du where the sun is located at dusk. | sequential_baseline_alignment, order_proximity, operation_add, definition_make_or_is |

Commentary, not aligned:
- This works because if as usual we assume that solar motion is constant, the move- ment from midnight to dawn is equal to the movement from dusk to midnight.

### cullen:chunk:79 §62 p.178 Proc. 3.21

Clauses: zh=8, en=3, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 92 | many_to_one | 以月周乘之 / 以二百除之 / 為積分 | set out the number for the night clepsydra for the Nodal qi, and multiply by Lunar Circuits [1016], then cast out 200, making [the number obtained] Accumulated Parts. | sequential_baseline_alignment, order_proximity, number_exact_match, operation_multiply, operation_cast_out_or_divide |
| aligned | high | 100 | many_to_one | 積分滿 蔀法得一 / 以增夜半度 / 即(明)月[明]所在度也 | Obtain 1 for each time Accumulated Parts fills Obscuration Factor [76], and by that increase the midnight du, then that is the du where the moon is located at dawn. | sequential_baseline_alignment, order_proximity, number_exact_match, term_obscuration_factor, operation_fill_count, operation_obtain |
| aligned | low | 44 | many_to_one | 推月明所入度分 術曰 / 置其節氣夜(半)[漏]之數 | §62 Method: | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since Lunar Circuits [1016] gives the circuits of Heaven made by the moon while the sun is making Obscuration Factor [76] circuits, using this instead of the 76 in the earlier calculation uses the moon’s speed instead of the sun’s, as appropri- ate.
- The later division by 76 is performed because unlike the case of the sun the moon will have moved more than one du in the given time, so it is not sensible to leave the motion in parts.

### cullen:chunk:80 §63 p.178-179 Proc. 3.22

Clauses: zh=5, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 求昏月所入度 | §63 By the dawn Accumulated Parts subtract from Lunar Circuits [1016], and obtain 1 du for each time the remainder fills Obscuration Factor [76]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 以明積分減月周 / 其餘滿蔀法得一度 | Add this to midnight, and it is the du where the moon is located at dusk. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 加夜半 / 則昏月所在度也 | The point here is that in a whole day the moon moves 1016/72 du, and as in the case of the sun the motion from midnight to dawn is assumed equal to the motion from dusk to midnight. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:82 §64 p.179 Proc. 3.23

Clauses: zh=0, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §64 Set out the number of the du and parts at conjunction, and add 7 du and (359 + ¾) parts. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Cast out the Lodges in succession, and that is the du and parts of the Lodge entered by the sun at the first crescent. |  |

Commentary, not aligned:
- Since a month contains 29 499/940 days, one quarter of this gives the movement of the sun in du from one quarter to the next, and that is 7 du + (359 + ¾) / 940, as stated here.
- The next three sections are similarly based.

### cullen:chunk:83 §65 p.179 Proc. 3.24

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | many_to_one | 求望、下弦 / 加除如前法 / 小分[滿]四從大分 / [大分]滿蔀月從度 | §65 Add and cast out as in the previous method, letting the lesser parts go with the greater parts as they fill 4, and letting the greater parts go with the du as they fill Obscuration Months [940]. | sequential_baseline_alignment, number_exact_match, term_rule_months, operation_add, operation_cast_out_or_divide, operation_fill_count |

### cullen:chunk:85 §66 p.179 Proc. 3.25

Clauses: zh=0, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §66 Method: |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | set out the number of du and parts for the moon at conjunction, and add 98 du and 653 and a half parts. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Cast out the lodges in succession, and that if the du and parts of the Lodge entered by the moon at the first crescent. |  |

### cullen:chunk:86 §67 p.179-180 Proc. 3.26

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 77 | many_to_one | 求望、下弦 / 加除如前分 / 滿蔀月從度 | §67 Add and cast out as before, and let what fills Obscuration Months [940] go with the du. | sequential_baseline_alignment, term_rule_months, operation_add, operation_cast_out_or_divide, operation_fill_count |

### cullen:chunk:87 §68 p.180 Proc. 3.27

Clauses: zh=7, en=13, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | one_to_many | 減一 | Count one for each full Year Number [513]. / This is called Accumulated Eclipses. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 64 | one_to_many | 不滿為食餘 | In the second year, the result is found from: / 1 × 1081/513 = 2 remainder 55 Thus two eclipses have already occurred in the first year (in addition, i.e. to the one at the full moon following the start of the Obscuration Coincidence) and 55 is the Eclipse Remainder representing in effect the fraction accumulated by the start of this year of an eclipse that will ‘mature’ as the current year progresses. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_remainder |
| aligned | low | 46 | one_to_one | 推月食術曰 | §68 Set out the year of entry into Obscuration Coincidence [2052]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 置入蔀會年數 | Subtract one. / Multiply by the Eclipse Number [1081]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 以食數乘之 | The remainder is the Eclipse Remainder. / For convenience of exposition, I have divided this procedure into three sections, of which this is the first. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 滿歲數得一 | An Obscuration Coincidence begins with an eclipse at full moon of its first Celestial month, as was the case in the month beginning at System Origin ‘Year of entry’ is the number of the target year in the Obscuration Coincidence; / subtracting one gives us the interval in years from the start of the Obscuration Coincidence to the start of the current Celestial year. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 名曰積食 | Since there is a complete cycle of 1081 lunar eclipses in 513 years, beginning with an eclipse at full moon of the first month, with another at full moon of the first month of the next cycle, the calculation prescribed year tells us how many lunar eclipses (within that Obscuration Coincidence) have taken place by the beginning of the target year. / Thus in the first year of the Obscuration Coin- cidence, the result is zero. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:88 §69 p.180-181 Proc. 3.27

Clauses: zh=4, en=9, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 68 | one_to_many | 以月數乘積[食] | §69 Multiply accumulated eclipses by the Month Number [135]. / Count one for each Eclipse Factor: | sequential_baseline_alignment, order_proximity, term_month_number, operation_multiply |
| aligned | medium | 53 | one_to_many | 滿食法得一 | [23]. / Call this Accumulated Months. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | one_to_many | 名為積月 | The remainder is the Lunation Remainder Fraction. / There is a complete cycle of 23 lunar eclipses in 135 months, with an eclipse at full moon of the first month of the cycle, and at full moon of the first month of the next cycle. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 52 | one_to_many | 不滿為月餘分 | Thus this calculation tells us how many months have elapsed from the start of the current Obscuration Coincidence to the last eclipse to take place before the start of the current Celestial year. / Following the example of the second year, before which 2 eclipses have occurred, we find the result from: / 2 × 135/23 = 11 remainder 17. | sequential_baseline_alignment, order_proximity, result_remainder |

### cullen:chunk:90 §70 p.181 Proc. 3.27

Clauses: zh=6, en=1, commentary=7

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | many_to_one | 月數 / 當先除入章閏 / 乃以十二除去之 / 不滿者命以十一月 / 筭盡之外 / 則 前年十一月前食月也 | §70 Remove multiples of the Rule Months [235] from Accumulated Months. | sequential_baseline_alignment, numbers_present_without_exact_match, operation_cast_out_or_divide |

Commentary, not aligned:
- The remainder is the number of months into the Rule.
- First one takes out the intercalations that far into the Rule.
- Then one removes multiples of 12.
- As for the remainder, count from the eleventh month, and outside the exhausted count that is the month of the eclipse before the eleventh month of the preceding [civil] year.
- This part of the procedure removes from Accumulated Months the months before this eclipse that are whole Rules or whole years (including intercalary months).

### cullen:chunk:91 §71 p.181-182 Proc. 3.28

Clauses: zh=9, en=8, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 96 | one_to_one | 餘分滿二百二十四以上 至二百三十一 | The Remainder Parts are the remainder from division (Accumulated Months) × 7/235 We are told that if these Remainder Parts are between 224 and 231, then the month in which the eclipse falls is intercalary. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, term_remainder_parts, result_remainder |
| aligned | low | 46 | one_to_one | 求入章閏者 | §71 Set out the months of entry into the Rule, and multiply by Rule Intercala - tions [7], counting one for each filling of Rule Months [235], then this is the number of intercalations from entry into the Rule. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 置入章月 | If the Remainder Parts fill 224 up to 231, that makes the eclipse situated in the intercalary month. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 以章閏乘之 | The intercalation may move back and forth: | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 滿章月得一 | fix it by the day of conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 則入章閏數也 | We are evidently calculating the total number of intercalations up to the present eclipse, including those in the current year. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_one | 為食在閏月 | Since 231 = 235 − 4, and 224 = 231 − 7, these figures clearly originate in the practice of moving an intercalation to an earlier month if the medial qi falls close enough to the next conjunction: | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 閏或進退 / 以朔日定之 | see Proc. 3.9. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:92 §72 p.182 Proc. 3.29

Clauses: zh=5, en=2, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 85 | many_to_one | 求後食 / 加五(百)[月]二十分 | §72 Add 5 months and 20 parts, with one for the count of months when the factor is filled. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, operation_add |
| aligned | low | 40 | many_to_one | 滿法得一月數 / 命之如法 / 其分盡食筭上 | Count it off according to the factor, and when the parts are exhausted there is an eclipse above the count. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Since there are Eclipse Factor:
- [23] eclipses in Month Number [135] months, the mean interval between eclipses will be 135/23 months = 5 20/23 months.
- Hence the process specified here to locate the next eclipse.

### cullen:chunk:94 §73 p.182 Proc. 3.30

Clauses: zh=0, en=5, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §73 Set out the number of Accumulated Months of the eclipse, multiply it by 29, to make Accumulated Days. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Further, multiply Accumulated Months by 499, and count one for each filling of Obscuration Months [940], adding this to the Accumulated Days. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Cast out multiples of 60, and count off the remainder from the name of the Coincidence Obscuration. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Outside the count that is exhausted, then that is the conjunction day [of the month] with a lunar eclipse before the Celestial First Month of the preceding year. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | All this follows from the fact that there are 29 499/940 days in a lunation . |  |

### cullen:chunk:95 §74 p.182-183 Proc. 3.31

Clauses: zh=6, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | many_to_one | 求食日 / 加大餘十四 | §74 Add to the Greater Remainder 14, and to the Lesser Remainder 719 and ½. | sequential_baseline_alignment, order_proximity, number_exact_match, term_greater_remainder, operation_add, result_remainder |
| aligned | high | 100 | many_to_one | 小餘七百一十九半 / 小餘滿蔀月為大餘 | As the Lesser Remainder fills Obscuration Months [940] let that count as Greater Remainder, and counting off the Greater Remainder as before, then that is the day of the eclipse. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_greater_remainder, term_lesser_remainder, term_rule_months, operation_fill_count, definition_make_or_is, result_remainder |
| aligned | low | 43 | many_to_one | 大餘命如前 / 則食 日也 | The additions specified simply add half the length of a lunation, the interval between conjunction and opposition. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:98 §75 p.183 Proc. 3.32

Clauses: zh=0, en=10, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §75 In each case add 27 to the Greater Remainder, and 615 to the Lesser Remain - der. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Where the parts for the month do not fill 20, further add 29 to the Greater Remainder and 499 to the Lesser Remainder. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | The Lesser Remainder for the eclipse should be compared with the clepsydra graduations. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Where the night run is not exhausted, count one back to make the day. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | The aim here is to predict the sexagenary day and time of day of the next eclipse. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | To get to these figures, we multiply the days in a lunation by the lunations from one eclipse to another, on the basis that eclipses can normally be expected at intervals of five lunations: |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | 5 × (Obscuration Days [27,759]/Obscuration Months [940]) = 147315/940 Since 147 = 2 × 60 + 27, we can see that the sexagenary day number must increase by 27, and the extra parts of a day (at a scale of 940) will be 615, as specified. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Recalling that the mean interval between eclipses is 5 20/23 lunations it is clear that the reference to ‘where the parts for the month do not fill 20’ identifies the situation where the interval since the last eclipse is not yet long enough for another eclipse to be expected. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | In that case, we simply add a lunation’s worth of days and parts as specified to get to the conjunction of the next month. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | The final sentence refers to the practice already seen in Proc. 3.10, where an event occurring during the hours of darkness after midnight is counted as occur - ring on the previous day. |  |

### cullen:chunk:99 §76 p.184-185 Proc. 3.33

Clauses: zh=6, en=32, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 79 | one_to_many | 以百一十二乘之 | Thus to find the number of months to be counted until the next eclipse is complete will be: / (135 − Eclipse Remainder) / 23 Now what is proposed here is to multiply Accumulated Months by 112 = (135 − 23) This represents the amount by which one month falls short of a whole eclipse. / 14 See Li Rui 李銳 (1768–1817) (1993) 763. / Then we are to cast out multiples of 135; / each of these multiples is a whole eclipse’s worth: | sequential_baseline_alignment, order_proximity, number_exact_match, operation_multiply |
| aligned | medium | 61 | one_to_many | 餘以為積月 | (3) No w we multiply by Eclipse Factor [23] and cast out whole multiples of Month Number [135]. / The result will be (at the scale of Month Number) the fraction of an eclipse that has been completed between the last eclipse and the start of the first Celestial month. / It will be a number greater than zero and less than 135. / Let us call this Eclipse Remainder. / (4) If w e subtract this number from 135, the result will tell us how far we have to go until the first eclipse after Celestial First Month is complete. / Now each month, 23/135 of an eclipse is completed. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_remainder |
| aligned | medium | 65 | one_to_many | 餘滿食法得一, 則天正後食 | The 135 repre - sents a further eclipse missed in that month, and thus the number of misses normally goes up by 1 a month, as it should. / But from time to time the accu - mulation of 23s passes the total of 135 – and when that happens a month passes without the total of missed eclipses increasing – which is what happens when an eclipse actually takes place. / Further, for a month in which an eclipse actually falls, (23 × Accumulated months) = a multiple of 135. / So clearly (135 − 23) × Accumulated months = a multiple of 135. / For the next month, when Accumulated Months increases by 1, the left-hand side of the equation will increase by 135 and decrease by 23. / The increase of 135 will not affect the result when 135 is cast out. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 49 | one_to_many | 一術 | §76 Cast out Year Number [513] from [the years since] High Origin. / [From the] remainder make Accumulated Months, and multiply by 112. / Cast out what fills Month Number [135], and for the remainder obtain one for each filling of Eclipse Factor [23], then this is the eclipse after Celestial First Month. / As Li Rui notes, the start of this text is elliptical. / It is however possible to make sense of the details that are given here if we consider how the first eclipse of a given Celestial year can in fact be predicted. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 42 | one_to_many | 以歲數去上元 | 14 The steps would be as follows: / (1) Cas t out Year Number [513] from years since High Origin. / This removes complete cycles of eclipses, so that we are counting years from the near - est year in which an eclipse occurs at opposition of the first Celestial month. / (2) W e then take the resulting years, and convert them to months, by multiply - ing by 235 and dividing by 19. / We take the whole number result of this, which is Accumulated Months from the start of the nearest year in which an eclipse occurs at opposition of the first Celestial month up to the start of the present year. | sequential_baseline_alignment, order_proximity |
| aligned | low | 41 | one_to_many | 滿月數去之 | thus, for example, if we consider an instant at the start of the 10th month of the sequence, when Accumulated Months is 9, we get: / 9 × 112 = 1008 1008 mod 135 = 63 7 multiples of 135 have been cast out, meaning we are 7 eclipses short of the number that would have occurred if there had been eclipses at the rate of one a month; / there have been nine months, so there should have been two eclipses so far: / this is indeed the case, since there were eclipses in the first and seventh month. / Each month we move forward increases the total by (135 − 23). | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Thus to find the next eclipse, we can count up 23 each month until we reach 135.
- Now returning to our example, where we had 9 Accumulated Months, from 63 to the next full eclipse missed is 135 − 63 = 72 72 = 3 × 23 + 3 So the number of fillings of 23 is 3.
- The next eclipse after the start of the 10th month of the sequence is indeed three months onwards, in the 13th month of the sequence.

### cullen:chunk:100 §77 p.185-186 Proc. 3.34

Clauses: zh=8, en=4, commentary=6

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | many_to_one | 推諸加時 / 以十二乘小餘 | §77 Multiply the Lesser Remainder by 12. | sequential_baseline_alignment, order_proximity, number_exact_match, term_lesser_remainder, operation_multiply, result_remainder |
| aligned | medium | 69 | many_to_one | 先減如法之半 / 得一時 | First subtract what matches half the factor, to get one double-hour. | sequential_baseline_alignment, order_proximity, operation_subtract, operation_obtain |
| aligned | medium | 67 | many_to_one | 其餘乃以法除之 / 所得筭之數從夜半 子起 | As for the remainder, cast out in accordance with the factor, and with the number of counts obtained begin from zi for midnight. | sequential_baseline_alignment, order_proximity, operation_cast_out_or_divide, result_remainder |
| aligned | low | 44 | many_to_one | 筭盡之外 / 則所加時也 | Then outside the exhausted count is the double-hour of occurrence. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This procedure can be applied to find the time of day of all lunar phenomena, not just eclipses.
- The ‘factor’ here is Obscuration Months [940], which is the scale factor for the Lesser Remainder of months.
- Multiplication by 12 and division by 940 converts the Lesser Remainder into (1/12) days, i.e. converts the fraction of a day into double hours.
- The day is divided into 12 ‘double-hours’, named after the 12 cyclical signs.
- The first double-hour is labelled zi 子, and centres on the moment of midnight.

### cullen:chunk:102 §78 p.186-187 Proc. 3.35

Clauses: zh=8, en=13, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 64 | one_to_many | 餘為夜上水數 | the remainder is the amount of the daytime water filling. / If it exceeds the day clepsydra, cast that out, and the remainder is the amount of the night water filling. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_remainder |
| aligned | medium | 56 | one_to_many | 其刻 不滿夜漏半者 | If the ke do not fill half the night clepsydra, then subtract [the ke] from it, and the remainder is the unexpired part of the preceding night. / The crescents and full moons [are counted on] that day. | sequential_baseline_alignment, order_proximity, operation_fill_count |
| aligned | medium | 54 | one_to_many | 餘為昨夜未(晝)[盡] | First we convert this into ke and tenths of ke, at the rate of 100 ke to the day. / The time from midnight to dawn is ‘half the night clepsydra for the Nodal Qi’ in question, and if the interval since midnight is greater than this, we have moved into the hours of daylight, and subtraction will tell us how far we are into that daytime clepsydra run. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 減所入節氣夜漏之半 | §78 Multiply the Lesser Remainder by 100. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 其餘為晝上水之數 | Obtain one ke for each time it fills its factor. / As for what does not fill, multiply it by ten, and obtain one fen for each time it fills the factor. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 過晝漏去之 | From the accumulated ke, first subtract half the night clepsydra for the Nodal qi entered; | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 乃減之 | The Lesser Remainder tells us the fraction of a day (at a scale of Obscuration Months [940] by which a given event falls after midnight. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 其弦望其日 | If the event is late enough, it will move into the clepsydra run for the next night, and we subtract the day clepsydra run to find out how far that is. / If however the time of the event past midnight is less that half the night length, then we may calculate how long before dawn the event occurs by subtraction, and as already seen in Proc. 3.10, we count the event as having occurred on the preceding day. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:103 §79 p.187 Proc. 3.36

Clauses: zh=3, en=8, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | one_to_many | 五星數之生也 | §79 As for the production of the numbers for the five planets, each is reckoned with reference to the Sun, and a rate is made by making it congruent with the du of the circumference of heaven. / Cycle Rate: | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 51 | one_to_many | 與周天度相約而為率 | 4327 Solar Rate: / 4725 For every 4725 circuits of the heavens by the sun, Jupiter makes 4327 conjunctions. / That means that during these 4725 solar circuits, it moves through (4725 − 4327) = 398 circuits. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 43 | one_to_many | 各記於日 | number of conjunctions between planet and sun Solar Rate: / number of complete circuits of the sun round the heaven while Cycle Rate conjunctions occur – i.e. the number of years required for that. / So for instance, for the Wood Star (Jupiter) has Cycle Rate: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:104 §80 p.187 Proc. 3.36

Clauses: zh=4, en=4, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 68 | one_to_one | 以章法乘周率為(用)[月]法 | §80 By multiplying the Cycle Rate by the Rule Factor [19] one makes the Lunation Factor, then Rule Months [235] multiplies the Solar Rate, and [from the number of] accords with the Lunation Factor, one makes the Accumulated Months and the Lunation Remainder. | sequential_baseline_alignment, order_proximity, term_cycle_rate, definition_make_or_is |
| aligned | medium | 58 | one_to_one | 章月乘日率 | Cycle Rate × Rule Factor [19] gives the number of Conjunctions in Solar Rate years, at a scale of Rule Factor: | sequential_baseline_alignment, order_proximity, term_solar_rate |
| aligned | medium | 58 | one_to_one | 如月法 | this is Lunation Factor. | sequential_baseline_alignment, order_proximity, term_lunation_factor |
| aligned | low | 46 | one_to_one | 為積月月餘 | Rule Months [235] × Solar Rate gives the number of months in the years of Solar Rate, at a scale of Rule Factor [19]. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Hence dividing the second result by the first gives the months in one conjunction (Accumulated Months) and the remainder is at a scale of Lunation Factor.
- (235 × Solar Rate) / (Cycle Rate × 19)

### cullen:chunk:105 §81 p.188 Proc. 3.36

Clauses: zh=2, en=1, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | many_to_one | 以月之(月)[日]乘積[月] / 為朔大小餘 | §81 Multiply Accumulated Months by the days in a month, to make the Greater and Lesser [Lunar] Conjunction Remainders. | sequential_baseline_alignment, operation_multiply, definition_make_or_is |

Commentary, not aligned:
- The days in a month are given by:
- Obscuration Days [27,759]/Obscuration Months [940] Multiplying Accumulated Months by this gives the number of days in Accumu- lated Months.
- The Greater Remainder is the number of days when whole multiples of 60 have been cast out.
- The Lesser Remainder is the fractional day part at a scale of 940.

### cullen:chunk:106 §82 p.188 Proc. 3.36

Clauses: zh=1, en=1, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 78 | one_to_one | 乘為入月日餘 | §82 Multiply [The Lunation Remainder] by [the days in a month] to make the days and remainder into the month. | sequential_baseline_alignment, order_proximity, operation_multiply, definition_make_or_is, result_remainder |

Commentary, not aligned:
- Here we take the fractional parts of a month in the time one conjunction takes, and convert it into days and fractional parts.
- The description of the process is very abbreviated.

### cullen:chunk:107 §83 p.188 Proc. 3.36

Clauses: zh=1, en=1, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | one_to_one | 以日法乘周率為日度法 | §83 By the Day Factor [4] Multiply the Cycle Rate to make the Day and Du Factor. | sequential_baseline_alignment, order_proximity, term_day_factor, term_day_du_factor, term_cycle_rate, operation_multiply, definition_make_or_is |

Commentary, not aligned:
- The result is the number of conjunctions in Solar Rate years, at a scale of Day Factor [4].
- It is the scale factor for days elapsed from winter solstice to conjunc - tion, and hence also for du moved by the sun in that period.

### cullen:chunk:108 §84 p.188-189 Proc. 3.36

Clauses: zh=4, en=5, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 以[周]率去日率 | §84 By the Cycle Rate cast out from the Solar Rate, and multiply the remainder by Circuits of Heaven [1461]. | sequential_baseline_alignment, order_proximity, term_solar_rate |
| aligned | medium | 55 | one_to_one | 餘以乘周天 | [Reckon] accords with the Day and Du Fac- tor, to make the du and remainder of the Accumulated Du. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 53 | one_to_many | 為[積]度(之)[度]餘也 | The multiplication by Circuits of Heaven [1461] gives the number of du in those circuits, at a scale of Day Fac- tor [4]. / The division by Day and Du Factor results in the number of du moved between conjunctions, with the remainder at a scale of Day and Du Factor. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | low | 43 | one_to_one | 如日度法 | The difference between Cycle Rate and Solar Rate is the number of circuits of the heavens made by the planet in Solar Rate years. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:109 §85 p.189 Proc. 3.36

Clauses: zh=5, en=5, commentary=6

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 日率相約取之 | §85 T aking it by harmonising the Solar Rates, obtain for the termination of the five planets 29,991,621,582,300. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 得二千九百九十〔九〕萬一千六百二十一億五十八萬二千三 百 | Take as many of these as the Obscuration [factor] to make this compatible with the Origin [factor]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 而五星終 | The Solar Rates are: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 如蔀之數 | Wood (Jupiter) 4725 = 5 × 945 = 5 × 5 × 3 × 3 × 3 × 7 Fire (Mars) 1876 = 2 × 2 × 7 × 67 Earth (Saturn) 9415 = 5 × 7 × 269 Metal (Venus) 4661 = 59 × 79 Water (Mercury) 1889 = prime The number given above is the lowest common multiple of these, and its factors are: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 與元通 | 4 × 5 × 5 × 3 × 3 × 3 × 7 × 59 × 67 × 79 × 269 × 1889 An Origin is 4560 = 2 × 2 × 2 × 2 × 3 × 5 × 19 To make the result a multiple of the Origin, we thus need to multiply by 2 × 2 × 19 = 76, an Obscuration Factor. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- This also produces a multiple of Origin Concidence [41,040] = 9 × Origin Factor [4560], and so repetition of a lunar eclipse at the full moon of the first Celestial month is also ensured:
- see Proc. 3.1.
- The result of this calculation will thus be the period after which all the initial conditions of the system at High Origin (see section § 256) will repeat.
- This is not an important quantity in the calculations underlying the Han Quarter Remain- der, nor is it used elsewhere in the system.
- Neither the Triple Concordance system nor not the Uranic Manifestation system contain anything similar.

### cullen:chunk:110 §86 p.189-190 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四千三百二十七 | 4327. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 周率 | §86 Cycle Rate: | sequential_baseline_alignment, order_proximity, term_cycle_rate |

### cullen:chunk:111 §87 p.189-190 Proc. 3.36

Clauses: zh=2, en=2, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四千七百二十五 | 4725. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 日率 | §87 Solar Rate: | sequential_baseline_alignment, order_proximity, term_solar_rate |

Commentary, not aligned:
- The Cycle Rate is the number of conjunctions of Jupiter with the sun (not counting the initial conjunction at High Origin) that take place while the sun performs Solar Rate circuits of the heavens, i.e. in Solar Rate solar cycles.
- 15 If Jupiter were a fixed star, these numbers would be equal.
- The number of con - junctions (Cycle Rate) is however less than the number of solar cycles elapsed (Solar Rate), since Jupiter is itself performing circuits of the heavens in the same direction as the sun, but more slowly.
- The difference 4725 − 4327 = 398 is the number of complete circuits of the heavens performed by Jupiter in Solar Rate solar cycles.

### cullen:chunk:112 §88 p.190 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 十三 | 13. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 合積月 | §88 Conjunction Accumulated Lunations: | sequential_baseline_alignment, order_proximity, term_accumulated_months |

### cullen:chunk:113 §89 p.190 Proc. 3.36

Clauses: zh=2, en=2, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四萬一千六百六 | 41,606. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 68 | one_to_one | 月餘 | §89 Lunation Remainder: | sequential_baseline_alignment, order_proximity, term_lunation_remainder, result_remainder |

Commentary, not aligned:
- The number of solar cycles from one conjunction to another is evidently:
- 4725/4327 and since 235 lunations are exactly 19 solar cycles, the number of lunations between conjunctions is:
- (4725 × 235) / (4327 × 19) = 13 remainder 41,606

### cullen:chunk:114 §90 p.190 Proc. 3.36

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 月法 / 八萬二千二百一十三 | §90 Lunation Factor 82,213. | sequential_baseline_alignment, number_exact_match, term_lunation_factor |

Commentary, not aligned:
- (4327 × 19) = 82,213 This is the divisor in the division just performed, and hence it is the denominator or scale of the fractional part.

### cullen:chunk:115 §91 p.190 Proc. 3.36

Clauses: zh=4, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 81 | many_to_one | 大餘 / 二十三 / 小餘 / 八百四十七 | §91 Greater Remainder 23. | sequential_baseline_alignment, number_exact_match, term_greater_remainder, result_remainder |

Commentary, not aligned:
- 15 W e may recall that at this period the sun’s winter solstice position was assumed to be fixed with respect to the background of the stars, so that (in modern terms) the tropical and sidereal years were taken as equal.

### cullen:chunk:116 §92 p.191 Proc. 3.36

Clauses: zh=0, en=1, commentary=7

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §92 Lesser Remainder 847. |  |

Commentary, not aligned:
- These quantities enable us to find the date and time of the conjunction of sun and moon falling at the start of the lunation within which the conjunction of the sun and Jupiter occurs.
- The first is the amount to be added to the cyclical day number with which the system began, once for each conjunction.
- The second is the fraction of a day (at a scale of 940) to be added to the instant of midnight for each conjunction.
- We convert the Conjunction Accumulated Lunations to days, on the basis that one Obscuration contains precisely 27,759 days or 940 months:
- 13 × 27,759/940 = 383 + 847/940 847/940 is the fraction of a day after midnight when falls the solar-lunar conjunc- tion beginning the lunation in which the first conjunction after High Origin of Jupiter with the sun occurs.

### cullen:chunk:117 §93 p.191 Proc. 3.36

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 虛分 / 九十三 | §93 V oid Parts 93. | sequential_baseline_alignment, number_exact_match, term_void_parts |

Commentary, not aligned:
- 940 − 847 = 93 This is the fraction of a day remaining after the conjunction just considered occurs.

### cullen:chunk:118 §94 p.191-192 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 入月日 / 十五 | §94 Days of entry into month 15. | sequential_baseline_alignment, number_exact_match, term_days_entry_month |

### cullen:chunk:119 §95 p.191-192 Proc. 3.36

Clauses: zh=2, en=1, commentary=14

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 日餘 / 萬四千六百四十(七)[一] | §95 Day Remainder 14,641. | sequential_baseline_alignment, numbers_present_without_exact_match, term_day_remainder, result_remainder |

Commentary, not aligned:
- The two quantities given here tell us how far into the month the first conjunction after High Origin falls.
- The first part is the number of whole days, and the second is the fractional part of a day, at a scale of Day and Du Factor.
- These results may be obtained by adding two quantities:
- (a) The fractional parts of days left over at the end of the whole lunation in Accumulated Months.
- (b) The part of a month left over in one conjunction after discarding the whole months in Accumulated Months (Lunation Remainder) Let us carry out the calculation for Jupiter, for which we have:

### cullen:chunk:120 §96 p.192 Proc. 3.36

Clauses: zh=2, en=1, commentary=5

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日度法 / 萬七千三百八 | §96 Day and Du Factor 17,308. | sequential_baseline_alignment, number_exact_match, term_day_du_factor |

Commentary, not aligned:
- 4 × 4327 = 17,308 This is the denominator for two quantities:
- (a) The fr actional part of days above whole days and whole months for one conjunction.
- (b) The fr actional parts of a du moved by Jupiter relative to the stars from one conjunction to another.
- It is clear that these fractions must differ by exactly ¼, since the sun moves at 1 du/day, and thus after 365 days it still has to move ¼ du in ¼ day to reach the position from which Jupiter has shifted by an angle whose fractional part is (b).
- Thus the same divisor will apply to both fractions.

### cullen:chunk:121 §97 p.192-193 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 積度 / 三十三 | §97 Accumulated Du 33. | sequential_baseline_alignment, number_exact_match, term_accumulated_du |

### cullen:chunk:122 §98 p.192-193 Proc. 3.36

Clauses: zh=2, en=1, commentary=5

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 度餘 / 萬三百一十四 | §98 Du Remainder 10,314. | sequential_baseline_alignment, number_exact_match, term_du_remainder, result_remainder |

Commentary, not aligned:
- We may recall that:
- Jupiter Cycle Rate = 4327 Jupiter Solar Rate = 4725 4725 − 4327 = 398, so that in the time that the sun makes 4725 circuits of heaven, Jupiter makes 398 circuits relative to the stars and in the same direction as solar motion, since there are only 4327 conjunctions of Jupiter and the sun in that period.
- There are 1461 du in 4 whole circuits, and so 398 × 1461 = 581,478 is the number of du moved relative to the stars in 4 × 4327 years = 17,308 years.
- Thus, 581,478/17,308 = 33 + 10,314/17,308 is the number of du moved by Jupiter relative to the stars between conjunctions by Jupiter with the sun, with the remainder at a scale of Day and Du Factor.
- 火， Fire [Mars]

### cullen:chunk:123 §99 p.193 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 八百七十九 | 879. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 周率 | §99 Cycle Rate: | sequential_baseline_alignment, order_proximity, term_cycle_rate |

### cullen:chunk:124 §100 p.193 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 千八百七十六 | 1876. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 日率 | §100 Solar Rate: | sequential_baseline_alignment, order_proximity, term_solar_rate |

### cullen:chunk:125 §101 p.193 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 二十六 | 26. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 合積月 | §101 Conjunction Accumulated Lunations: | sequential_baseline_alignment, order_proximity, term_accumulated_months |

### cullen:chunk:126 §102 p.193 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 六千六百三十四 | 6634. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 68 | one_to_one | 月餘 | §102 Lunation Remainder: | sequential_baseline_alignment, order_proximity, term_lunation_remainder, result_remainder |

### cullen:chunk:127 §103 p.193 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 月法 / 萬六千七百一 | §103 Lunation Factor 16,701. | sequential_baseline_alignment, number_exact_match, term_lunation_factor |

### cullen:chunk:128 §104 p.193 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 大餘 / 四十七 | §104 Greater Remainder 47. | sequential_baseline_alignment, number_exact_match, term_greater_remainder, result_remainder |

### cullen:chunk:129 §105 p.193 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 小餘 / 七百五十四 | §105 Lesser Remainder 754. | sequential_baseline_alignment, number_exact_match, term_lesser_remainder, result_remainder |

### cullen:chunk:130 §106 p.193-194 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 虛分 / 一百八十六 | §106 V oid Parts 186. | sequential_baseline_alignment, number_exact_match, term_void_parts |

### cullen:chunk:131 §107 p.194 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | many_to_one | 入月日 / 十(一)[二] | §107 Days of entry into month 12. | sequential_baseline_alignment, numbers_present_without_exact_match, term_days_entry_month |

### cullen:chunk:132 §108 p.194 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 日餘 / 千八百七十二 | §108 Day Remainder 1872. | sequential_baseline_alignment, number_exact_match, term_day_remainder, result_remainder |

### cullen:chunk:133 §109 p.194 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日度法 / 三千五百一十六 | §109 Day and Du Factor 3516. | sequential_baseline_alignment, number_exact_match, term_day_du_factor |

### cullen:chunk:135 §110 p.194 Proc. 3.36

Clauses: zh=1, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 四十九 | §110 Accumulated Du 49. | sequential_baseline_alignment, order_proximity, number_exact_match |

### cullen:chunk:136 §111 p.194 Proc. 3.36

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 度餘 / 一百一十四 | §111 Du Remainder 114. | sequential_baseline_alignment, number_exact_match, term_du_remainder, result_remainder |

Commentary, not aligned:
- 土， Earth [Saturn]

### cullen:chunk:137 §112 p.194 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 九千九十六 | 9096. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 周率 | §112 Cycle Rate: | sequential_baseline_alignment, order_proximity, term_cycle_rate |

### cullen:chunk:138 §113 p.194 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 九千四百一十五 | 9415. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 日率 | §113 Solar Rate: | sequential_baseline_alignment, order_proximity, term_solar_rate |

### cullen:chunk:139 §114 p.194 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 十二 | 12. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 合積月 | §114 Conjunction Accumulated Lunations: | sequential_baseline_alignment, order_proximity, term_accumulated_months |

### cullen:chunk:140 §115 p.194 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 十三萬八千六百三十七 | 138,637. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 68 | one_to_one | 月餘 | §115 Lunation Remainder: | sequential_baseline_alignment, order_proximity, term_lunation_remainder, result_remainder |

### cullen:chunk:141 §116 p.194 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 月法 / 十七萬二千八百二十四 | §116 Lunation Factor 172,824. | sequential_baseline_alignment, number_exact_match, term_lunation_factor |

### cullen:chunk:142 §117 p.194-195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 大餘 / 五十四 | §117 Greater Remainder 54. | sequential_baseline_alignment, number_exact_match, term_greater_remainder, result_remainder |

### cullen:chunk:143 §118 p.194-195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 小餘 / 三百四十八 | §118 Lesser Remainder 348. | sequential_baseline_alignment, number_exact_match, term_lesser_remainder, result_remainder |

### cullen:chunk:144 §119 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 虛分 / 五百九十二 | §119 V oid Parts 592. | sequential_baseline_alignment, number_exact_match, term_void_parts |

### cullen:chunk:145 §120 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | many_to_one | 入月日 / 二十(三)[四] | §120 Days of entry into month 24. | sequential_baseline_alignment, numbers_present_without_exact_match, term_days_entry_month |

### cullen:chunk:146 §121 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 日餘 / 二千一百六十三 | §121 Day Remainder 2163. | sequential_baseline_alignment, number_exact_match, term_day_remainder, result_remainder |

### cullen:chunk:147 §122 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日度法 / 三萬六千三百八十四 | §122 Day and Du Factor 36,384. | sequential_baseline_alignment, number_exact_match, term_day_du_factor |

### cullen:chunk:148 §123 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 積度 / 十二 | §123 Accumulated Du 12. | sequential_baseline_alignment, number_exact_match, term_accumulated_du |

### cullen:chunk:149 §124 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 度餘 / 二萬九千四百五十一 | §124 Du Remainder 29,451. | sequential_baseline_alignment, number_exact_match, term_du_remainder, result_remainder |

Commentary, not aligned:
- 金， Metal [Venus]

### cullen:chunk:150 §125 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 周率 / 五千八百三十 | §125 Cycle Rate 5830. | sequential_baseline_alignment, number_exact_match, term_cycle_rate |

### cullen:chunk:151 §126 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日率 / 四千六百六十一 | §126 Solar Rate 4661. | sequential_baseline_alignment, number_exact_match, term_solar_rate |

### cullen:chunk:152 §127 p.195 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 九 | 9. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 合積月 | §127 Conjunction Accumulated Lunations: | sequential_baseline_alignment, order_proximity, term_accumulated_months |

### cullen:chunk:153 §128 p.195 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 九萬八千四百五 | 98,405. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 68 | one_to_one | 月餘 | §128 Lunation Remainder: | sequential_baseline_alignment, order_proximity, term_lunation_remainder, result_remainder |

### cullen:chunk:154 §129 p.195 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | many_to_one | 月法 / 十[一]萬七百七十 | §129 Lunation Factor 110,770. | sequential_baseline_alignment, numbers_present_without_exact_match, term_lunation_factor |

### cullen:chunk:155 §130 p.195-196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 大餘 / 二十五 | §130 Greater Remainder 25. | sequential_baseline_alignment, number_exact_match, term_greater_remainder, result_remainder |

### cullen:chunk:156 §131 p.195-196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 小餘 / 七百三十一 | §131 Lesser Remainder 731. | sequential_baseline_alignment, number_exact_match, term_lesser_remainder, result_remainder |

### cullen:chunk:157 §132 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 虛分 / 二百九 | §132 V oid Parts 209. | sequential_baseline_alignment, number_exact_match, term_void_parts |

### cullen:chunk:158 §133 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 入月日 / 二十六 | §133 Days of entry into month 26. | sequential_baseline_alignment, number_exact_match, term_days_entry_month |

### cullen:chunk:159 §134 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 日餘 / 二百八十一 | §134 Day Remainder 281. | sequential_baseline_alignment, number_exact_match, term_day_remainder, result_remainder |

### cullen:chunk:160 §135 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日度法 / 二萬三千三百二十 | §135 Day and Du Factor 23,320. | sequential_baseline_alignment, number_exact_match, term_day_du_factor |

### cullen:chunk:161 §136 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 積度 / 二百九十二 | §136 Accumulated Du 292. | sequential_baseline_alignment, number_exact_match, term_accumulated_du |

### cullen:chunk:162 §137 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 度餘 / 二百八十一 | §137 Du Remainder 281. | sequential_baseline_alignment, number_exact_match, term_du_remainder, result_remainder |

Commentary, not aligned:
- 水， Water [Mercury]

### cullen:chunk:163 §138 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 周率 / 萬一千九百八 | §138 Cycle Rate 11,908. | sequential_baseline_alignment, number_exact_match, term_cycle_rate |

### cullen:chunk:164 §139 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 日率 / 千八百八十九 | §139 Solar Rate 1889. | sequential_baseline_alignment, number_exact_match, term_solar_rate |

### cullen:chunk:165 §140 p.196 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 一 | 1. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | medium | 58 | one_to_one | 合積月 | §140 Conjunction Accumulated Lunations: | sequential_baseline_alignment, order_proximity, term_accumulated_months |

### cullen:chunk:166 §141 p.196 Proc. 3.36

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 68 | one_to_one | 月餘 | §141 Lunation Remainder: | sequential_baseline_alignment, order_proximity, term_lunation_remainder, result_remainder |
| aligned | medium | 54 | one_to_one | 二十一萬七千六百六十[三] | 217,663 (restored following Qian Daxin 錢大昕). | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

### cullen:chunk:167 §142 p.196 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 月法 / 二十二萬六千二百五十二 | §142 Lunation Factor 226,252. | sequential_baseline_alignment, number_exact_match, term_lunation_factor |

### cullen:chunk:168 §143 p.197 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 大餘 / 二十九 | §143 Greater Remainder 29. | sequential_baseline_alignment, number_exact_match, term_greater_remainder, result_remainder |

### cullen:chunk:169 §144 p.197 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 83 | many_to_one | 小餘 / 四百九十九 | §144 Lesser Remainder 499. | sequential_baseline_alignment, number_exact_match, term_lesser_remainder, result_remainder |

### cullen:chunk:170 §145 p.197 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | many_to_one | 虛分 / 四百四十(九)[一].16 | §145 V oid Parts 441. | sequential_baseline_alignment, numbers_present_without_exact_match, term_void_parts |

### cullen:chunk:171 §146 p.197 Proc. 3.36

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 55 | many_to_one | 入月日 / 二十(七)[八].17 日餘 / 四萬四千八百五 | §146 Days of entry into month 28. | sequential_baseline_alignment, numbers_present_without_exact_match, term_days_entry_month |

### cullen:chunk:172 §147 p.197 Proc. 3.36

Clauses: zh=0, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §147 Day Remainder 44,805. |  |

### cullen:chunk:173 §148 p.197 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | many_to_one | 日度法 / 四萬七千六百三十(一)[二].18 | §148 Day and Du Factor 47,632. | sequential_baseline_alignment, numbers_present_without_exact_match, term_day_du_factor |

### cullen:chunk:174 §149 p.197 Proc. 3.36

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | many_to_one | 積度 / 五十七 | §149 Accumulated Du 57. | sequential_baseline_alignment, number_exact_match, term_accumulated_du |

### cullen:chunk:175 §150 p.197 Proc. 3.36

Clauses: zh=1, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 93 | one_to_one | 度餘四萬四千八百五 | §150 Du Remainder 44,805. | sequential_baseline_alignment, order_proximity, number_exact_match, term_du_remainder, result_remainder |

### cullen:chunk:176 §151 p.197-198 Proc. 3.37

Clauses: zh=3, en=1, commentary=6

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 55 | many_to_one | 推五星術 / 置上元以來 / 盡所求年 | §151 Set out the years since High Origin, exhausting the year sought. | sequential_baseline_alignment, numbers_present_without_exact_match, operation_set_out |

Commentary, not aligned:
- This expression ‘exhausting the year sought’ means that we take the number of years elapsed between High Origin and the end of the current year (or more precisely the winter solstice that ends the current solar cycle).
- In the following 16 Emended following Qian Daxin.
- 17 Emended following Qian Daxin.
- 18 Emended following Qian Daxin.
- sections, we shall look back from that year-end position and ask when the most recent planetary conjunction occurred.

### cullen:chunk:177 §152 p.198 Proc. 3.37

Clauses: zh=3, en=1, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | many_to_one | 以周率乘之 / 滿日率得一 / 名為積合 | §152 Multiply by Cycle Rate, and obtain 1 for each filling of the Solar Rate. | sequential_baseline_alignment, number_exact_match, term_cycle_rate, term_solar_rate, operation_multiply, operation_fill_count, operation_obtain |

Commentary, not aligned:
- Call this Accumulated Conjunctions.
- Solar Rate is the number of circuits of heaven by the sun (and hence the number of solar cycles from winter solstice to winter solstice) in which Jupiter undergoes Cycle Rate conjunctions with the sun.
- Hence this calculation gives the number of conjunctions of the planet with the sun from High Origin up to the winter solstice at the end of the current year, excluding the conjunction at High Origin itself.

### cullen:chunk:178 §153 p.198 Proc. 3.37

Clauses: zh=1, en=1, commentary=3

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | one_to_one | 不盡名[為]合餘 | §153 What is not exhausted, call it Conjunctions Remainder. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_not_exhausted_or_not_fill, result_remainder |

Commentary, not aligned:
- Conjunctions Remainder is the remainder from:
- Solar cycles × Cycle Rate/Solar Rate.
- It represents the part of a conjunction completed at the winter solstice at the end of the solar cycle, at a scale of Solar Rate.

### cullen:chunk:179 §154 p.198-199 Proc. 3.37

Clauses: zh=6, en=15, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 78 | one_to_many | 〔合〕餘以周率除之 | §154 As for Conjunctions Remainder, cast out Cycle Rate from it. / (When one does not get [a conjunction] there, then one steps back a year [to find it].)19 If nothing is obtained, the planet has a conjunction in that year. | sequential_baseline_alignment, order_proximity, term_cycle_rate, operation_cast_out_or_divide, result_remainder |
| aligned | medium | 68 | one_to_many | 二合前 二年. | If Conjunction Remainder >2 × Cycle Rate at year’s end, then the conjunction was more than two years ago. / The interpretation of the sentence 不得焉退歲 seems supported by the later usage of 退歲 to mean the years one has to step back from the present year to find a year with a conjunction: / see section § 163. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 44 | one_to_many | 不得焉退歲 | If 1 is obtained, then it is one year before, and if two are obtained it is two years before. / Conjunctions Remainder is the remainder from: / Solar Cycles × Cycle Rate/Solar Rate. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 無所得 | 19 This bracketed portion may be intruded, since it breaks the obvious sequence of the rest of the text. / One full conjunction matures each time the Conjunction Remainder becomes equal to Solar Rate = 4725 for Jupiter. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_many | 星合其年 | In one solar cycle, the fraction of a con - junction that is added is (Cycle Rate) / (Solar Rate) = 4327/4725 for Jupiter. / So Conjunction Remainder increases by Cycle Rate each solar cycle. / Now if Conjunction Remainder = Cycle Rate at year’s end, it was clearly zero at the start of the solar cycle, i.e. the cycle began with a conjunction at winter solstice. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 得一合前年 | If Conjunction Remainder < Cycle Rate at the solstice at year’s end, then clearly the conjunction was less than a year ago, i.e. within the present year. / If Conjunction Remainder > Cycle Rate at the solstice at year’s end, then the conjunction was more than one year ago, i.e. before the start of the present year. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:180 §155 p.199 Proc. 3.37

Clauses: zh=2, en=4, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | one_to_many | 水積合奇為晨 | §155 For Venus and Mercury, if the [number of] conjunctions is odd, then it is in the morning; / if it is even it is evening. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 52 | one_to_many | 偶為夕 | A ‘morning’ conjunction is a conjunction followed by a morning appearance, and so on. / Since morning and evening appearances alternate with one another, clearly there is an ‘evening’ conjunction for both planets at High Origin, so the first conjunction thereafter is ‘morning’. | sequential_baseline_alignment, order_proximity, definition_make_or_is |

### cullen:chunk:181 §156 p.199-200 Proc. 3.37

Clauses: zh=2, en=5, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 89 | one_to_many | 其不滿周率者反減之 | §156 What does not fill Cycle Rate, subtract back [from Cycle Rate], and the remainder is Du Parts. / So Du Parts = Cycle Rate – Conjunction Remainder And Conjunction Remainder = Cycle Rate – Du Parts Now since each complete solar cycle adds Cycle Rate to Conjunction Remainder, and from one conjunction to the next, the amount added between the solstice at the start of the year and the last conjunction must have been Du Parts, the fraction of a solar cycle from the solstice to the last conjunction would be: | sequential_baseline_alignment, order_proximity, term_cycle_rate, operation_subtract, operation_fill_count, result_not_exhausted_or_not_fill |
| aligned | low | 40 | one_to_many | 餘為度分 | Du Parts / (Cycle Rate) Expressing this in du moved by the sun between the solstice and conjunction with the planet, we obtain: / (1461/4) × Du Parts / (Cycle Rate) = (Circuits of Heaven [1461]) × Du Parts / (Day and Du Factor) as prescribed below. / The fractional part of this will be in du at a scale of Day and Du Factor. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:182 §157 p.200 Proc. 3.38

Clauses: zh=5, en=2, commentary=4

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 77 | many_to_one | 推星合月 / 以合積月乘積合為小積 | §157 By the Conjunction Accumulated Lunations multiply Accumulated Conjunc - tions to make the Lesser Accumulation, and further by Lunation Remainder multiply Accumulated Conjunctions, counting one for filling of the Lunation Factor and letting that go with the Lesser Accumulation to make Accumu - lated Months. | sequential_baseline_alignment, order_proximity, term_accumulated_months, operation_multiply, definition_make_or_is |
| aligned | high | 76 | many_to_one | 又以月餘乘積合 / 滿其月法得一 / 從小積[為積月, 不盡]為月餘 | What is not exhausted makes Lunation Remainder. | sequential_baseline_alignment, order_proximity, term_lunation_remainder, definition_make_or_is, result_not_exhausted_or_not_fill, result_remainder |

Commentary, not aligned:
- This is the first of three sections on this topic.
- The calculation just specified in Proc. 38 yields the number of whole luna - tions between High Origin and the last conjunction of the planet before the solstice at the end of the present year (Accumulated Months), together with the remaining fraction of a lunation (Lunation Remainder) taking us up to the instant of the conjunction itself, at a scale of Lunation Factor.
- Note that Lunation Remainder here refers to two different quantities in succession:
- first the fraction of a lunation between planetary conjunctions, and second the fraction remaining when this quantity is multiplied by Accumulated Conjunc - tions, the integral part being removed and added to the total of months.

### cullen:chunk:183 §158 p.200-201 Proc. 3.38

Clauses: zh=5, en=4, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | one_to_one | 積月滿紀月去之 | §158 As Accumulated Months fills Era Months cast them out, and the remain - der makes months entered into the Era. | sequential_baseline_alignment, order_proximity, term_accumulated_months, operation_fill_count |
| aligned | medium | 55 | one_to_one | 餘為入紀月 | In each case multiply this by Rule Intercalations [7], and as this fills Rule Months [235] get one, to make an intercalation. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 61 | many_to_one | 滿章月得一為閏 / 不盡為 閏餘 | The Era is the period of 1520 years or 18,800 months giving repeat of concor - dance for conjunction, qi inception, time of day and sexagenary day number. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, definition_make_or_is |
| aligned | low | 43 | one_to_one | 每以章閏乘之 | What is not exhausted makes Intercalation Remainder. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- The calculation here tells us how many of the remaining months must have been intercalary ones, and how much of an intercalary month has been accumulated since the last was inserted.

### cullen:chunk:184 §159 p.201 Proc. 3.38

Clauses: zh=8, en=9, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | one_to_one | 其餘以十二去之 | The remainder is the number of months entered into the year. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 55 | one_to_one | 餘為入歲月數 | Start off from the Celestial Standard [month, which is] the 11th [Xia] month, and outside the count is the month of the planet’s conjunction. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 53 | one_to_one | 從天正十一月起 | If the Intercalation Remainder fills from 224 up to 231, then the planet’s conjunction is in the intercalary month. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 52 | one_to_one | 其閏[餘]滿二百二十四以上至二百三十一星合閏月 | When we subtract the intercalary months, we are left with the months in the present year, plus a multiple of 12 months representing whole years. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 以閏減入紀月 | §159 By the intercalations diminish the months entered into the Era, and cast out 12 from the remainder. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 筭外, 星合所在之月也 | The inter - calation may be shifted back and forth, but it is ruled by the conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_one | 閏或 進退 | Subtracting the latter, we have the months in the present year preceding the month in which the conjunction occurs, on the Celestial month count. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 以朔制之 | Of course the month of conjunction may be an intercalary month itself. / See section § 50 for an explana - tion of the numbers 224 and 231, as well as the reference to shifting ‘back and forth’. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:185 §160 p.201-202 Proc. 3.39

Clauses: zh=8, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 87 | one_to_one | 滿蔀月得一為積日 | As the Accumulated Days fill 60, cast that out, and the remainder is the Greater Remainder. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_accumulated_days, operation_fill_count, definition_make_or_is |
| aligned | medium | 55 | one_to_one | 不盡為小餘 | Count it off starting from jiazi.1, and outside the count is the conjunction day of the month of the planet’s conjunction. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | one_to_one | 積日滿六十去之, 餘為大餘 | The ‘conjunction day’ here is the day of the solar-lunar conjunction that begins the month in which the conjunction falls. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 46 | one_to_one | 推朔日 | §160 By Obscuration Days multiply the months into the Era, and as this fills Obscuration Months get one to make Accumulated Days. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以蔀日乘(之)入紀月 | What is not exhausted is the Lesser Remainder. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_one | 命以甲子 | The procedure is a simple conversion of whole months into days and fractions of a day at a scale of Obscuration Months [940], using the equivalence: | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 筭外 / 星合月朔日 | Obscuration Days [27,759] = Obscuration Months [940] We then cast out multiples of 60 from the whole days to find the shift of the cyclical day number from the initial value at High Origin. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:186 §161 p.202-203 Proc. 3.40

Clauses: zh=11, en=11, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | one_to_one | 以其月法乘朔小餘 | What is not exhausted is the Day Remainder. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 54 | one_to_one | 以四千四百六十五約之 | Lunation Remainder here is used in the second of its two meanings, i.e. the fractional part of a lunation from the solar-lunar conjunction at the start of the month to the instant of planetary conjunction, at a scale of Lunation Factor, which is Cycle Rate × 19. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 54 | one_to_one | 所得 (得)滿日度法得一 | However, the end result of this procedure has to be in days at a scale of Cycle Rate × 4. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推入月日 | §161 By Obscuration Days [27,759] multiply Lunation Remainder, and by the Lunation Factor multiply the Lesser Remainder for the conjunction [i.e. the luni-solar conjunction beginning this lunation], and let it go with [the previous result]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以蔀日乘月餘 | Simplify by 4465, and for what you obtain, get one for each filling of the Day and Du Factor, to make the days entered into the month. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 從之 | Count off the days entered into the month from the conjunction [day], and outside the count is the day of [the planet’s] conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 為入月日 | Now days convert to lunations as follows: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 不盡為日餘 | Lunations = Days × Obscuration Months [940]/Obscuration Days [27,759] So in this procedure, we start with: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 以朔命入月日 | Lunations × (Cycle Rate × 19), then multiply by 27,759 and divide by 4465, to produce: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 筭外 | Lunations × (Cycle Rate × 19) × 27,759/4465 = (Days × 940/27,759) × (Cycle Rate × 19) × 27,759/4465 = (Days × Cycle Rate) × 940 × 19/4465 And since 4465 = 235 × 19, we have (Days × Cycle Rate) × 940 × 19 / (235 × 19) = Days × (Cycle Rate × 4), as specified since (Cycle Rate × 4) is Day and Du Factor. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 星合日也 | Turning to the second quantity, Lunation Factor = (Cycle Rate × 19), so multi- plying Lesser Remainder by this raises the scale to Cycle Rate × 19 × 940 And 4465 = 235 × 19, So the simplification by 4465 prescribed changes the scale to Cycle Rate × 19 × 940 / (235 × 19) = Cycle Rate × 4, which is Day and Du Factor as required. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:187 §162 p.203 Proc. 3.41

Clauses: zh=7, en=11, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 53 | one_to_one | 滿日度法得一為積度 | Count off the du from 21¼ du of Dipper. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 54 | one_to_many | 不盡為度餘 | Outside the count, that is the du where the star has its conjunction. / Du Parts is the fraction of a solar cycle between the last winter solstice and the current conjunction of the sun with the planet; | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 53 | one_to_one | 以斗二十一四分 之一命度 | see section § 156. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 推合度 | §162 By circuit s of heaven multiply Du Parts. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 以周天乘度分 | As this fills Day and Du Factor, obtain 1 to make Accumulated Du. / What is not exhausted makes Du Remainder. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 筭外 | As shown there, (Circuits of Heaven) × Du Parts / (Day and Du Factor) gives the distance moved by the sun from winter solstice (at 21¼ du of Dipper) to conjunction with the planet, as specified here. / The integral result of the calculation, Accumulated Du, is the number of du moved by the sun between winter solstice and conjunction. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 星合所在度也 | It is therefore the number of days elapsed from winter solstice to conjunction. / The remainder is in du at a scale of (Day and Du Factor) / (Circuits of Heaven) | sequential_baseline_alignment, order_proximity |

### cullen:chunk:188 §163 p.203-204 Proc. 3.42

Clauses: zh=9, en=4, commentary=10

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 94 | many_to_one | 以減上元 / 滿八十除去之 | Cast out what fills 80, and multiply the remainder by the Extinction Number [21]. | sequential_baseline_alignment, order_proximity, number_exact_match, operation_cast_out_or_divide, operation_fill_count |
| aligned | high | 100 | many_to_one | 餘以沒數乘之 / 滿日法得一, 為大餘 | Count one for each filling of the Day Factor [4], to make the Greater Remainder, and let what is not exhausted be the Lesser Remainder. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, term_greater_remainder, term_day_factor, operation_fill_count, definition_make_or_is, result_remainder |
| aligned | high | 86 | many_to_one | 不盡為小餘 / 以甲子命大餘 / 則星合歲天正冬至日也 | Count off the Greater Remainder from the jiazi, and then that is the day of the winter solstice for the Celestial first month in the year of the planet’s conjunction. | sequential_baseline_alignment, order_proximity, term_greater_remainder, operation_count_or_name, definition_make_or_is, result_remainder |
| aligned | medium | 64 | many_to_one | 一術 / 加退歲一 | §163 Add one to the years stepped back, and subtract from [the years to] High Origin. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_add |

Commentary, not aligned:
- What are the ‘years stepped back’? It is clear that the result of:
- (Years to High Origin) − (Years Stepped Back + 1) gives the interval in years from High Origin to the winter solstice preceding the conjunction.
- We recall that in calculating ‘High Origin’, we were told to include the current year.
- If ‘Years Stepped Back’ are the count from the present year back to when the conjunction actually occurred, this makes sense.
- Suppose that we find that we are in year 100, but the conjunction occurred the year before the present year, then clearly there was an interval of 98 years from High Origin to the winter solstice before the conjunction.

### cullen:chunk:189 §164 p.204-205 Proc. 3.42

Clauses: zh=5, en=3, commentary=12

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 92 | one_to_one | 以周率[乘]小餘 | §164 By Cycle Rate multiply the Lesser Remainder , and add it to Du Remainder, and let the number of times this [combined] Remainder fills Day and Du Factor go with the Du. | sequential_baseline_alignment, order_proximity, term_lesser_remainder, term_cycle_rate, operation_multiply, result_remainder |
| aligned | low | 43 | many_to_one | 并度餘 / 餘滿日度法從度 | Then this is the number of days after the solstice that the planet’s conjunction [takes place]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 即(正)[至]後星合日數也 / 命以 冬至 | Count it off from the winter solstice. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- Lesser Remainder is the fraction of a day by which the solstice falls after midnight, at a scale of Day Factor [4].
- Multiplication by Cycle Rate raises the scale to 4 × Cycle Rate = Day and Du Factor, as required.
- Du Remainder (like Month Remainder) has two meanings:
- 1.
- The fr actional part of the angular motion of the planet between conjunc - tions, given once for each planet in the initial listing of constants.

### cullen:chunk:191 §165 p.205 Proc. 3.43

Clauses: zh=2, en=4, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 62 | one_to_many | (一)[金、水]加晨得夕 | §165 Add Conjunction Accumulated Lunations to the Months of Entry into the Year, and add the Month Remainder to the Month Remainder, counting one for each filling of Lunation factor and letting that go with the Months of Entry into the Year. / If the Months of Entry into the Year fill 12, cast it out, reckoning into that any intercalary month. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_add |
| aligned | medium | 54 | one_to_many | 加夕得晨 | As for the remainder, count off as before, and outside the count, that is the month of the next conjunction. / For Venus and Mercury, if one adds to a dawn appearance one gets a dusk appearance, and if one adds to a dusk appearance one gets a dawn appearance. | sequential_baseline_alignment, order_proximity, operation_obtain |

### cullen:chunk:192 §166 p.205 Proc. 3.44

Clauses: zh=8, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 100 | many_to_one | 求朔日 / 以大小餘加今所得 / 其月餘得一月者 / 又[加大]餘二十九 / [小餘四百九十 九 / ]小飾滿蔀月得一 / (如)[加]大餘 / 大餘命如前 | §166 By the Greater and Lesser Remainders add to those you now obtain, and when from the Month Remainder you get one month, further to the Greater Remainder add 29, and to the Lesser Remainder 499, and when the Lesser Remaind er fills Obscuration Months [940] obtain 1, and add to the Greater Remainder, then the Greater Remainder is counted off as before. | sequential_baseline_alignment, number_exact_match, number_exact_match, term_greater_remainder, term_lesser_remainder, term_rule_months, operation_add, operation_fill_count, operation_obtain, result_remainder |

Commentary, not aligned:
- This section and the two following simply add on one conjunction’s worth of constants onto the values already obtained, to find the values for the next con - junction of the planet with the sun.

### cullen:chunk:193 §167 p.206 Proc. 3.45

Clauses: zh=9, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 82 | many_to_one | 求入月日 / 以入月日[日]餘加今所得 / 餘滿日度法得一 / 從日 | §167 By the Days of Entry Into the Month, and the Day Remainder add to those you now obtain. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_add, operation_obtain, result_remainder |
| aligned | high | 85 | many_to_one | 其前合月朔小餘(不)滿 其虛分者 / 空加一日 / 日滿月先去二十九 / 其後合月朔小餘不滿四百九十九, 又減一日 / 其餘命如前 | As the remainder fills Day and Du Factor obtain 1, and let it go with the days. | sequential_baseline_alignment, order_proximity, number_exact_match, operation_fill_count, result_remainder |

### cullen:chunk:194 §168 p.206 Proc. 3.46

Clauses: zh=5, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 89 | many_to_one | 求合度 / 以積度度餘加今所得 | §168 Add the Accumulated Du and the Du Remainder to what you have obtained, and as the remainder fills the Day and Du Factor let it go with the du. | sequential_baseline_alignment, order_proximity, term_du_remainder, term_accumulated_du, operation_add, result_remainder |
| aligned | medium | 64 | many_to_one | 餘滿日度法得一從度 / 命如前 / 經斗除如周率矣 | Count it off as before, and as you pass through Dipper cast out what accords with Cycle Rate. | sequential_baseline_alignment, order_proximity, term_cycle_rate, operation_cast_out_or_divide |

### cullen:chunk:196 §169 p.206-207 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 晨伏 / 十六日七千(二)[三]百二十分半 / 行二度萬三千八百一十一分 | §169 Having become invisible at dawn, in 16 days and 7320 and ½ parts, it moves 2 du and 13,811 parts | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:197 §170 p.207 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後十三度有奇 / 而見東方 | §170 When it becomes visible in the east, it is 13 du and a bit behind the Sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:198 §171 p.207 

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 64 | many_to_one | 見順 / 日行五十八分度之十一 / 五十八日行十一度 / 微遟 | §171 On visibility, it moves direct, moving 11/58 du in a day, and in 58 days it moves 11 du, [then] slows slightly. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:199 §172 p.207 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 日行九分 / 五十八日行九度 | §172 It moves 9 parts [of a du] in a day, and in 58 days it moves 9 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:200 §173 p.207 

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 二十五日 | §173 It becomes stationary and does not move for 25 days. | sequential_baseline_alignment, number_exact_match |

Commentary, not aligned:
- As in the Triple Conjunction.

### cullen:chunk:201 §174 p.207 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 旋逆 | §174 It turns back retrograde, and in a day moves 1/7 du, and in 84 days it retreats 12 du. | sequential_baseline_alignment, order_proximity |
| aligned | low | 41 | many_to_one | 日行七分度之一 / 八十四日(進)[退]十二度 | As in the Triple Conjunction. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:202 §175 p.207 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 復留 / 二十五日 | §175 It is once more stationary, for 25 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:203 §176 p.207 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 復順 / 五十八日行九度 | §176 It returns to [moving] direct, and in 58 days moves 9 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:204 §177 p.207 

Clauses: zh=1, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | one_to_one | 又五十八日行十一度 | §177 Again in 58 days it moves 11 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |

### cullen:chunk:205 §178 p.207-208 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日前十三度有奇 / 而夕伏西方 | §178 When it becomes invisible in the west, it is 13 du and a bit in advance of the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:206 §179 p.208 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 一見三百六十六日 / 行二十八度 | 58 + 58 + 25 + 84 + 25 + 58 + 58 = 366 11 + 9 − 12 + 9 + 11 = 28 | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 除伏逆 | §179 Casting out invisibility and retrograde motion, one Appearance is 366 days, and it moves 28 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:207 §180 p.208 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 伏復十六日七千(二)[三]百二十分半 / 行二度萬三千八百一十一分 / 而與 日合 | §180 On becoming invisible, during a further 16 days and 7320 and ½ parts, it moves 2 du and 13,811 parts, and has conjunction with the Sun. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:208 §181 p.208 

Clauses: zh=4, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 74 | one_to_many | 三百九十八日有萬四千六百四十一分 | 366 + 16 + 7320½ parts + 16 + 7320½ parts = 398 + 14,641 parts; / since Jupiter Day and Du Factor is 17,308, this is as calculated in the text. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | high | 74 | one_to_many | 通率日行四千七百二十五分之三百九十八 | 33 du and 10,314 parts = 581,478 du parts 398 days + 14,641 parts = 6,903,225 day parts Thus Day Rate is 581,478/6,903,225 du/day = 398/4725 du/day precisely as in text. / 火， Fire [Mars] | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 54 | one_to_one | 凡一終 | §181 In one termination [of a cycle], in 398 days and 14,641 parts it moves [relative to] the stars 33 du and 10,314 parts ． The overall rate for one day’s motion is 398/4725. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 69 | one_to_many | 行星三十(二)[三]度與萬 三百一十四分 | 28 + 2 + 13,811 parts + 2 + 13,811 parts = 32 + 27,622 parts; / since Jupiter Day and Du Factor is 17,308, this is 33 and 10,314 parts, as calculated in the text. | sequential_baseline_alignment, order_proximity, number_exact_match |

### cullen:chunk:209 §182 p.208 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 晨伏 / 七十一日二千六百九十四分 / 行五十五度二千二百五十四分半 | §182 Having become invisible at dawn, in 71 days and 2694 parts, it moves 55 du and 2254 parts. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:211 §183 p.209 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 36 | many_to_one | 度有奇 / 而見東方 | §183 When it becomes visible in the east, it is 16 du and a bit behind the Sun. | sequential_baseline_alignment |

### cullen:chunk:212 §184 p.209 

Clauses: zh=4, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 72 | many_to_one | 見順 / 日行二十三分度之十四 | §184 On visibility, it moves direct, moving 14/23 du in a day, and in 184 days it moves 112 du and slows slightly. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 50 | many_to_one | [百]八十四日行[百]一十二度 / 微遟 | 184 × 14/23 = 112 exactly | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

### cullen:chunk:213 §185 p.209 

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 日行十二分 / 九十二日行四十八度 | §185 It moves 12 parts in a day, and in 92 days it moves 48 du. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

Commentary, not aligned:
- (48/92 = 12/23) The total number of days since dawn appearance is 276, as in the Triple Con - cordance, which does not however subdivide this motion.

### cullen:chunk:214 §186 p.209 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 十一日 | §186 It delays and does not move for 11 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:215 §187 p.209 

Clauses: zh=3, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | one_to_one | 日行六十二分度之十七 | In 62 days it goes back 17 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 旋逆 | §187 It turns and retrogrades, and in a day moves 17/62 du. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 六十二日退十七度 | As in Triple Concordance. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:216 §188 p.209 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 復留 / 十一日 | §188 It delays once more, for 11 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:217 §189 p.209 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 65 | many_to_one | 復順 / 九十二日 / 行四十八度 | §189 It returns to direct motion for 92 days, and moves 48 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:218 §190 p.209-210 

Clauses: zh=1, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | one_to_one | 又百八十四日行百一十二度 | §190 Further , in 184 days it moves 112 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |

Commentary, not aligned:
- The total number of days in the last two phases before dusk setting is 276, as in the Triple Concordance, which does not however subdivide this motion.

### cullen:chunk:219 §191 p.210 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日前十六度有奇 / 而夕伏西方 | §191 When it sets in the west at dusk it is 16 du and a bit in advance of the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:220 §192 p.210 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 一見六百三十六日 / 行[三]百三度 | (184 + 92 + 11 + 62 + 11 + 92 + 184) days = 636 days (112 + 48 − 17 + 48 + 112) du = 303 du | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 除伏逆 | §192 Discarding invisibility and retrogradation, one Appearance is 636 days, and it moves 303 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:221 §193 p.210 

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 69 | many_to_one | 伏復 / 七十一日二千六百九十四分 / 行五十五度二千二百五十四分半 / 而與 日合 | §193 It moves while invisible, and in 71 days and 2694 parts, it moves 55 du and 2254½ parts, then is in conjunction with the sun. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:222 §194 p.210-211 

Clauses: zh=4, en=7, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 74 | one_to_many | 行星四百一十四度與九百九十三 分 | since Mars Day and Du Factor is 3516, this is 779 days and 1872 parts, as in text 303 + 55 + 2254½ parts + 55 + 2254½ parts = 413 + 4509 parts. / since Mars Day and Du Factor is 3516, this is 414 du and 993 parts, as in text. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | high | 74 | one_to_many | 通率日行千八百七十六分之九百九十七 | 414 du and 993 parts = 1,456,617 du parts 779 days and 1872 parts = 2,740,836 Thus Day Rate is 1,456,617/2,740,836 du/day = 997/1876 du/day precisely as in text. / 土， Earth [Saturn] | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 54 | one_to_one | 凡一終 | §194 For one termination [of a cycle], there are 779 days and 1872 parts, and it moves [relative to] the stars 414 du and 993 parts. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 52 | one_to_many | 七百七十九日有千八百七十二分 | The overall rate for one day’s motion is 997/1876. / 636 + 71 + 2694 parts + 71 days + 2694 parts = 778 days + 5388 parts; | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

### cullen:chunk:223 §195 p.211 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 晨伏 / 十九日千八十一分半 / 行三度萬四千七百二十五分半 | §195 Having become invisible at dawn, in 19 days and 1081½ parts, it moves 3 du and 14,725½ parts. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:224 §196 p.211 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後十五度有奇 / 而見東方 | §196 When it becomes visible in the east, it is 15 du and a bit behind the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:225 §197 p.211 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | many_to_one | 日行四十三分度之三 / 八十六日行六度 | 6/86 = 3/43 | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 見順 | §197 On visibility, it moves direct, moving 3/43 du in a day, and in 86 days it moves 6 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:226 §198 p.211 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 三十三日 | §198 It delays and does not move for 33 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:227 §199 p.211 

Clauses: zh=3, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 日行十七分度之一, 百二日退六度 / 20 | In 102 day it retreats 6 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 旋逆 | §199 It moves retrograde, and in a day moves 1/17 du. | sequential_baseline_alignment, order_proximity |

Commentary, not aligned:
- 102/17 = 6

### cullen:chunk:228 §200 p.211 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 復留 / 三十三日 | §200 It delays once more, for 33 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:229 §201 p.211 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 65 | many_to_one | 復順 / 八十六日 / 行六度 | §201 It returns to direct motion for 86 days, and moves 6 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:231 §202 p.212 

Clauses: zh=0, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §202 When it sets at dusk in the west, it is 15 du and a bit in advance of the sun. |  |

### cullen:chunk:232 §203 p.212 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 見三百四十日 / 行六度 | 86 + 33 + 102 + 33 + 86 = 340 6 − 6 + 6 = 6 | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 除伏逆 | §203 Discarding invisibility and retrogradation, it is visible for 340 days, and moves 6 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:233 §204 p.212 

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 69 | many_to_one | 伏復 / 十九日千八十一分半 / 行三度萬四千七百二十五分半 / 與日合 | §204 It returns to invisibility, and in 19 days and 1081½ parts it moves 3 du 14,725½ parts, and has conjunction with the sun. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:234 §205 p.212 

Clauses: zh=4, en=5, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | one_to_many | 通率日行九千四百一十五分之三百一十九 | 3 du + 14,725½ parts + 6 du + 3 du + 14,725½ parts = 12 du 29,451 parts, as in text Now Saturn Day and Du Factor is 36,384, so 378 days and 2163 parts = 13,755,315 day parts 12 du and 29,451 parts = 466,059 du parts Thus Day Rate is 466,059/13,755,315 du/day = 319/9415 du/day, precisely as in text. / 金， Metal [Venus] | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 54 | one_to_one | 凡一終 | §205 For one termination of a cycle, in 378 days and 2163 parts, it moves rela - tive to the stars 12 du and 29,451 parts. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | one_to_one | 三百七十八日有二千一百六十三分 | The overall rate is that in a day it moves 319/9415 parts. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 51 | one_to_one | 行星十二度與二萬九千四百五 十一分 | 19 days and 1081½ parts + 340 days + 19 days and 1081½ parts = 378 days and 2163 parts, as in text. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |

### cullen:chunk:235 §206 p.212 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 65 | many_to_one | 晨伏 / 五日 / 退四度 | §206 It becomes invisible at dawn, and in 5 days it retreats 4 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:236 §207 p.212-213 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後九度 / 而見東方 | §207 When it becomes visible in the east, it is 9 du behind the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:237 §208 p.213 

Clauses: zh=4, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 72 | many_to_one | 見逆 / 日行五分度之三 | §208 On visibility it moves retrograde, and in a day it moves 3/5 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | high | 72 | many_to_one | 十日 / 退六度 | In 10 days it retreats 6 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |

### cullen:chunk:238 §209 p.213 

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 八日 | §209 It delays and does not move for 8 days. | sequential_baseline_alignment, number_exact_match |

Commentary, not aligned:
- As in Triple Concordance.

### cullen:chunk:239 §210 p.213 

Clauses: zh=4, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 73 | one_to_one | 日行(行)四十六分度之三十三 | In 46 days it moves 33 du, and speeds up. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | [旋]順 | §210 It turns and moves direct, travelling 33/46 du in a day. | sequential_baseline_alignment, order_proximity |
| aligned | low | 42 | many_to_one | 四十六日行三十三度 / 而[疾] | As in Triple Concordance. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:241 §211 p.213 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 一度九十[一]分度之十五 / 九十一日行百六度 | §211 In a day it moves 1 du 15/91 du, travelling 106 du in 91 days. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:242 §212 p.213 

Clauses: zh=3, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | one_to_one | 九十一日行百一十三度 | As before, the denominator for parts is obviously 91, since 91 + 22 = 113. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 54 | one_to_one | 日行一度二十二分 | In 91 days it moves 113 du. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 益疾 | §212 It speeds up further , moving 1 du 22 parts in a day. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:243 §213 p.213 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後九度 / 而晨伏東方 | §213 When it becomes invisible in the east at dawn, it is 9 du behind the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:244 §214 p.213-214 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 一見二百四十六日 / 行二百四十六度 | (10 + 8 + 46 + 91 + 91) days = 246 days (−6 + 33 + 106 + 113) du = 246 du | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 46 | one_to_one | 除伏逆 | §214 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:245 §215 p.214 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 伏四十一日二百八十一分 / 行五十度二百八十一分 / 而與日合 | §215 It is invisible for 41 days and 281 parts, and moves 50 du and 281 parts, then it has conjunction with the sun. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:246 §216 p.214 

Clauses: zh=2, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | one_to_one | 一合二百九十二日[二]百八十一分 | §216 One conjunction is 292 days 281 parts, and the motion relative to the stars is like to it. | sequential_baseline_alignment, order_proximity, number_exact_match |
| aligned | low | 41 | one_to_many | 行星如之 | 5 days + 246 days + 41 days and 281 parts = 292 days 281 parts. / −4 du + 246 du + 50 du and 281 parts = 292 days 281 parts. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:247 §217 p.214 

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 69 | many_to_one | 金 / 夕伏 / 四十一日二百八十一分 / 行五十度二百八十一分 | §217 V enus becomes invisible at dusk, and in 41 days 281 parts, it moves 50 du and 281 parts. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:248 §218 p.214 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日前九度 / 而見西方 | §218 It becomes visible in the west, 9 du in advance of the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:249 §219 p.214 

Clauses: zh=5, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 78 | many_to_one | 疾 / 日行一度九十一分度之二十二 | It speeds up, moving 1 du 22/91, and in 91 days it moves 113 du. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 見順 | §219 On visibil ity, it moves direct. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 九十一日行百一十三度 / 微遟 | It slows down slightly. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:250 §220 p.214 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 日行一度十五分 / 九十一日行百六度 / 而(進)[遟] | §220 In a day it moves 1 du and 15 fen, and in 91 days it moves 106 du, and slows down. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:251 §221 p.214-215 

Clauses: zh=2, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 日行四十六分度之三十三 / 四十六日行三十三度 | §221 In a day it moves 33/46 du, and in 46 days it moves 33 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

Commentary, not aligned:
- As in Triple Concordance.

### cullen:chunk:252 §222 p.215 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 八日 | §222 It delays and does not move for 8 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:253 §223 p.215 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 旋逆 / 日行五分度之三 / 十日退六度 | §223 It turns retrograde, and in a day it moves 3/5 du, so that in 10 days it retreats 6 du. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:254 §224 p.215 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日前九度 / 而夕伏西方 | §224 It disappears at dusk in the west, when it is 9 du in advance of the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:255 §225 p.215 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 60 | many_to_one | 除伏逆 / 一見二百四十六日 / 行二百四十六度 | §225 Casting out invisibility and retrogradation, one Appearance is 246 days, and it moves 246 du. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:256 §226 p.215 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 伏五日 / 退四度而(後)[復]合 | §226 It is invisible for 5 days, and it has conjunction after retreating 4 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:257 §227 p.215 

Clauses: zh=4, en=4, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 54 | one_to_one | 凡(三)[再]合一終 | §227 When repeated conjunction is terminated once, that is 584 days and 562 parts, and the motion relative to the stars is the same. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 54 | one_to_one | 五百八十四日有五百六十二分 | The overall rate is that it moves 1 du in a day. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 行星如之 | 5 days + 246 days + 41 days 281 parts + 41 days 281 parts + 5 days = 584 days and 562 parts. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 通率日行一度 | 水， Water [Mercury] | sequential_baseline_alignment, order_proximity |

### cullen:chunk:258 §228 p.215-216 

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 65 | many_to_one | 晨伏 / 九日 / 退七度 | §228 It becomes invisible at dawn, and in 9 days it retreats 7 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:259 §229 p.216 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後十六度 / 而見東方 | §229 It becomes visible in the east when it is 16 du behind the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:260 §230 p.216 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 見逆 / 一日退一度 | §230 On visibility it retrogrades, and in a day it retreats 1 du. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:261 §231 p.216 

Clauses: zh=3, en=1, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 60 | many_to_one | 留不行 / 二日 / 21 | §231 It delays and does not move for 2 days. | sequential_baseline_alignment, number_exact_match |

Commentary, not aligned:
- As in Triple Concordance.

### cullen:chunk:262 §232 p.216 

Clauses: zh=4, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 72 | many_to_one | 旋順 / 日行九分度之八 | §232 It turns and moves direct, moving 8/9 du in a day. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | high | 72 | many_to_one | 九日行八度 / 而疾 | In 9 days it moves 8 du, and speeds up. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |

### cullen:chunk:263 §233 p.216 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 71 | many_to_one | 日行一度四分度之一 / 二十日行二十五度 | §233 It moves 1¼ du in a day, and moves 25 du in 20 days. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:264 §234 p.216 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日後十六度 / 而晨伏東方 | §234 It become s invisible at dawn in the east when it is 16 du behind the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:265 §235 p.216 

Clauses: zh=4, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 50 | many_to_one | 除伏逆 / 一見 | §235 Casting out invisibility and retrogradation, one Appearance is 32 days, and it moves 32 du. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 67 | many_to_one | 三十二日 / 行三十二度 | (1 + 2 + 9 + 20) days = 32 days (−1 + 8 + 25) du = 32 du | sequential_baseline_alignment, order_proximity, number_exact_match |

### cullen:chunk:267 §236 p.217 

Clauses: zh=0, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §236 It is invisible for 16 days and 44,805 parts, and moves 32 du 44,805 parts, then has conjunction with the sun. |  |

### cullen:chunk:268 §237 p.217 

Clauses: zh=2, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | one_to_one | 一合五十七日有四萬四千八百五分 | §237 One conjunction is 57 days and 44,805 parts, and the motion relative to the stars is like it. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 行星如之 | 9 + 32 + 16 days and 44,805 parts = 57 days and 44,805 parts | sequential_baseline_alignment, order_proximity |

### cullen:chunk:269 §238 p.217 

Clauses: zh=4, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 69 | many_to_one | 水 / 夕伏 / 十六日四萬四千八百五分 / 行三十二度四萬四千八百五分 | §238 Mercury becomes invisible at dusk, for 16 days and 44,805 parts, and moves 32 du 44,805 parts. | sequential_baseline_alignment, number_exact_match, number_exact_match, number_exact_match |

### cullen:chunk:271 §239 p.217 

Clauses: zh=1, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 見西方 | §239 When it appears in the west, it is 16 du in advance of the sun. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:272 §240 p.217 

Clauses: zh=5, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 70 | many_to_one | 日行一度四分度之一 / 二十日行二十五度 / 而遟 | In 20 days it moves 25 du, then slows down. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | low | 43 | many_to_one | 見順 / 疾 | §240 It moves direct on visibility , speeding up, and in a day moves 1 du ¼. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:273 §241 p.217 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 66 | many_to_one | 日行九分度之八 / 九日行八度 | §241 In a day it moves 8/9 du, and in 9 days it moves 8 du. | sequential_baseline_alignment, number_exact_match, number_exact_match |

### cullen:chunk:274 §242 p.217 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 留不行 / 二日 | §242 It delays and does not move for 2 days. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:275 §243 p.217 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | [旋]逆 / 一日退一度 | §243 It turns retrograde, and in a day it retreats 1 du. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:276 §244 p.217-218 

Clauses: zh=2, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 61 | many_to_one | 在日前十六度 / 而夕伏西方 | §244 When it disappears at dusk in the west, it is 16 du in advance of the sun. | sequential_baseline_alignment, number_exact_match |

### cullen:chunk:277 §245 p.218 

Clauses: zh=3, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | many_to_one | 一見三十二日 / 行三十[二]度 | (20 + 9 + 2 + 1) days = 32 days (25 + 8 − 1) du = 32 du | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match, number_exact_match |
| aligned | low | 46 | one_to_one | 除伏逆 | §245 Casting out invisibility and retrogradation, one Appearance is 32 days, and it moves 32 du. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:278 §246 p.218 

Clauses: zh=6, en=1, commentary=5

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 62 | many_to_one | 伏九日 / 退七度而復合 / 凡再合一終 / 百一十五日有四萬一千九百七十八分 / 行星如之 / 通率日行一度 | §246 It is invisible for 9 days, and retreats 7 du then has conjunction once more. | sequential_baseline_alignment, number_exact_match, number_exact_match |

Commentary, not aligned:
- When repeated conjunction is terminated once, that is 115 days and 41,978 parts, and movement relative to the stars is like it.
- The overall rate is that it moves 1 du in a day.
- 9 days + 32 + 16 days and 44,805 parts + 16 days and 44,805 + 32 + 9 = 114 days and 16 days and 89,610 parts = 115 days and 41,978 parts, since the Mer - cury Day and Du Factor is 47,632.
- −7 − 1 + 8 + 25 + 32 du 44,805 parts + 32 du 44,805 + 25 + 8 − 1 − 7 = 115 du and 41,978 parts, as in the text, since the Mercury Day and Du Factor is 47,632.
- [Calculating planetary motion]

### cullen:chunk:279 §247 p.218-219 Proc. 3.47

Clauses: zh=5, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 步術 | §247 By the Du and Parts for the days of invisibility from the pacing method, add to the Du and Remainder for the day of conjunction of the planet, and count it off as before, to obtain solar du of the Appearance of the planet. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 以步法伏日度分 / (如)[加]星合日度餘 | In Proc. 3.41, we found where the planet would be when it was in conjunc - tion with the sun. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | many_to_one | 命之如前 / 得星見日度也 | We know how many du the planet moves between conjunc - tion and its appearance while remaining invisible – see for instance section | sequential_baseline_alignment, order_proximity |

### cullen:chunk:280 §169 p.218-219 Proc. 3.47

Clauses: zh=0, en=2, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §169 in the case of Jupiter. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | Thus we may calculate where the planet will be when first seen in the east at dawn. |  |

### cullen:chunk:281 §248 p.219 Proc. 3.47

Clauses: zh=4, en=1, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 76 | many_to_one | (術)[行]分母乘之 / 分(日)如[日]度法而一 / 分不盡如(法)半[法]以上 / 亦得一, | §248 Let the denominator for motion parts multiply it, and obtain one for each time the parts accords with the Day and Du Factor, and if the parts not exhausted accord with half the factor or greater, then accordingly obtain one. | sequential_baseline_alignment, numbers_present_without_exact_match, operation_multiply, operation_obtain, result_not_exhausted_or_not_fill |

Commentary, not aligned:
- The result of this rule is that we only calculate planetary positions to within 1 du.
- Thus 1.2 du counts as 1 du, and 1.7 du counts as 2 du.

### cullen:chunk:282 §249 p.219 Proc. 3.47

Clauses: zh=6, en=2, commentary=1

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 72 | many_to_one | 而日加所行分 / 滿其母得一度 / 逆順母不同 | §249 Then [each] day add the parts moved, obtaining one du as the denominator is filled. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match, operation_add, operation_fill_count |
| aligned | medium | 52 | many_to_one | 以當行之母乘故分 / 如故母 / 如一也 | If the denominators for retrograde and direct motion are not the same, by the denominator appropriate to the [type of] motion multiply the given parts, and as they accord with the given denominator, that counts as one. | sequential_baseline_alignment, order_proximity, operation_multiply |

Commentary, not aligned:
- This refers to the fact that the daily rate of motion in the planet may involve fractional amounts with different denominators in different phases.

### cullen:chunk:283 §250 p.219 Proc. 3.47

Clauses: zh=3, en=1, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 47 | many_to_one | 留者承前 / 逆則減之 / 伏不書度 | §250 For a station, uphold the previous [value], for retrogradation then subtract it, and for invisibility do not write down the du. | sequential_baseline_alignment, operation_subtract |

### cullen:chunk:284 §251 p.219 Proc. 3.47

Clauses: zh=4, en=3, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 經斗除如行母 | §251 When it goes through [the lodge] Dipper, corresponding to the motion denominator, take one in four. | sequential_baseline_alignment, order_proximity |
| aligned | low | 43 | one_to_one | 四分具一 | The parts have their increase and decrease, but what goes before and after are related. | sequential_baseline_alignment, order_proximity |
| aligned | low | 42 | many_to_one | 其分有損益 / 前後相放 | When the planet moves through the lodge Dipper, of width 21¼ du, we subtract the fraction and calculate accordingly, to find how far the planet has moved into the next lodge. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:285 §252 p.219-220 Proc. 3.48

Clauses: zh=3, en=2, commentary=2

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 58 | one_to_one | 其以赤道命度 | §252 Y ou are to count off the du along the Red Road. | sequential_baseline_alignment, order_proximity, operation_count_or_name |
| aligned | medium | 65 | many_to_one | 進加退減之 / 其步以黃道 | Add to this for advance and subtract for retardation, and the motion is [reckoned] according to the Yellow Road. | sequential_baseline_alignment, order_proximity, operation_add, operation_subtract |

Commentary, not aligned:
- The figures for the ‘advance and retardation’ referred to here are given later:
- see

### cullen:chunk:291 §253 p.224-225 Proc. 3.51

Clauses: zh=24, en=12, commentary=15

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 82 | many_to_one | 夜漏減(三)[之 / 二]百而一 | For the production of dusk and dawn [centred stars], multiply the du of Heaven by the day clepsydra, and subtract from it the night clepsydra, counting 1 for 200, to make the Determined Du. | sequential_baseline_alignment, order_proximity, number_exact_match, operation_subtract |
| aligned | high | 80 | many_to_one | 強三為少 / 少四為度 | When there are 3 qiang that is shao, and when there are four shao that is a du. | sequential_baseline_alignment, order_proximity, number_exact_match, definition_make_or_is |
| aligned | medium | 53 | many_to_one | 一刻 / 以相增損 | §253 For producing the distance of the Yellow Road from the pole, and the solar shadow, one relies on the [armillary] instrument and the gnomon. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 57 | many_to_one | 昏明之生 / 以天度乘晝漏 | For producing the clepsydra divisions, multiply the differences in distance from the pole by the differences for the Nodal qi, with a difference of 1 ke being counted as this accords with the varying distance, then let them be added and subtracted. | sequential_baseline_alignment, order_proximity, operation_multiply |
| aligned | medium | 67 | many_to_one | 為 定度 / 以減天度 | By that subtract from the du of Heaven, and the remainder is [the du of the] dawn [centred star]. | sequential_baseline_alignment, order_proximity, operation_subtract, definition_make_or_is |
| aligned | medium | 67 | many_to_one | 餘為明 / 加定度一為昏 | Add one to the Determined Du to make [the du of the] dusk [centred star]. | sequential_baseline_alignment, order_proximity, operation_add, definition_make_or_is |
| aligned | medium | 65 | many_to_one | 其餘四之 / 如法為少 | If there is a remainder, four-fold it; | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_remainder |
| aligned | medium | 55 | many_to_one | [二為半 / 三 為太 | if it accords with the factor once, that is shao ‘Lesser’, if twice, that is ban ‘Half’ , and if three times, that is tai ‘Greater’. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 55 | many_to_one | ]不盡 / 三之 | What is not exhausted, three-fold it; | sequential_baseline_alignment, order_proximity, result_not_exhausted_or_not_fill |
| aligned | medium | 65 | many_to_one | 如法為強 / 餘半法以上以成強 | if it accords with the factor that is qiang ‘Strengthened’ – let it make up qiang [even if] the remainder is [only] over half of the factor. | sequential_baseline_alignment, order_proximity, definition_make_or_is, result_remainder |
| aligned | medium | 55 | many_to_one | 其 強二為少弱也 / 又以日度餘為少強 | Two qiang make shao ruo . | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 57 | many_to_one | 而各加焉 / [一] | [So] you may alternatively make the remainder for the sun’s du into shao and qiang, and add them to it respectively. | sequential_baseline_alignment, order_proximity, operation_add |

Commentary, not aligned:
- In this section, we are told what observations and calculations were made in order to produce the data in the solar table that follows.
- The summary explanations given here may be supplemented by the details in (Cullen, Christopher 2007a).
- The first paragraph refers to the two main sources of actual observational data used for the table – an armillary instrument for measuring the sun’s north polar distance, and a gnomon for measuring the noon solar shadow.
- These are to be observed on the days corresponding to the 24 qi, the equally spaced divisions of the solar cycle from one winter solstice to the next;
- see Proc. 3.49.

### cullen:chunk:293 §254 p.227-228 Proc. 3.52

Clauses: zh=0, en=4, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | §254 Table of solar data, day and night lengths, and centred stars (see T able 3.11) Table 3.10 (Continued) Figure 3.1 Page from the 1739 edition of Hou Han shu, zhi 3, 21a–21b, showing part of a table of solar data Proc. 3.51 explains how the data in Table 3.11 were produced: |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | actual measurements of solar shadows and north polar distances of the sun were performed, and the other quantities were calculated from them as specified in the section referred to. |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | For further details, see (Cullen, Chris - topher 2007a: |  |
| unmatched_translation | unmatched | 0 | unmatched_translation |  | 88–90, and 93–94). |  |

### cullen:chunk:294 §255 p.228-231 Proc. 3.53

Clauses: zh=18, en=16, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 56 | one_to_one | 中星以日所在為正 | §255 Centred stars take the location of the Sun as the standard, and [their sequence] is accomplished as the sun moves through four years. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | one_to_one | 日行四歲乃終 | Set out the Lesser Remainders for the 24 qi for the year sought, and four-fold them, and as they accord with the factor make shao and tai. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 56 | one_to_one | 置所求年二十四氣小餘四之 | As for the remainder that is not exhausted, three-fold it, and as it accords with the factor make qiang and ruo, with which one subtracts from the dusk and dawn centred stars, and so each will be determined. | sequential_baseline_alignment, order_proximity, result_remainder |
| aligned | medium | 56 | one_to_one | 如法為少、大 | Qiang is upright; | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 55 | one_to_one | 如法為強、弱 | If one makes qiang go forward shao is made ruo; | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | medium | 54 | many_to_one | 從強進少為弱 / 從弱退少而強 | the rendering here follows Li Rui, who sees it as referring to the effect of adding qiang to qiang to make shao ruo, which is clear enough, since 2/12 = 1/4 – 1/12, and of subtracting qiang from shao ruo to make qiang, i.e. (1/4 – 1/12) – 1/12 = 1/12. | sequential_baseline_alignment, order_proximity, definition_make_or_is |
| aligned | low | 45 | one_to_one | 餘不盡 | ruo is inverted. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 三之 | When qiang and ruo are subtracted, if the name is the same it is taken off, but if the name is different it goes with it. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 以減節氣昏明中星 / 而各定矣 | if from the ruo one goes backwards, shao is made qiang. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 強 | The tabulated centred stars are those that apply if is assumed that the relevant qi falls at midnight, so that the midnight position of the sun is as tabulated. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 正 | In fact this is not generally the case. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 弱 | Since qi recur at intervals of 365¼ day, a qi that falls at midnight in year 1 will fall a quarter day after midnight in year 2, then half a day after midnight in year 3, then three-quarters of a day after midnight in year 4, until returning to midnight in year 5. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | (直)[負]也 | In any given year, the Lesser Remainder for that qi is the fraction of a day after midnight when the qi falls, at a scale of Medial [ Qi] factor [32]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 其強弱相減 | The procedure given here acts, in effect, to produce quarters according to the shao/ban/tai system, followed by the conversion of the remainder into ± 12ths according to the qiang/ruo system, as outlined in Proc. 3.51. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 同名相去 | Since the result is the shift in the midnight solar posi - tion, we may apply the same shift directly to the dusk and dawn centred stars positions. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 異名從之 | The final sentence is obscure: | sequential_baseline_alignment, order_proximity |

### cullen:chunk:295 §256 p.231-232 

Clauses: zh=4, en=1, commentary=12

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 59 | many_to_one | 從上元太歲在庚辰以來 / 盡熹平三年 / 歲在甲寅 / 積九千四百五十五歲也 | §256 From High Origin when the taisui was at gengchen.17, exhausting the 3rd year of the Xiping period [174–175 ce] when the year is at jiayin.51, the accumulation is 9455 years. | sequential_baseline_alignment, number_exact_match |

Commentary, not aligned:
- The reference to a date in the late second century makes it plain that the state - ment just translated cannot date from the time when the Han Quarter Remainder was promulgated in 85 ce.
- The year named is however precisely the year when Liu Hong is first said to have been officially consulted on an astronomical topic:
- see Chapter 5, § 73.
- It therefore seems likely that this text is part of the editorial contributions of Cai Yong and Liu Hong.
- 9455 = 157 × 60 + 35 and 35 + 17 = 52 Thus, as usual, the ‘accumulation’ which ‘exhausts’ a given year includes both the initial and final years of the interval specified.

### cullen:chunk:297 §257 p.232 

Clauses: zh=14, en=8, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | low | 46 | one_to_one | 易有太極 | §257 In the Book of Change there is the Supreme Ultimate, and this produced the Two Emblems [Yin and Yang]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 是生兩儀 / 兩儀之分尚矣 | So the distinction between the Two Emblems is from long ago. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 乃有皇犧 / 皇犧之有天下也 | Then there was Sovereign [Fu] Xi; | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 未有書計 / 歷載彌久 | when Sovereign Xi held all under Heaven, there was as yet no writing or reck - oning. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 暨於黃帝 | As the sequence of years went on and on, it came to Huang Di, who first made known written texts. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 班示文章 / 重黎記註 | Then Chongli [= Zhuanxu] made records and annotations, and set out names in correspondence to the phe - nomena, so that beginning and end were checked against one another, and by measured steps [sc. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 象應著名 / 始終相驗 | du] one could go back to the Origin. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 準度追元 / 乃立曆數 | Thereupon he set up the reckonings of the [astronomical] system. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:298 §258 p.232-233 

Clauses: zh=23, en=15, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 53 | many_to_one | 得五星會庚戌之歲 / 以為上元 | The Grand Inception system, which was not a Quarter Remainder system, had its origin in 104 bce, which was indeed a dingchou.14 year according to the reck- oning of years used from the Eastern Han onwards, and the Triple Concordance developed from it by Liu Xin had a High Origin in 143,231 bce, a gengxu.17 year by the same reckoning. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 天難諶斯 | §258 ‘Heaven is difficult to rely on’ 24 and therefore from the Five [emperors of High Antiquity] and the Three [dynasties Xia, Shang and Zhou] down to 24 This is a quotation from the Book of Odes, Shi jing 世經 , a collection of ancient poems, some of which may date from around 1000 bce. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 是以五、三迄于來今 / 各有改作 | The reference is to the fall of the last king of the Shang (or Yin) dynasty who was overthrown by the Zhou. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 不通用 | See Mao shi 毛詩 in the edition of Ruan Yuan 阮 the present, there were changes and innovations in each [period], and they did not follow a consistent practice. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 故黃帝造曆 / 元起辛卯 | Thus when the Yellow Emperor made his system, the Origin started from xinmao.28, but Zhuanxu used yimao.52, Yu [i.e. Emperor Shun 舜] used wuwu.55, Xia used bingchen.53, Yin used jiayin.51, Zhou used dingsi.54, and [the state of] Lu used gengzi.37. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 而顓頊用乙卯 | When Han arose it carried on from Qin, and at first used yimao.52. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 虞用戊午 / 夏用丙寅 | When it came to the Yuanfeng period of Wudi, it did not fit together with Heaven, and thus gentlemen who were able in reckoning made the Grand Inception system, which had its origin at dingchou.14. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 殷用甲寅 | At the interface with [the reign of] Wang Mang, Liu Xin made the Triple Concordance [system], which went back 31 Origins before the Taichu, to obtain a year in which the Five Planets were in conjunction at gengxu.17, and took that to be the High Origin. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 周用丁巳 / 魯用庚子 | The sexagenary numbers given are those of the years of system origin of the systems supposedly used by the ruler or state named. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 漢興 承秦 | We have no clear reference to any one these systems before the later part of the Western Han, and it may be that they are simply later reconstructions rather than ancient survivals. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 初用乙卯 / 至武帝元封 | Those for the Yellow Emperor, Zhuanxu (and hence early Han, as was thought), Yin , Zhou and the state of Lu are as found in other sources such as ( Qutan Xida 瞿 曇悉達 c. 725 ce: | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 不與天合 | chapter 105), but the year more commonly given for Xia is yichou.2. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 乃會術士作太初曆 / 元以丁丑 | I do not know of another early statement of the system origin ascribed to Emperor Shun. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 王莽 之際 | Whatever these systems may have been, there is general agree- ment that all of them were of the Quarter Remainder type. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 劉歆作三統 / 追太初前(世)[卅]一元 | Thus their use of different origins did not change the intervals between (say) successive winter solstices and luni-solar conjunctions, but only (in effect) introduced slight displacements in the timing of such events between one such system and another. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:299 §259 p.233-234 

Clauses: zh=18, en=9, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | high | 75 | many_to_one | 加六百五元 一紀 / 上得庚申 | 25 Adding on 605 Origins [4560 years] and 1 Era [1520 years], they reached up to gengshen.57 [in 276,0481 bce]. | sequential_baseline_alignment, order_proximity, number_exact_match, number_exact_match |
| aligned | medium | 53 | many_to_one | 追漢 (三)[四]十五年庚辰之歲 / 追朔一日 | Stockholm, Museum of Far Eastern Antiquities, 187–188. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | many_to_one | 乃與天合 / 以為四分曆元 | reckoning checked and compared all the systems, fixing the conjunctions and seeking the Origin, going back to the 45th year of Han, a gengchen.17 year, where they moved back the conjunction one day, whereupon it fitted in with Heaven, and they took that as the Origin for the Quarter Remainder system. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 44 | many_to_one | 太初曆到章帝元和 / 旋復疏闊 | §259 When the Grand Inception came down to the Yuanhe period of Zhangdi [84–86 ce], it in turn had become inaccurate. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 徵能術者課校諸曆 / 定朔稽元 | Those with subtle ability in 元 (1973 reprint of original of 1815), 16, 1b in vol. 2, 540, and Bernhard Karlgren (1950) The book of Odes. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 有近於緯 / 而歲不攝提 | This was near to the Wefts,26 but the year was not sheti [= one ending in yin 寅]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 以辨曆者得開其說 / 而其元尠與緯 同 | This gave an opening to those who disputed about systems. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | many_to_one | 同則或不得於天 / 然曆之興廢 | However, their Origins were scarcely in accord with the Wefts, and when they were in accord they did not succeed so far as the Heavens [were concerned]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | many_to_one | 以疏密課 / 固不主於元 | For the success or failure of an [astronomical] system depends on a check of its accuracy, and is certainly not ruled by the [choice of] Origin. | sequential_baseline_alignment, order_proximity |

### cullen:chunk:300 §260 p.234 

Clauses: zh=12, en=19, commentary=0

| status | conf | score | type | zh | en | features |
| --- | --- | ---: | --- | --- | --- | --- |
| aligned | medium | 52 | one_to_many | 述敘三光 | The Han Quarter Remainder system simply moved both winter solstice and conjunction back to the midnight beginning that day – not quite one day, but close enough. / At that moment the sun was about 50 minutes past winter solstice, so the correspondence was not bad. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | medium | 53 | one_to_many | 以備一家 | For a discussion of the background and contents of Cai and Liu’s documentary collection, see the Introduction to Chapter 5 of this book. / The document whose translation concludes at this point is the ‘second chapter’ referred to in the text. | sequential_baseline_alignment, order_proximity, numbers_present_without_exact_match |
| aligned | low | 46 | one_to_one | 光和元年中 | §260 In the first year of the Guanghe period [178 ce], the Gentleman for Consulta- tion Cai Yong, and the Palace Gentleman Liu Hong added to and continued the Monograph on the Pitchpipes and [Astronomical] System [from the Han shu]. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 議郎蔡邕、郎中劉洪補續律曆志 | Yong was able in setting out writings, and in the tuning of bells and pitchpipes, while Hong was able in calculations, and in giving an ordered account of the Three Luminaries. / Now I have examined and evaluated their work: | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 邕能著文 | its ideas are broad and general, and [the details of] numerical procedures are succinct and complete. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 清濁鍾律 | Therefore I have collected their notes into a first and second chapter, and have let them serve as a continuation of the Former Treatise, in order to show their point of view. / 27 25 The civil year that began in spring 161 bce was a gengchen.17 year, 45 years from the start of the Han dynasty. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 洪能為 筭 | According to the Triple Concordance System, the winter solstice of late 162 bce fell on December 25, a jiazi.1 day, at about 17:45 local Chang’an time, while the conjunction beginning the first Celestial month fell at 18:00. | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_many | 今考論其業 | An estimate of the mean conjunction suggests that it fell close to 15:00 on December 25, so the Triple Concordance made things worse rather than better in that regard. / However, what actually mattered was the accuracy of predictions around 85 ce, when the system was adopted, and this was much better. | sequential_baseline_alignment, order_proximity |
| aligned | low | 46 | one_to_one | 義指博通 | See Cullen (forthcoming), chapter 6. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 術數略舉 | 26 These are the apocryphal texts much studied in the Western Han: / they are frequently mentioned in Cai Yong and Liu Hong’s documentary collection: | sequential_baseline_alignment, order_proximity |
| aligned | low | 45 | one_to_one | 是以集錄為上下篇 | see Chapter 5. | sequential_baseline_alignment, order_proximity |
| aligned | low | 44 | one_to_many | 放續前 志 | 27 Literally ‘to [give] a complete school of thought’. / The word jia 家 ‘house, family’ is the usual word for an intellectual lineage and its doctrine. | sequential_baseline_alignment, order_proximity |

