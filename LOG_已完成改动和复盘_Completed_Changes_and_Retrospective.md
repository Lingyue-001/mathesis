# LOG 已完成改动和复盘 / Completed Changes and Retrospective

职责说明：
- 本文件只记录“已完成改动、问题原因、实施过程、复盘结论”。
- 每条记录按事件组织，结构固定为：需求明确 -> 操作 -> 解决 -> 复盘。
- 待办与优先级不写在这里；请查 `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`。

## [2026-06-17] Naming display rules and CSS component governance
0. Tags / Labels
   - project-docs, infra
1. Time
   - 2026-06-17
2. Goal
   - Establish semantic naming display rules for historical names, modern locations, calendar names, periods, and measurement units.
   - Establish the CSS governance direction: shared visual components first, page-specific styles only for genuinely page-specific behavior.
3. Actions
   - Added semantic text formatters: historical names use original-script slash romanization; calendar names use romanization followed by original script; modern locations use English only; periods use English labels with CE/BCE year ranges.
   - Updated map calendar labels, historical-place labels, modern-location labels, records list rendering, map detail cards, and visualization node labels to follow the naming rules.
   - Kept measurement units in structured data and rendered them automatically through the shared measurement formatter.
   - Recorded the CSS component split now in use: detail-panel for floating detail panels, entry-card for entry cards, with page-specific classes limited to behavior hooks such as position, drag, and resize.
4. Outcome
   - Display logic now distinguishes historical names from modern locations instead of mixing them in one line.
   - Calendar labels now follow the romanization-plus-original pattern; modern map locations render in English only; periods render with English dynasty labels and CE/BCE date ranges.
   - Node Details and map detail cards share the same detail-panel / entry-card component layer; map-specific CSS lives in src/css/map.css.
5. Retrospective
   - Naming display rules should follow the semantic type of the object, not a single generic bilingual ordering rule. New display logic should first identify whether the object is a historical name, modern location, calendar name, period, or measurement, then call the appropriate formatter.
   - CSS governance should move toward Design tokens -> base styles -> layout -> reusable components -> page-specific overrides. The practical path is gradual: split long CSS by section first, then extract variables.css, shared components, and page-specific files.
   - Future UI should reuse existing global components first. Only behavior such as map markers, Leaflet controls, transcription viewer splits, dragging, and resizing should stay in page-specific CSS or JS hooks.

## [2026-06-03] Brhat Netlify TEI 渲染容错修复
0. Tags / 标签
   - transcriptions, infra
1. Time
   - 2026-06-03
2. 需求明确 / Goal
   - 排查 Netlify 上 `src/transcriptions/tei_brhat/1r.html` 梵语转写区域显示 `Failed to render TEI`，但中文转写页面正常的问题。
   - 降低 Brhat 页面在生产环境中因增强逻辑失败而误判为 XML/TEI 主渲染失败的风险。
3. 操作 / Actions
   - 检查 Netlify、Eleventy passthrough、Brhat HTML/XML 资源链路与目录路由差异。
   - 将 Brhat 页 XML 加载改为基于 `new URL("../<file>", window.location.href)` 的明确 URL 解析。
   - 将 XML fetch/parse/TEI 正文渲染与后续增强逻辑分离为两段容错流程。
   - 对 Sanskrit node highlight、line preview、layout sync、script mode 等增强逻辑增加独立降级，避免增强失败时清空已渲染正文。
4. 解决 / Outcome
   - Brhat 页即使在线上增强逻辑失败，也应保留已成功渲染的 TEI 正文，只在 console 输出增强失败诊断。
   - `Failed to render TEI` 现在更接近真实 XML 加载或解析失败，不再覆盖后处理错误。
5. 复盘 / Retrospective
   - 转写页的主内容渲染和交互增强应分层容错；增强层失败不应破坏正文可读性。
   - 生产环境排障信息要避免误导，应让错误提示对应真实失败阶段。

## [2026-06-05] Brhat Netlify XML 路径修复
0. Tags / 标签
   - transcriptions, infra
1. Time
   - 2026-06-05
2. 需求明确 / Goal
   - 修复 Netlify 上 Brhat 转写页请求 `1r.xml` 时落到 `/transcriptions/1r.xml` 并返回 404，导致梵语 TEI 正文无法渲染的问题。
   - 保持 localhost 与 Netlify 在不同 URL 尾斜杠形态下的 XML 资源解析一致。
3. 操作 / Actions
   - 根据线上错误信息确认实际失败请求为 `/transcriptions/1r.xml`。
   - 将 Brhat 页 XML URL 从相对路径解析改为基于站点前缀拼接 `/transcriptions/tei_brhat/<fileName>`。
   - 保留 GitHub Pages 项目路径前缀兼容逻辑，避免未来带 `/mathesis` 前缀时再次错位。
4. 解决 / Outcome
   - `1r.xml` 加载路径固定为 Brhat 转写目录下的 XML 文件，不再受当前页面是否带尾斜杠影响。
   - Netlify 自动部署后应请求 `/transcriptions/tei_brhat/1r.xml`，而不是 `/transcriptions/1r.xml`。
5. 复盘 / Retrospective
   - 生产环境 URL canonicalization 与本地开发服务器不一定一致；转写资源不应依赖脆弱的 `../` 相对路径。
   - 页面内关键数据资源应优先使用 base-aware 的绝对站内路径，避免部署平台路由差异影响正文渲染。

## [2025-01-26] GitHub Pages 部署问题修复
### 需求明确
- 解决 GitHub Pages 上样式丢失、子页面 404、渲染不完整。
- 保持 Eleventy 项目结构不变，支持 GitHub Actions 自动部署。

### 操作
- 在 Eleventy 生产环境加入 `pathPrefix`。
- 模板与脚本路径改为 `| url` 或 base-aware 拼接。
- 修正 CSS 字体/静态资源相对路径。
- 增加必要资源的 passthrough。
- 将 Pages 发布方式改为 GitHub Actions，并对齐产物目录 `dist`。

### 解决
- 部署路径前缀错位导致的 CSS/JS 404 消失。
- 构建产物与 Pages Source 对齐，页面可正确渲染。

### 复盘
- 项目站点不是根域名时，路径前缀必须统一处理。
- 发布方式、构建目录、路由前缀三者必须同时对齐。

## [2026-01-30] 搜索/转写/可视化交互与本地构建修复
### 需求明确
- 统一 Search/Transcriptions/About 的视觉节奏。
- Visualization 增加交互并修复 CSV 解析错位造成的“乱码”。
- 暂时取消卡片跳转，保留可视化主体可用。

### 操作
- CSV 解析从简单 `split(",")` 改为支持引号内逗号。
- 分页数据改为 Eleventy 规范引用（`pagination.data = "cards"`）。
- `cards` 数据迁移到 `src/data/cards.js` 以匹配 `dir.data`。
- 针对重复 `cardURL` 增加回退逻辑，避免输出冲突。
- 优化 hover/缩放交互，移除不稳定 idle 漂浮。

### 解决
- 可视化字段错位修复，节点文案显示恢复。
- 本地构建错误（分页数据找不到、重复 permalink）排除。
- 页面交互从“突变”改为平滑反馈。

### 复盘
- Eleventy 分页必须用数据键名，不应直接传数组。
- CSV 若用于生产展示，必须按 RFC 场景处理引号和逗号。
- 视觉动效应优先保证阅读稳定性。

## [2026-02-08] Transcriptions 旧项目（汉书律历志）复刻接入
### 需求明确
- 从旧项目迁入 `XML + 对应 HTML + 手稿图片`。
- 本阶段不重写逻辑，优先复刻旧页面效果并验证链路可跑通。

### 操作
- 导入文件：
  - `src/transcriptions/tei_hanshu/lingyue.xml`
  - `src/transcriptions/tei_hanshu/lingyue.html`
  - `assets/tei_hanshu/lingyue.jpeg`
- 在 `.eleventy.js` 增加 `addPassthroughCopy("src/transcriptions/tei_hanshu")`，保证 HTML 可直出访问。
- 将 `lingyue.html` 的 `fetch("TEI/...")` 改为 `fetch("./...")`。
- 删除 `loadTEI(...)` 行尾 `#...` 非 JS 注释，避免脚本中断。
- 将 `lingyue.xml` 中 `<graphic url>` 改为 `../../assets/tei_hanshu/lingyue.jpeg`。
- `src/transcriptions/index.md` 增加入口，直接指向 `{{ '/transcriptions/tei_hanshu/lingyue.html' | url }}`。

### 解决
- 修复 `Cannot GET /transcriptions/tei_hanshu/lingyue.html`。
- 恢复 XML 加载与图片调用，页面可按旧格式渲染。

### 复盘
- “复刻阶段”优先处理路径兼容，再考虑组件化重构。
- 迁移旧前端时优先检查三类路径：HTML 内 fetch、XML 内图像 URL、入口链接前缀。

## [2026-02-08] 文档体系重构（Note/Log 职责分离与命名）
### 需求明确
- note 只保留当前状态与待办优先级。
- log 只保留已完成改动与复盘。
- 文件名改为中英双语，降低使用门槛。

### 操作
- 重命名与整合：
  - `PROJECT_BACKLOG.md` -> `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`
  - `CHANGELOG_2025-01-26.md` 与 `CHANGELOG_2026-01-30.md` 合并为 `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`
- 在 note/log 文件头新增职责声明。
- 更新 README 的引用路径。
- 新增 `AGENTS.md`，要求每次会话先阅读 note 与 log。

### 解决
- Note 与 Log 的语义边界明确，不再重复记录同类信息。
- 历史记录集中到单文件，按事件+时间可追溯。

### 复盘
- 文件名直接编码“用途 + 中英释义”，可显著降低认知成本。
- 一条事件一条记录能减少后期整理成本并提高检索效率。

## [2026-02-09] Lingyue 节点词命中原型（只高亮 + 统计）与纠偏
### 需求明确
- 在不改 TEI 渲染主结构的前提下，为 `lingyue` 页面加入“节点词命中高亮 + 日志统计”最小原型。
- 仅做命中可视化，不加超链接；先验证命中质量。

### 操作
- 仅在 `src/transcriptions/tei_hanshu/lingyue.html` 增量加入二次处理流程：
  - 渲染完成后加载 `src/data.json` 词条（`name/name_zh/name_zh_simple/name_en/name_sa/transliteration`）。
  - 对正文文本节点做命中高亮（跳过脚本/按钮/链接等区域）。
  - 输出统计日志（命中总数、命中词数、Top hits）并在页面显示简要命中摘要。
- 先后纠偏了三类规则：
  - **繁简混写漏匹配**：补入 `simp_to_trad_map.json` 参与词形变体生成，覆盖 `黄鐘` 这类混写场景。
  - **数字策略修正**：阿拉伯数字保持不匹配；将 `1-10` 的阿拉伯数字映射为汉字数字词（`一`到`十`）用于命中测试。
  - **标题排除**：大标题 `h1` 不参与匹配，避免视觉干扰。
- 高亮视觉从硬块样式改为更柔和的“下半段水彩笔”渐变，并调字色与 hover 反馈。

### 解决
- 页面可直接看到节点词命中（包括繁简混写词形），并可通过页面摘要与控制台复核命中情况。
- 解决了“黄钟只命中部分位置”与“汉字数字未命中”的两次核心问题。

### 复盘
- 原型阶段不能只依赖控制台，必须提供页面内可见反馈，否则容易误判“无变化”。
- 中文文本命中需要显式处理繁简/混写变体，否则局部漏匹配概率高。
- 数字语境是高风险区域，应先把“是否匹配阿拉伯数字、汉字数字如何放行”写成明确规则再扩展。

## [2026-02-09] Brhat 首次接入排障与转写页面统一规范
### 需求明确
- 新接入 `tei_brhat` 后页面出现 `Cannot GET /transcriptions/tei_brhat/1r.html`，需要定位并恢复访问。
- 在多文本并行接入时，确立文件组织和命名的一致性规则。
- 详细页 UI 要与站点全局样式一致，避免局部样式漂移。

### 操作
- 定位 404 根因链：
  - `.eleventy.js` 未将 `src/transcriptions/tei_brhat` 加入 passthrough。
  - `1r.html` 仍残留旧引用（加载 `lingyue.xml`）。
  - `1r.xml` 的 `<graphic url>` 仍指向 `assets/tei_hanshu/...`。
- 对应修复：
  - 增加 `addPassthroughCopy("src/transcriptions/tei_brhat")`。
  - `1r.html` 改为加载 `1r.xml`。
  - `1r.xml` 图片路径改为 `../../assets/tei_brhat/1r.jpg`。
- UI 统一修复：
  - 顶栏由局部 `legacy-*` 样式改为复用全局 `site-header/site-nav`。
  - 详细页返回交互收敛为常规 `Back` 按钮样式（无边框 + 轻微底部阴影）。

### 解决
- Brhat 页面恢复可访问、可加载 XML、可正确显示对应图片。
- 详细页顶栏与站点全局导航样式一致，减少跨页面视觉割裂。

### 复盘
- 新文本接入应先做“3项一致性检查”：
  - 目录是否在 Eleventy passthrough。
  - `html -> xml` 文件名是否一致。
  - `xml -> assets` 图片文件名/路径是否一致。
- XML 文件组按 text 分类、同一作品放在同组目录是可维护的；但必须保证 `XML-HTML-图片` 命名严格一致，否则很容易出现“能开页但内容错位/错图”的隐性故障。
- UI 层应坚持全局复用意识：对高复用、需一致的模块（header/nav/基础按钮）优先复用全局类和样式，避免局部复制导致后续维护分叉。

## [2026-02-09] CText 外部检索接入（单节点点击 + 右侧浮窗）与黄钟案例验证
### 需求明确
- 在 `lingyue` 详细转写页中，点击高亮节点词后触发外部检索，不跳转页面，在右侧浮窗返回结构化结果。
- 检索统一使用 CText 算书页面链接：`https://ctext.org/mathematics/zh?if=gb&searchu=<variant>`。
- 保证“单次只检索当前点击节点的全部变体”，并可通过 debug 追踪每个变体是否真实执行与解析成功。

### 操作
- 新增后端中间件 `server/ctextSearchMiddleware.js`，并在 `.eleventy.js` 注入开发服务器 middleware（兼容 `setServerOptions` / `setBrowserSyncConfig`）。
- 在 `src/transcriptions/tei_hanshu/lingyue.html` 中新增：
  - 高亮词点击后请求 `/api/ctext/search?q=...`；
  - 右侧浮窗展示结构化字段（检索范围/条件/符合次数/文本名/篇章名）；
  - debug 展示（attempts、source endpoint、query used、raw 提取线索）。
- 统一检索与手动 fallback 链接为 `?if=gb&searchu=`，并增加请求头（`Accept-Language`、`Referer`）提升返回模板一致性。
- 增加重试与诊断字段：
  - 单变体多次尝试（attempts）；
  - `parseStatus` 区分 `ok` / `ok_via_query_normalization` / `missing_result_header_after_retries` / `request_error`；
  - `markers` 与 `extracted` 用于判断是上游返回无结果块还是解析漏提取。
- 前端纠偏：
  - 修复 `hitCountDisplay is not defined`（冲突标记残留导致）；
  - 修复 `Number(null) === 0` 造成的“未解析误显示 0”；
  - 结果按 `符合次数` 降序显示，`0` 仅在真实数值时显示。

### 解决
- 黄钟节点（含 `黃鐘/钟` 场景）可稳定触发并返回结构化检索结果，作为当前可运行样本。
- 调试可见性显著增强：每个变体是否真正执行、是否解析成功、失败类别都可在前端 debug 明确观察。

### 复盘
- “同一 pipeline 下部分词成功、部分词失败”并不必然意味着流程分叉，常见根因是上游同端点返回模板不一致。
- 原型阶段必须把“请求是否成功”和“解析是否成功”拆分可视化，否则容易把解析空值误判为零命中。
- 对外部站点检索，先保证单一端点与可诊断状态，再做召回率优化；避免在排障期同时引入多端点策略导致因果混淆。

## [2026-02-09] CText 浏览器态采集（带会话）+ 缓存链路落地
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 将 CText 检索从单一脚本态请求升级为“浏览器态采集 + 本地缓存”，验证是否能提升高频词（如一/三/五）稳定性并降低重复请求。
3. 操作 / Actions
   - 在 `server/ctextSearchMiddleware.js` 新增浏览器抓取通道：
     - 默认 `CTEXT_FETCH_MODE=browser`，使用 Playwright 持久化会话目录 `tmp/ctext_session` 抓取页面；
     - 浏览器抓取异常时自动回退到原有 HTTP 抓取，保证接口可用。
   - 新增查询级缓存：
     - 缓存目录 `tmp/ctext_cache`；
     - 默认 TTL 6 小时（可由 `CTEXT_CACHE_TTL_MS` 覆盖；后续基线已调整为 24 小时）；
     - 支持 `refresh=1` 强制绕过缓存。
   - 新增“登录门槛/风控页”识别：
     - 通过“请登录显示此页/严禁自动下载”标记识别上游 gating 页；
     - `parseStatus` 新增 `upstream_login_required_or_rate_limited`，便于在 debug 面板中直接区分“解析失败”与“上游拒绝”。
   - README 增补了 CText middleware 运行说明、环境变量和 Playwright 依赖安装说明。
4. 解决 / Outcome
   - 后端具备浏览器态采集能力并保持 HTTP 回退；
   - 接口具备缓存与强制刷新能力，减少重复抓取；
   - 可在 debug 数据中明确识别“上游要求登录/限流”状态，避免继续误判为纯解析问题。
5. 复盘 / Retrospective
   - 仅更换解析正则无法解决“脚本态被上游拦截”的根因，需要抓取层能力升级。
   - 浏览器态 + 持久会话 + 缓存是更稳妥的基线；后续是否完全稳定仍取决于上游策略与会话有效性。

## [2026-02-09] CText 全局节流与并发上限收敛
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 进一步降低触发上游风控概率：新增全局请求节流，并将对 CText 的抓取并发限制为 1。
3. 操作 / Actions
   - 在 `server/ctextSearchMiddleware.js` 增加全局串行队列 `runWithGlobalThrottle(...)`：
     - 所有外发抓取请求统一进入同一队列；
     - 任何时刻只允许一个请求执行（并发上限=1）。
   - 增加全局最小间隔配置 `CTEXT_GLOBAL_GAP_MS`（默认 `1200ms`），在相邻抓取间等待，避免短时突发请求。
   - 将抓取入口改为经节流器执行：`runWithGlobalThrottle(() => fetchTextByMode(searchUrl))`。
   - README 补充节流配置说明。
4. 解决 / Outcome
   - 后端对上游的访问模式从“可能并发”收敛为“串行 + 限速”，进一步减少短时请求峰值。
5. 复盘 / Retrospective
   - 缓存降低了重复请求成本，串行节流进一步降低了单位时间压力；两者组合比单独启用任何一个都更稳妥。

## [2026-02-09] CText 检索长期卡点复盘（为何此前反复失败、最终如何稳定）
0. Tags / 标签
   - ctext, search
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 解释“同一检索逻辑下为何黄钟常成功而一/三/五常失败”的根因，并沉淀可复用的技术结论与实践边界。
3. 操作 / Actions
   - 先做证据对照而非继续猜测正则：
     - 对同一关键词分别抓取脚本态 HTML 与浏览器访问结果，定位是否同模板返回；
     - 在 debug 中核对 `firstLines/scopeLine/conditionLine/parseStatus`，识别“壳页”与“结果页”差异。
   - 确认问题后修正“代码层 + 思路层”两类错误：
     - 代码层此前问题：
       - 解析器过度依赖固定字段（如 `条件\\d+`），把模板差异误当“无结果”；
       - 缺少“登录门槛/风控页”显式识别，导致失败类型混淆；
       - 无缓存、无全局节流，重复点击会放大上游拦截概率。
     - 思路层此前问题：
       - 误以为“URL固定 = 返回必同模板”，忽略了上游按词频/会话/请求特征分流；
       - 误以为“批量离线抓取自然更稳”，但若仍是脚本态同样会批量抓到门槛页。
   - 最终改造链路：
     - 抓取：默认切换为浏览器态（Playwright 持久化会话），失败再回退 HTTP；
     - 诊断：新增 `upstream_login_required_or_rate_limited`，明确区分“解析漏提取”与“上游拒绝”；
     - 稳定性：引入查询缓存（TTL）+ 强制刷新参数；
     - 风控：引入全局串行队列（并发=1）+ 最小请求间隔。
4. 解决 / Outcome
   - 节点检索从“部分词条长期失败且难解释”转为“大多数词条可返回，异常词条可诊断归因”；
   - 交互层避免了重复抓取，明显减少了无效外部请求；
   - 文档层明确了运行参数、缓存策略和风险控制边界。
5. 复盘 / Retrospective
   - 根因不是单一正则 bug，而是“上游模板分流 + 本地抓取策略不匹配”的系统性问题。
   - 外部检索接入应优先建设三件事：可观测状态、失败分类、请求治理（缓存/节流/并发控制）。
   - 后续优化不应继续堆 parser patch，优先转向对方官方 JSON API 或授权接口，减少 HTML 模板耦合与策略波动风险。
   - 后续回应（2026-03-04）：已在 `1a` 页面落地 JSON API 试点（`searchtexts`）并保留 middleware fallback，验证了“静态托管可用 + 本地链路可对照”的过渡路线。

## [2026-02-09] CText 结果展示收敛（移除候选链接，文本名聚合全部章节）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 精简结果面板：移除“候选链接”与单独“篇章名”行；将结果改为“文本名 + 其下全部篇章链接”的聚合格式。
3. 操作 / Actions
   - 后端新增 `parseTextGroups(rawHtml)`：
     - 从结果页 `width=100%` 的标题表格中提取所有 `《...》` 标题与链接；
     - 使用“右侧包含 `提到《xx》的書籍`”识别文本层条目；
     - 将后续标题归并为当前文本的章节列表（去重，保留链接）。
   - 在 `structured` 中新增 `textGroups`，用于前端直接渲染分组结构。
   - 前端 `lingyue.html` 渲染改为：
     - `文本名：《文本》-《篇章1》；《篇章2》...`；
     - 多文本时按行继续输出；
     - 删除候选链接整块与单独篇章名块。
4. 解决 / Outcome
   - 结果面板信息密度提高，避免候选链接噪音；
   - 用户可一眼看到“文本 -> 全部篇章”并直接点击对应链接跳转。
5. 复盘 / Retrospective
   - 结果展示应优先贴合决策动作（先看文本，再看篇章范围），而不是展示抓取过程中的中间链接集合。

## [2026-02-09] 文本名显示为“—”的回归修复（缓存结构版本不一致）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 修复“检索已成功但文本名显示为 `—`”的问题，并避免同类问题再次发生。
3. 操作 / Actions
   - 定位到根因是缓存结构版本不一致：
     - 新前端读取 `structured.textGroups`；
     - 旧缓存仅有 `structured.text/chapter`，导致命中旧缓存时被渲染为空。
   - 在后端缓存中引入 `schemaVersion` 并写入缓存 key：
     - 读取时若版本不匹配直接失效；
     - 写入时带 `schemaVersion`，避免后续结构升级产生静默回归。
   - 前端增加兼容 fallback：
     - 当 `textGroups` 缺失时，从 `text/chapter` 回退构造最小分组，避免空白展示。
4. 解决 / Outcome
   - 旧缓存不再污染新展示结构；
   - 即使遇到异常缓存或部分数据，文本名仍可回退显示，不再直接变为 `—`。
5. 复盘 / Retrospective
   - 任何接口结构升级都应同步考虑缓存迁移策略，否则功能改动会被旧缓存“反向覆盖”。

## [2026-02-09] CText 文本提取修正（仅用 reqtype=stats + 输出章节次数）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 修复文本名误抓到页面导航文案（如“顯示原文/檢索範圍...”）的问题；文本与章节统一从统计页提取，并展示各自命中次数。
3. 操作 / Actions
   - 在 `server/ctextSearchMiddleware.js` 新增统计页专用解析：
     - 主查询页仍用于提取“检索范围/条件/符合次数”；
     - 每个变体额外请求 `&reqtype=stats` 页面；
     - 从统计表按“缩进层级”区分文本与章节，并抽取次数列及其链接。
   - `structured.textGroups` 改为仅使用统计页结果，避免混入普通结果页的无关链接。
   - 前端 `src/transcriptions/tei_hanshu/lingyue.html` 改为：
     - 不再回退 `structured.text/chapter`；
     - 文本名和章节名后展示次数；
     - 次数若有链接则可点击。
   - 缓存版本升级（`schema=5`）以淘汰旧结构缓存。
4. 解决 / Outcome
   - 文本名/章节名来源收敛到统计页表格，错误标题显著减少。
   - 可直接查看文本/章节对应次数并点击跳转。
5. 复盘 / Retrospective
   - CText 普通检索页结构噪音较多；稳定字段应以统计页表格为主数据源，普通页仅做检索元信息读取。

## [2026-02-09] CText 结果面板排版与链接微调
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 优化“匹配很多时”的可读性；将符合次数数字链接到原始检索页；去除检索范围后无关标点。
3. 操作 / Actions
   - 前端 `src/transcriptions/tei_hanshu/lingyue.html`：
     - 文本名区域改为“标签列 + 内容列”布局，内容换行后保持与冒号后首行对齐。
     - “符合次数”数字改为链接到该变体 `searchu=` 的完整检索结果页。
     - 移除“检索范围”与“检索类型”之间的圆点分隔。
   - 后端 `server/ctextSearchMiddleware.js`：
     - 收紧 `stripTrailingPunctuation(...)`，进一步清理 scope/condition 尾部噪声标点。
4. 解决 / Outcome
   - 长文本/章节行在换行后保持统一缩进，阅读更稳定。
   - 用户可直接点击符合次数跳到对应完整结果页复核。
   - 检索范围展示更干净，不再携带尾部无关符号。
5. 复盘 / Retrospective
   - 信息密度高的结果块应优先做“结构化对齐 + 快速复核入口”，比单纯缩小字体更有效。

## [2026-02-09] CText 查询归一与展示细化（同节点复用 + 24h 缓存）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 保证“文本名：”首行不折行；检索范围只保留冒号后第一段中文；同一节点不同位置点击复用同一查询结果；缓存改为 24 小时。
3. 操作 / Actions
   - 前端 `src/transcriptions/tei_hanshu/lingyue.html`：
     - 文本名区域改为“首行前缀 + 后续行缩进”布局，确保 `文本名：` 与首个文本同一行。
     - 高亮命中写入 `data-query-key`，按繁简归一生成同一查询 key。
     - 增加前端内存缓存与 in-flight 去重：同一 `queryKey` 重复点击不重复发请求。
   - 后端 `server/ctextSearchMiddleware.js`：
     - 新增 `normalizeScopeValue(...)`，`scope` 只取第一段汉字（无汉字时回退首 token）。
     - 默认缓存 TTL 从 6 小时提升到 24 小时。
     - 缓存版本按后续结构与清洗规则持续升级（当前为 `schema=7`），避免旧缓存结构影响新规则。
4. 解决 / Outcome
   - 文本名首行展示更稳定，长列表换行不再把前缀挤到单独一行。
   - `scope` 不再混入“检索类型”等后续字段。
   - 同一节点在页面不同位置点击时复用同一请求结果，减少重复请求。
   - 后端缓存周期延长为 24 小时，降低重复抓取频率。
5. 复盘 / Retrospective
   - 在高频点击交互里，前端 query 归一与并发去重和后端缓存同样重要，二者应同时设计而不是单独依赖后端缓存。

## [2026-02-09] CText 面板命名与中英切换
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 将面板标题由“CText 算书检索”调整为“CText 检索”，并保留中英双语可切换展示。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 的 CText 面板头部新增语言切换按钮（`中文 / EN`）。
   - 面板标题改为：
     - 中文：`CText 检索`
     - 英文：`CText Search`
   - 结果卡片关键字段支持双语切换：
     - 检索范围 / Scope
     - 检索类型 / Request type
     - 条件1 / Condition 1
     - 符合次数 / Matched
   - 增加简易值翻译映射（如 `算書 -> Mathematics`，`段落 -> Paragraph`，`包含字詞"X" -> Contains text "X"`）。
4. 解决 / Outcome
   - 面板命名更中性，避免限定在“算书”语义。
   - 可在不刷新页面情况下切换中英文查看同一检索结果。
5. 复盘 / Retrospective
   - 外部数据源固定中文时，前端语义层翻译是低成本、可维护的过渡方案；后续可再评估是否直接接入英文端点。

## [2026-02-09] CText 方案状态更正（基于最新实现）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 对 log 中已被后续迭代替换的 CText 细节做统一更正，避免把过时做法当作当前基线。
3. 操作 / Actions
   - 统一当前基线说明：
     - 文本/章节与次数来源：`searchu=...&reqtype=stats` 统计页；
     - 检索范围/条件/符合次数来源：`searchu=...` 主结果页；
     - `scope` 仅保留第一段汉字；`condition` 清洗时保留引号，避免单边引号显示。
   - 展示层更正：
     - 已移除空白“检索内容 / Search details”标题行。
   - 缓存层更正：
     - 默认 TTL 为 24 小时；
     - 缓存 schema 采用递增策略，当前实现为 `schema=7`。
4. 解决 / Outcome
   - 文档与代码当前行为对齐，降低后续排障时的信息偏差。
5. 复盘 / Retrospective
   - 对高频迭代模块（如外部检索）应定期增加“状态更正”事件，而非只追加功能条目，避免历史叙述漂移。

## [2026-02-09] Brhat 正式转写 XML 渲染修复（1r）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 修复 `src/transcriptions/tei_brhat/1r.xml` 更新为正式转写后无法在 `1r.html` 中渲染的问题。
3. 操作 / Actions
   - 使用 `xmllint` 校验定位错误：
     - `Opening and ending tag mismatch: msItem ... and msContents`。
   - 在 `src/transcriptions/tei_brhat/1r.xml` 修复 `<msContents>` 下的重复嵌套 `msItem` 开标签，恢复正确标签配对。
   - 再次执行 `xmllint --noout src/transcriptions/tei_brhat/1r.xml` 验证通过。
4. 解决 / Outcome
   - `1r.xml` 从“解析失败（parsererror）”恢复为“可被前端 TEI 渲染器解析”状态。
5. 复盘 / Retrospective
   - 转写更新后应先做一次 XML well-formedness 校验（如 `xmllint --noout`），可在前端调试前快速排除结构性错误。

## [2026-02-09] Brhat 1r 手稿行式可视化（19 行 + 菱形留白）
1. Time
   - 2026-02-09
2. 需求明确 / Goal
   - 将 `1r` 正文可视化整理为严格 19 行手稿模式，并在中间 5 行形成 `2-6-10-6-2`（按拉丁字符宽）菱形空白。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 中新增行式控制：
     - `ab` 节点改为独立单行渲染（`tei-ab-line`），并记录行号；
     - `body` 增加手稿网格类（`tei-manuscript-grid`）。
   - 渲染后执行 `applyBrhatManuscriptLayout(...)`：
     - 以 19 行为基准，给中间 5 行注入中心留白宽度变量（`2-6-10-6-2ch`）。
   - 样式微调：
     - 降低字号并微调行距/字距以减少左右不齐；
     - 中央留白通过伪元素遮罩实现，形成稳定菱形视觉空白。
   - `gap reason=\"ornamental\"` 改为不输出 `+++`，避免干扰手稿空白形态。
4. 解决 / Outcome
   - `1r` 正文可按 19 行单行模式展示，并在中段形成可控的菱形留白。
5. 复盘 / Retrospective
   - 对“版式先于语义”的手稿可视化，先固定行式与留白骨架，再迭代字符级校对，能显著减少样式反复返工。

## [2026-02-10] Brhat/Hanshu 转写页浮窗与工具栏细节补丁
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 调整 Brhat 详细页中 `Transcription` 小标题与 `Script` 按钮的布局与间距，并把提示语移动到正文结束后、参考文献前。
   - 为 Hanshu 系列补丁 node 浮窗默认左侧显示，避免与 CText 右侧浮窗重叠。
   - 统一大浮窗（node / CText）出现动画：左侧面板从左侧滑入，右侧面板从右侧滑入。
3. 操作 / Actions
   - `src/transcriptions/tei_brhat/1r.html`
     - 将 `.transcription-tools` 改为同一行 `flex` 布局，按钮右对齐；
     - 调整小标题与按钮的间距参数（`gap`），并把小标题文本改为 `Transcription · {folio}`；
     - 新增 `placeLineInteractionHint(...)`，在 TEI 渲染后将 Tip 自动插入到 `.tei-bibl` 之前（若无 bibliography 则回退到 XML 链接前）。
   - `src/js/nodeEntryPopup.js`
     - node 浮窗动画改为与 CText 一致的横向滑入（`translateX` + `opacity`）；
     - 新增 `side-left / side-right` 入场方向类，左侧面板从左边进入、右侧面板从右边进入。
   - `src/transcriptions/tei_hanshu/lingyue.html`
     - Hanshu node 面板默认位置显式固定为左侧（`left: 14px`）；
     - CText 面板加入 `side-right / side-left` 动画方向类并统一移动端定位规则（当前默认右侧）。
4. 解决 / Outcome
   - Brhat 页面工具栏更紧凑清晰，`Script` 按钮已在右侧并与 `Transcription · 1r` 同行。
   - Tip 已从正文外移到正文结束后、参考文献分隔线附近。
   - Hanshu 系列 node 浮窗默认左侧，且 node/CText 两类浮窗动画方向统一。
5. 复盘 / Retrospective
   - 浮窗方向应与落位侧一致，否则入场动线和空间感会冲突。
   - 对“正文内部提示位”的需求，优先采用渲染后插入，比写死在容器外更稳健。

## [2026-02-10] Brhat folio 切换动线与章节范围标注优化
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 调整 Brhat folio 切换动画为“顶部背景与正文同步开始”，且正文中的 transcription 与 viewer 两块错峰入场。
   - 在不增加页面负担的前提下，给 `1r` 补充章节覆盖范围提示。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 的 `animateFolioSwitch(...)` 中：
     - 保留 hero 背景动画即时开始；
     - 将正文动画拆分为 `transcription-main` 与 `transcription-viewer` 两段，设置同一时长但不同 delay（0ms / 110ms）。
   - 在同文件新增 `folioChapterSpan` 轻量提示行（小字号次级文字），并在 `FOLIOS` 的 `1r` 元数据中增加章节范围字段，渲染时自动展示，其他 folio 自动隐藏。
4. 解决 / Outcome
   - 切换时视觉起点一致（hero 与正文同步），同时正文两块具备层次化进入节奏。
   - `1r` 页面可见简洁章节范围提示，避免把较长章节名直接堆进主标题造成拥挤。
5. 复盘 / Retrospective
   - “同步起步 + 局部错峰”比“整块延迟”更符合阅读节奏，也更利于用户建立版面稳定预期。
   - 章节信息优先放在副信息层而非主标题，可在保留学术语义的同时控制界面密度。

## [2026-02-10] Brhat 正文切换方向修正与弹窗进场动画补丁
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 使 Brhat 正文左右两块切换方向一致，且与顶部背景动画方向相反。
   - 修复 Hanshu/Brhat 弹窗“关闭有退场、首次打开无滑入”的体验不一致问题。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 将正文两块位移变量统一为 `contentStartX`，与 `heroStartX` 保持反向关系。
   - 在 `src/js/nodeEntryPopup.js` 增加 `openPanelWithEnterAnimation(...)`，通过 `requestAnimationFrame` 延后一帧加 `is-open`，确保 node 弹窗首次打开触发进场过渡。
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 增加 `openCtextPanelWithEnterAnimation(...)`，并在 loading/error/results 渲染时统一走该开场逻辑。
4. 解决 / Outcome
   - Brhat 切页时正文两块同向入场，且与 hero 方向相反。
   - Hanshu/Brhat 的大浮窗在首次打开时也能看到从边缘滑入动画，开关体验对称。
5. 复盘 / Retrospective
   - 对“创建后立即加 open 类”的面板，浏览器可能合并样式计算导致首次入场动画失效；延后一帧是稳定做法。
   - 视觉动线规则（主背景与内容反向、内容内部同向）应作为切页动画约束固定下来，避免后续迭代漂移。

## [2026-02-10] Hanshu 双弹窗不遮正文与单击/双击交互分流
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 让 Hanshu 的 node / CText 两侧弹窗优先占用页面左右留白区域，避免遮挡正文主栏。
   - 将交互分流为“单击看 node、双击查 CText”，并补一条简洁 Tip 放在 bibliography 前。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 增加侧栏宽度变量与桌面断点规则（`min-width: 1260px`）：
     - `--hanshu-side-panel-width` 根据视口与正文宽度动态计算；
     - `#hanshuNodePanel` 与 `.ctext-result-panel` 同步采用该宽度。
   - 调整 node 面板定位为左侧 `top: 88px`，与 CText 面板顶部基线统一。
   - 将 CText 触发事件从 `click` 改为 `dblclick`，并补 `stopPropagation`。
   - 在通用 `bindNodeHitPopup` 增加 `deferSingleClickMs`，Hanshu 设置为 `220ms`：
     - 单击延迟触发 node；
     - 若发生双击则取消待触发的单击，避免双弹窗同时弹出。
   - 新增 `lineInteractionHintHanshu`，并通过 `placeHanshuLineInteractionHint(...)` 在渲染后插入到 `.tei-bibl` 前（若无 bibliography 回退到 XML 链接前）。
4. 解决 / Outcome
   - 大屏下左右弹窗宽度收敛到页边空白区，不再压住正文阅读主栏。
   - 节点交互从“同击双弹窗”改为“单击 node / 双击 CText”分流。
   - Hanshu 页新增简要操作提示，位置与 Brhat 的提示策略一致。
5. 复盘 / Retrospective
   - 双动作手势（single vs double）若不做单击延迟与双击取消，会天然冲突；应在事件层显式建模。
   - 侧栏宽度应与正文版心绑定，而不是固定像素，否则在宽屏上容易侵入阅读区。

## [2026-02-10] Hanshu 中央点击收起弹窗与命中统计去冗余
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 在 Hanshu 页面增加“点击正文中央区域自动收起左右弹窗”。
   - 优化 Node highlight 信息展示，减少同一词形变体重复占位造成的冗余。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 新增 `bindHanshuCentralDismiss(...)`：
     - 仅对正文容器点击生效；
     - 排除高亮词、按钮、链接、summary/details、统计区交互；
     - 触发时同时收起 `hanshuNodePanel` 与 `ctextResultPanel`。
   - 将命中统计从“原词逐条”改为“按 `queryKey` 聚合”：
     - `highlightNodeTerms(...)` 新增 `groupedCounts`，输出 `matchedGroups` 与 `groupedTerms`；
     - `renderHitSummary(...)` 改为显示聚合组（主词形 + 少量变体摘要），并更新文案为 `hits / groups`。
   - 增补 `node-hit-variants` 样式，弱化变体信息层级。
4. 解决 / Outcome
   - 点击正文中央非交互区域可快速收起两侧弹窗。
   - Node highlight 列表不再把同一概念的繁简/异体拆成多条主项，信息密度更高、可读性更好。
5. 复盘 / Retrospective
   - 统计展示应优先按“可解释单元（概念组）”组织，再附带词形细节，能显著降低视觉噪音。
   - 弹窗关闭手势放在正文主栏是低学习成本方案，但需严格排除正文内交互元素以避免误触。

## [2026-02-10] Brhat/Hanshu 小标题字号统一与 Hanshu 繁简切换按钮
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 统一 Brhat 与 Hanshu 转写区域小标题（含 bibliography）字号，按 `Transcription · 1r` 的层级对齐。
   - 为 Hanshu 增加与 Brhat 类似的单按钮脚本切换机制（此处为繁体/简体切换）。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 与 `src/transcriptions/tei_hanshu/lingyue.html` 分别引入 `--transcription-mini-heading-size: 1.4rem`，并将：
     - `transcription-subtitle`
     - `tei-doc h2/h3`
     - `tei-bibl h2/h3`
     统一绑定到该变量（Brhat 额外含 `cudl-title`）。
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 新增 `transcription-tools` 区块与 `scriptToggleButtonHanshu`。
   - 新增 Hanshu 脚本切换链路：
     - 加载 `simp_to_trad_map.json` 并构建 `trad->simp` 映射；
     - 捕获正文文本节点；
     - `applyHanshuScriptMode(...)` 在繁体/简体之间切换，按钮文案同步更新。
4. 解决 / Outcome
   - 两组页面的转写小标题与 bibliography 标题字号统一到同一视觉层级。
   - Hanshu 页面可通过单按钮在 `Script: Traditional / Script: Simplified` 间切换。
5. 复盘 / Retrospective
   - 标题层级应通过变量集中管理，避免多页面并行迭代时出现字号漂移。
   - 文本脚本切换在不动数据层的前提下可通过“渲染后文本节点替换”快速实现，适合当前迭代阶段。

## [2026-02-10] Hanshu/Node 弹窗宽度自适应放宽与用户拖拽调宽
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 让两侧弹窗在大屏下按比例变宽，避免全屏时仍显过窄。
   - 支持用户直接拖动边缘手动调节弹窗宽度（左窗拖右边，右窗拖左边）。
3. 操作 / Actions
   - `src/transcriptions/tei_hanshu/lingyue.html`
     - 将 `--hanshu-side-panel-width` 调整为 `clamp(300px, 26vw, 620px)`；
     - 为 CText 面板增加 resize handle 样式与 `is-resizing` 状态；
     - 新增 `makeCtextPanelResizable(...)`，按面板左右侧方向计算宽度增减并限制最小/最大宽度。
   - `src/js/nodeEntryPopup.js`
     - 将 node 面板默认宽度改为 `clamp(300px, 26vw, 620px)`；
     - 增加 `node-entry-resize-handle` 与 `makePanelResizable(...)`；
     - 在 `ensurePopupPanel(...)` 中注入拖拽手柄并自动绑定缩放逻辑。
4. 解决 / Outcome
   - 两侧弹窗在宽屏环境下显著放宽，阅读舒适度提升。
   - 用户可在运行时通过边缘拖拽自定义弹窗宽度，满足个人偏好。
5. 复盘 / Retrospective
   - 固定像素宽度在大屏下体验容易失衡，`clamp(min, vw, max)` 更适合作为基础策略。
   - 面板交互应同时支持“定位（拖动）+ 尺寸（缩放）”，避免用户只能适配单一工作习惯。

## [2026-02-10] Hanshu 转写块收敛为“单转写 + Edited”并修正繁简切换作用域
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 把 Hanshu 正文从“三块（繁转写/简转写/Edited）”收敛为“两块（转写 + Edited）”。
   - `Script` 按钮仅切换第一块转写（默认繁体，点击切简体），Edited 保持不变。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 的 TEI `div` 渲染分支中：
     - 识别 `subtype="simplified"` 并直接跳过渲染；
     - 给 `subtype="diplomatic"` 标记 `tei-transcription-primary`；
     - 给 `subtype="critical"` 标记 `tei-edited-fixed`。
   - 将 `captureHanshuTranscriptionTextNodes(...)` 的采集范围改为优先 `.tei-transcription-primary`，确保 `Script` 切换只影响第一块转写。
   - 同步移除页面工具栏中的 `Transcription · Lingyue` 文案，只保留 `Script` 按钮。
4. 解决 / Outcome
   - 页面结构变为“Transcription + Edited”两块，默认不再并列展示繁简两版转写。
   - Script 切换行为与 Brhat 类似：默认繁体，点击切简体，再点切回繁体，且不改 Edited 块。
5. 复盘 / Retrospective
   - 当源 XML 同时提供多脚本版本时，若前端已有脚本切换能力，应避免直接双份渲染造成信息重复。

## [2026-02-10] Hanshu 命中面板视觉收敛与间距微调
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 去除命中面板中冗余提示文本，并避免“hits/groups”大徽标喧宾夺主。
   - 拉开正文与页面下方 Tip 间距，增强阅读节奏。
   - 增加汉书页图片与转写标题之间的间距。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html`：
     - 删除 `node-hit-head` 内的 `node-hit-guide` 提示行；
     - 移除 `node-hit-badge` 模块；
     - 将统计信息并入 `Grouped terms` 的 `summary`（`groups / hits`）。
   - 将 `.line-interaction-hint` 的上边距从 `0.42rem` 提升到 `1.15rem`。
   - 将 `.tei-graphic` 下边距增大（`margin` 调整为 `1.2em auto 2.05em`）。
4. 解决 / Outcome
   - 命中面板信息层级更克制，统计不再单独占据大块视觉焦点。
   - 正文到 Tip 的留白更自然，图片与后续标题间距更舒展。
5. 复盘 / Retrospective
   - 面板内统计信息优先内嵌到结构标题（summary）可减少冗余组件。
   - 通过小幅留白调整（margin）即可明显改善页面阅读节奏。

## [2026-02-10] Hanshu 小标题字号统一与工具栏左右对齐
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 将 Hanshu 页面小标题字号统一到 Brhat `Transcription` 标题同级。
   - 让 `Script` 按钮与 `Transcription` 标题同一行，按钮在右侧。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 中恢复 `transcription-subtitle` 样式，并将其字号绑定到 `--transcription-mini-heading-size`。
   - `transcription-tools` 布局由右对齐改为 `justify-content: space-between`。
   - 工具栏 DOM 恢复左侧 `Transcription` 标题、右侧 `Script` 按钮。
4. 解决 / Outcome
   - Hanshu 页面 `Transcription` 与正文内 `tei-doc h2/h3`、`tei-bibl h2/h3` 处于同一字号体系。
   - 标题与按钮形成稳定左右对齐的一行布局。
5. 复盘 / Retrospective
   - 统一字号建议继续通过变量驱动，避免局部样式单点漂移。

## [2026-02-10] Hanshu Script 按钮并入正文既有 Transcription 标题行
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 不在页面顶部新增独立 Transcription 行；将 Script 按钮放到正文中既有 `Transcription` 标题右侧。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 删除顶部 `transcription-tools` 标题行。
   - 新增 `placeHanshuScriptButton(...)`：TEI 渲染后定位 `.tei-transcription-primary > h2`，生成 `tei-head-with-script` 行并将按钮移入该行右侧。
   - 按钮初始为 `hidden`，仅在定位到正文标题后显示。
4. 解决 / Outcome
   - Script 按钮与正文已有 `Transcription` 标题同一行显示，不再出现额外重复标题。
5. 复盘 / Retrospective
   - 对 TEI 动态渲染页面，工具按钮更适合在渲染后挂载到语义标题附近，避免静态模板层重复信息。

## [2026-02-10] Hanshu 段落呼吸感优化与 Brhat 命中分组面板对齐
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 增加 Hanshu `Transcription` 与 `Edited Text` 两块之间的留白。
   - 将 Hanshu 的 `Matched terms` 分组统计逻辑应用到 Brhat，减少重复词形展示并保持代码清晰。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 增加 `.tei-transcription-primary { margin-bottom: 2rem; }`。
   - 在 `src/transcriptions/tei_brhat/1r.html`：
     - 扩展高亮统计：按分组键聚合命中与词形分布；
     - 新增 `renderSanskritHitSummary(...)` 输出 `Matched terms` 可折叠面板（`Grouped terms (top 30)` + `groups / hits`）；
     - 新增 `clearSanskritHitSummary(...)`，在占位 folio 时清理旧统计，避免跨 folio 残留。
   - 补充 Brhat 对应的 `node-hit-*` 面板样式，保持与 Hanshu 命中面板视觉行为一致。
4. 解决 / Outcome
   - Hanshu 两个正文块之间有了更明显的呼吸感。
   - Brhat 现在也使用分组命中展示，避免重复词形挤占列表，且交互与 Hanshu 保持一致。
5. 复盘 / Retrospective
   - 对多页面同类交互，优先复用“统计结构 + 展示模式”，再按页面做最小差异化样式调整，可避免后续维护分叉。

## [2026-02-10] Hanshu Script 切换改为直接调用 XML 的 simplified 段
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 取消前端自动繁简转换逻辑，改为直接使用 XML 中已人工校对的 `diplomatic`/`simplified` 两段内容切换。
   - 保持页面结构为“两块”：转写 + Edited；Script 仅切换转写块。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html`：
     - `div` 渲染恢复保留 `subtype="simplified"`，并标记为 `.tei-transcription-simplified`；
     - `applyHanshuScriptMode(...)` 改为显示/隐藏 `.tei-transcription-primary` 与 `.tei-transcription-simplified`，不再替换字符；
     - 删除 `ensureHanshuScriptMaps / captureHanshuTranscriptionTextNodes` 等自动转换相关函数与状态；
     - 高亮统计增加 `[hidden]` 过滤，并在切换后重跑 `runNodeHighlightPrototype(...)`，保证只统计当前可见转写块。
4. 解决 / Outcome
   - Script 切换完全基于 XML 原始人工校对文本，避免自动转换误差。
   - 默认繁体显示，点击按钮切简体，再点切回繁体；Edited 块保持不变。
5. 复盘 / Retrospective
   - 当源文档已提供并校对多版本文本时，前端应优先做“版本切换”而非“内容再生成”，可显著降低语义偏差风险。

## [2026-02-10] Brhat Matched terms 主项改为节点名优先
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - Brhat 命中分组列表中，主项应先显示 node 名称（canonical），再显示文中变体，而不是直接把文中最高频词形放在第一位。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 新增 `extractSanskritStemDisplayMapFromNode(...)`，从节点字段构建 `stem -> display` 映射。
   - 在 `loadSanskritNodeLexiconMVP()` 中返回 `stemToDisplay`，并为手工词条补默认显示名。
   - 在分组统计阶段为每个组写入 `primary`（canonical 显示名）。
   - 在 `renderSanskritHitSummary(...)` 中改为优先渲染 `primary`，变体列表仅显示文中词形。
4. 解决 / Outcome
   - Brhat 的 `Matched terms` 列表现在先显示节点名，再显示文中命中变体，信息层级与使用预期一致。
5. 复盘 / Retrospective
   - 分组展示建议统一采用“canonical + attested forms”结构，可降低高频变体对主语义标签的干扰。

## [2026-02-10] Hanshu Script 切换稳定化与转写标题统一
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 修复 Hanshu 点击 `Script` 后按钮消失、标题变化的问题。
   - 转写区只显示统一标题 `Transcription`，不使用 XML 中 `diplomatic/simplified` 各自标题文本，仅渲染正文内容。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/lingyue.html` 调整 `placeHanshuScriptButton(...)`：
     - 不再把按钮挂到 `.tei-transcription-primary > h2` 内；
     - 改为创建独立工具栏 `.tei-head-with-script.hanshu-transcription-toolbar`，固定标题为 `Transcription`，按钮挂在右侧。
   - 在 TEI `div` 渲染逻辑中：
     - `subtype="diplomatic"` 与 `subtype="simplified"` 不再渲染 XML `head`；
     - 仅保留正文内容，`critical` 段仍保留其标题逻辑。
4. 解决 / Outcome
   - Hanshu `Script` 可持续来回切换，按钮不再因区块隐藏而消失。
   - 转写视觉标题固定为 `Transcription`，不再跟随 XML 各段标题变化。
5. 复盘 / Retrospective
   - 交互控件应挂载在独立稳定容器，避免被内容切换（`hidden`）连带隐藏。

## [2026-02-10] Brhat 背景导航箭头内缩与背景大标题统一
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 背景区左右导航箭头离页边保留更安全点击距离，避免过贴边缘影响操作。
   - Brhat 背景左侧大标题统一为 `Bṛhatsaṃhitā (MS Add.2329)`，不再显示分章/folio变化标题。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 的 `:root` 新增 `--folio-nav-inline-gap`。
   - `.folio-nav-prev/.folio-nav-next` 的 `left/right` 改为使用该变量，统一内缩。
   - 背景标题初始文本改为 `Bṛhatsaṃhitā (MS Add.2329)`。
   - `syncHeroTitleFromContent(...)` 改为固定写入统一标题，不再取正文 `h1` 文本作为 hero 标题。
4. 解决 / Outcome
   - 左右箭头离边更远，点击更稳定。
   - 所有 Brhat folio 切换时背景左侧大标题保持统一，不再出现 `Bṛhatsaṃhitā - upanayanādhyāyaḥ (1r)` 这类变化文本。
5. 复盘 / Retrospective
   - 视觉导航区的大标题宜保持稳定识别信息，章节细粒度信息可放在正文区更不干扰主导航。

## [2026-02-10] NOTE/LOG 文档同步：补充 CText 部署边界说明
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 检查近期更新在项目文档中的落点，补齐会影响部署预期的关键信息。
3. 操作 / Actions
   - 在 `NOTE_当前需求清单和待办_Current_Status_and_Todo.md` 的“当前状态”中新增一条：
     - 明确 `/api/ctext/search` 依赖本地 Eleventy dev middleware；
     - 说明 GitHub Pages 线上静态部署不提供该后端接口，线上以外链 fallback 为主。
4. 解决 / Outcome
   - 当前功能边界与线上行为预期被明确记录，降低“本地可用但线上不可用”造成的误判风险。
5. 复盘 / Retrospective
   - 涉及部署差异的能力（本地 middleware / 线上静态托管）应在 `NOTE` 持续可见，避免被实现细节淹没。

## [2026-02-10] Brhat 行图片预览联动：对应行常亮直到关闭/切换
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 打开某个行图片时，对应正文行应保持常亮；只有关闭预览或切换到其他行图片时才取消/转移高亮。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 新增 `activePreviewLineEl` 状态。
   - `showLinePreview(...)` 打开预览前先关闭旧预览，并给当前行添加 `is-line-preview-active`。
   - `closeLinePreview()` 统一移除 `is-line-preview-active` 并清理状态。
   - CSS 增加 `.tei-ab-line.is-line-preview-active` 与对应 `::after` 规则，使常亮视觉与 hover 高亮一致。
4. 解决 / Outcome
   - 行图片预览与正文行形成稳定一一对应的持久高亮反馈。
   - 切换行图片时高亮自动转移；关闭预览后高亮自动清除。
5. 复盘 / Retrospective
   - 这类“外部浮层对应正文上下文”的交互应使用显式状态类，而非仅依赖 hover/focus 临时态。

## [2026-02-10] Brhat 本地专用 Editor 模式（?edit=1）
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 为 Brhat 页面提供仅作者本人可用的快速编辑入口，支持在页面上直接改行文本用于迭代。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 增加 `Editor` 按钮（默认隐藏，URL 带 `?edit=1` 才显示）。
   - 新增编辑态逻辑：
     - 行文本 `.tei-ab-line-text` 可编辑（`contentEditable`）；
     - 编辑内容按 folio 键写入 `localStorage` 草稿；
     - 重新加载对应 folio 时自动回填草稿。
   - 编辑态下禁用 `Script` 切换并清理高亮面板，避免编辑与高亮/转写脚本互相覆盖。
4. 解决 / Outcome
   - 可在页面上快速试改转写内容并保存为本地草稿，适合个人迭代。
   - 该模式不改动 XML 源文件，符合当前数据安全边界。
5. 复盘 / Retrospective
   - 浏览器端编辑适合“草稿/试改”，正式入库仍应回写 XML 以保持可追溯与可协作。

## [2026-02-10] Brhat Editor 加固：限制为 localhost 可见
1. Time
   - 2026-02-10
2. 需求明确 / Goal
   - 避免线上用户通过 `?edit=1` 看到编辑入口，把 Editor 明确收口为本地个人工具。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_brhat/1r.html` 增加主机名判断：仅 `localhost/127.0.0.1/::1` 且 `?edit=1` 时 `BRHAT_EDITOR_UNLOCKED` 为真。
   - 在 `NOTE_当前需求清单和待办_Current_Status_and_Todo.md` 增加本地编辑器说明（入口、作用范围、数据边界）。
4. 解决 / Outcome
   - 线上部署环境不再暴露 Editor 入口；本地仍可用同一流程进行草稿编辑。
5. 复盘 / Retrospective
   - 纯前端“个人工具”功能应默认按环境收口，避免把调试能力误暴露到公开页面。

## [2026-03-03] 文档与转写入口同步（1a 替换 + 脚本可移植性 + Editor 草稿回填修正）
0. Tags / 标签
   - transcriptions, infra
1. Time
   - 2026-03-03
2. 需求明确 / Goal
   - 将汉书转写样本入口从 `lingyue` 同步到 `1a` 命名，保持入口与资产一致。
   - 修复简繁映射脚本的绝对路径问题，提升跨环境可执行性。
   - 修正 Brhat 编辑器草稿回填逻辑，避免非编辑模式误套用本地草稿。
3. 操作 / Actions
   - 更新转写入口与文件命名：
     - `src/transcriptions/index.md` 的链接改为 `src/transcriptions/tei_hanshu/1a.html`；
     - 汉书资源从 `lingyue.*` 对齐为 `1a.*`（HTML/XML/图片）并同步 NOTE 中的当前状态描述。
   - 重构 `generate_simp_trad_map.py`：
     - 新增 `--input/--output` 参数，默认使用项目相对路径；
     - 移除硬编码绝对路径，统一基于脚本目录解析输入输出。
   - 调整 `src/transcriptions/tei_brhat/1r.html`：
     - `applyEditorDraftToContainer` 增加 `force` 参数与编辑模式守卫；
     - 在编辑模式初始化时显式 `force: true` 回填草稿，非编辑模式不再误回填。
   - 在 `NOTE_当前需求清单和待办_Current_Status_and_Todo.md` 新增未完成项：
     - “改正错误后反思”的边界条件与 prompt 模板规范仍待补齐并固化。
4. 解决 / Outcome
   - 转写入口、文件命名与资产引用已对齐到 `1a`，减少入口错链和命名漂移。
   - 简繁映射脚本可直接在仓库内跨机器运行，不再依赖个人绝对路径。
   - Brhat 草稿回填行为与编辑模式边界一致，降低误覆盖阅读态内容的风险。
5. 复盘 / Retrospective
   - “可运行”之外还需保证“可迁移”：路径/命名/入口的一致性应与代码修复同优先级维护。
   - 流程反思若不把边界条件和 prompt 模板写成明确规范，容易在后续迭代中重复出现口径偏差；该项已在 NOTE 保持为进行中待办。

## [2026-03-04] CText 调试参数治理与协作边界固化
0. Tags / 标签
   - ctext, project-docs
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 将 CText 调试 URL 参数从分散写法收敛为统一配置与可查文档，降低维护门槛。
   - 固化协作注意事项：未经确认不写 NOTE/LOG；非功能型 UI 外观改动必须先沟通确认，不可静默落代码。
3. 操作 / Actions
   - 新增统一参数源 `src/js/debugFlags.mjs`，集中定义与解析：
     - `ctextDebug`、`ctextRefresh`、`ctextSource`。
   - 新增文档生成脚本 `scripts/generate-debug-flags-doc.mjs`，输出 `DEBUG_FLAGS_REFERENCE.md`。
   - 在 `package.json` 增加自动流程：
     - `generate:debug-flags-doc`；
     - `prestart`/`prebuild` 自动更新调试参数文档。
   - 在 `src/transcriptions/tei_hanshu/1a.html` 改为读取统一参数模块，不再散落解析 URL 参数。
   - 新增 `DEBUG_FLAGS_QUICKSTART.md`（小白快速指引），并在 `README.md` 增加“去哪看什么”的导航索引。
   - 在 `AGENTS.md` 增加两条协作边界规则：
     - 文档更新确认规则（NOTE/LOG）；
     - UI 变更确认规则（提议可先提，但非功能外观改动需先确认）。
4. 解决 / Outcome
   - CText 调试尾巴有了单一来源、自动文档与小白指引，后续新增参数可控且可追踪。
   - 协作边界从口头约定变为仓库内显式规则，减少“未确认先改/先记”的重复风险。
5. 复盘 / Retrospective
   - 参数与文档若分离维护，长期必然漂移；应以“配置为源、文档自动生成”为默认策略。
   - 对可见 UI 变化和文档落库时机，应先确认再执行；把规则写进 AGENTS 比依赖记忆更稳。

## [2026-03-04] CText JSON API 试点落地（静态托管可用 + 双源对照）
0. Tags / 标签
   - ctext, search
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 在不依赖本地 dev middleware 的前提下，让 CText 检索在 GitHub Pages 静态托管场景可运行。
   - 保留本地 middleware 路径作为对照与回退，降低迁移风险。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/1a.html` 增加 JSON API 调用链路：
     - 使用 `https://api.ctext.org/searchtexts` 获取检索结果；
     - 将返回的 `texts/paragraphs/urn` 映射到现有结果面板结构（`textGroups/hitCount`）。
   - 保留 middleware 路径并形成双源策略：
     - 本地默认 `middleware`，非本地默认 `json`；
     - 支持 `ctextSource=json|middleware` 强制切换。
   - 增加调试与排障参数统一入口（配合 `debugFlags`）：
     - `ctextDebug`、`ctextRefresh`、`ctextSource`。
4. 解决 / Outcome
   - CText 检索在静态部署场景具备可用路径，不再被“线上无本地后端接口”完全阻塞。
   - 本地与线上可在同一页面做双源对照，便于逐步验证迁移质量。
5. 复盘 / Retrospective
   - JSON API 解决的是“部署形态”问题（静态站可调用），不是一次性解决所有字段同构问题；展示口径仍需持续对齐。
   - 迁移期保留双源切换开关是必要缓冲层：既保证可用性，也保留可诊断性与回退能力。

## [2026-03-04] 日志体系精简与根目录收敛（Timeline + Tag）
0. Tags / 标签
   - infra, project-docs
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 将日志能力保留为“时间线主文件 + 按标签视图”最小方案，避免文档和目录层级继续膨胀。
   - 将常用说明文档收敛到根目录，提升入口可见性与记忆成本友好度。
3. 操作 / Actions
   - 标签体系收敛为 6 个：`ctext`, `transcriptions`, `search`, `data`, `infra`, `project-docs`。
   - 在 `AGENTS.md` 固化日志事件写法：新增 `0. Tags / 标签`，每条 1-2 tags。
   - 新增 `scripts/generate-log-by-tag.mjs`，从主 LOG 生成按标签视图。
   - 文档迁移到根目录并统一命名：
     - `DEBUG_FLAGS_REFERENCE.md`
     - `DEBUG_FLAGS_QUICKSTART.md`
     - `LOG_按标签视图_By_Tag.md`
   - 同步更新 `README.md`、生成脚本输出路径与相关引用。
4. 解决 / Outcome
   - 日志导航收敛为两视图：按时间（主 LOG）与按标签（自动生成），使用路径更直观。
   - 常用文档全部在根目录可见，降低“去哪个文件夹找文档”的摩擦。
5. 复盘 / Retrospective
   - 对当前项目阶段，命名清晰的根目录入口比额外目录分层更有实际价值。
   - 标签系统应先简后繁：先保证可执行与可维护，再按需要细分。

## [2026-03-04] 回滚全部 test ctext api 提交并重置基线
0. Tags / 标签
   - ctext, infra
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 线上 CText 仍失败，先回滚全部 `test ctext api` 相关变更，恢复到可控基线，避免继续叠加临时补丁。
3. 操作 / Actions
   - 回滚 `ddb906f`（proxy 前置条件 + fail-fast 试验）。
   - 回滚 `eb506c9`（Cloudflare proxy 接入试验）。
4. 解决 / Outcome
   - test API 试验代码已撤回，代码基线恢复为 test 系列之前状态。
5. 复盘 / Retrospective
   - 当验证链路依赖外部部署状态但不可观测时，应先回滚试验分支，避免把失败实验长期留在主干。

## [2026-03-04] 二次清基线：回滚 Netlify JSON 代理试验提交
0. Tags / 标签
   - ctext, infra
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 在切换到“Netlify 上运行 middleware 逻辑”前，先移除剩余 test API 试验改动，确保基线干净可控。
3. 操作 / Actions
   - 回滚 `48bbd16`（Netlify publish 目录修正，属 JSON 代理试验链路）。
   - 回滚 `4d82322`（Netlify JSON 代理方案及配套文档）。
4. 解决 / Outcome
   - test API 第二轮试验代码已全部撤回；仓库恢复到试验前可控状态。
5. 复盘 / Retrospective
   - 在连续实验失败后，应分阶段清理历史试验改动，再进入下一条技术路线，避免跨方案残留互相干扰。

## [2026-03-04] Netlify middleware 接入与本地独立代理联调闭环
0. Tags / 标签
   - ctext, infra
1. Time
   - 2026-03-04
2. 需求明确 / Goal
   - 让 CText 检索在 Netlify 部署形态可用，并保留本地可控会话代理用于稳定复现与排障。
3. 操作 / Actions
   - 新增 `netlify/functions/ctext-search.js`，复用 `server/ctextSearchMiddleware.js` 作为函数处理器。
   - 新增 `netlify.toml`，将 `/api/ctext/search` 重写到 `/.netlify/functions/ctext-search`。
   - 新增 `server/ctextProxyServer.js` 与 `npm run start:ctext-proxy`，提供带 CORS 的本地独立代理（含 `/healthz`）。
   - 更新 `src/js/debugFlags.mjs` 与 `src/transcriptions/tei_hanshu/1a.html`：
     - `ctextSource=auto` 改为 middleware 优先、JSON fallback；
     - 支持 `ctextProxyOrigin` 注入代理源；
     - 修复 `/1a/` 路由下资源与 XML/图像相对路径解析。
   - 调整 `.eleventy.js` 的 `pathPrefix` 逻辑：仅 GitHub Actions 构建启用 `/MATHesis/`，避免本地/Netlify 路径串扰。
4. 解决 / Outcome
   - 本地 `netlify dev` 与独立代理联调下，CText 变体检索可返回完整结果，`-` 占位问题已显著缓解。
   - `1a` 页面在 `/1a/` 路由下恢复正常渲染，手稿图与站点图标可正确加载。
5. 复盘 / Retrospective
   - 部署形态差异（GitHub Pages 静态 / Netlify 函数 / 本地长会话代理）必须显式拆层，不应混用单一默认路径。
   - 对外部检索链路，先保证“可观测 + 可切源 + 可回退”，再谈召回率优化，整体推进更稳。

## [2026-03-05] CText 前端代理注入兜底与转写路由规范化
0. Tags / 标签
   - ctext, transcriptions
1. Time
   - 2026-03-05
2. 需求明确 / Goal
   - 解决线上 `window.CTEXT_PROXY_ORIGIN` / `window.__CTEXT_PROXY_ORIGIN` 为 `undefined` 导致双击不发请求的问题。
   - 统一转写页入口路由，避免 `*.html` 与目录路由行为不一致。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/1a.html` 增加注入兜底：
     - 同时写入 `window.__CTEXT_PROXY_ORIGIN` 与 `window.CTEXT_PROXY_ORIGIN`；
     - `resolveCtextMiddlewareBase` 支持两种变量名读取。
   - 在 `1a.html` 增加入口规范化逻辑：
     - 若命中 `/transcriptions/tei_hanshu/1a.html`，自动重定向到 `/transcriptions/tei_hanshu/1a/`。
   - 在 `netlify.toml` 增加重定向：
     - `/transcriptions/tei_hanshu/1a.html` -> `/transcriptions/tei_hanshu/1a/`
     - `/transcriptions/tei_brhat/1r.html` -> `/transcriptions/tei_brhat/1r/`
   - 在 `src/transcriptions/index.md` 把入口链接改为目录路由（`/1a/`、`/1r/`）。
   - 更新 `NETLIFY_CTEXT_PROXY_SETUP.md`，明确验证时必须使用目录路由。
4. 解决 / Outcome
   - 前端代理地址读取链路对变量名与入口路径均具备兜底能力，降低“变量未注入”误判概率。
   - 转写页访问路径收敛为目录路由，减少模板注入与资源路径在不同入口下的偏差。
5. 复盘 / Retrospective
   - 对独立页面（非统一 layout）应优先保证“规范入口 + 路由重定向”，否则同一页面会出现多套运行上下文，排障成本高。
   - 环境变量注入问题需与路由一致性联合排查，不能只盯构建注入本身。

## [2026-03-05] Netlify 产物目录对齐修复（dist 输出强制化）
0. Tags / 标签
   - infra, ctext
1. Time
   - 2026-03-05
2. 需求明确 / Goal
   - 修复 Netlify 构建时偶发输出到 `_site` 导致 `publish=dist` 部署失败的问题。
3. 操作 / Actions
   - 在 `.eleventy.js` 中新增 `isNetlifyBuild` 判断；
   - 当 `NETLIFY=true` 或 `NODE_ENV=production` 时统一输出目录为 `dist`。
4. 解决 / Outcome
   - 本地模拟 `NETLIFY=true npm run build` 已稳定产出 `dist/`，与 Netlify `publish=dist` 一致。
5. 复盘 / Retrospective
   - 托管平台的发布目录与静态站生成目录必须硬性对齐，不能依赖隐式环境变量推断。

## [2026-03-05] CText JSON fallback 参数修正（避免整链路失败）
0. Tags / 标签
   - ctext, search
1. Time
   - 2026-03-05
2. 需求明确 / Goal
   - 修复 middleware 失败后 JSON fallback 仍报错的问题，确保线上至少有可用回退结果。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/1a.html` 中修正 JSON API 调用参数：
     - `searchtexts` 从错误参数改为 `title`；
     - `if` 改为合法值 `zh`，并补 `remap=gb`；
     - 移除无效参数 `json=1`。
   - 返回解析兼容 `data.texts` 与 `data.books` 两种结构。
4. 解决 / Outcome
   - middleware 失败时不再因 fallback 参数错误而整体报错，回退链路可正常返回可解析数据。
5. 复盘 / Retrospective
   - 迁移到官方 API 时必须逐项对齐参数与返回结构，否则“兜底链路”会变成新的失败点。

## [2026-03-05] CText 单字词上下文扩展检索（仿黄钟逻辑推广）
0. Tags / 标签
   - ctext, search
1. Time
   - 2026-03-05
2. 需求明确 / Goal
   - 降低单字词（如“五”）在线上检索中“全变体失败/返回空结构”的概率，把“黄钟可解析”的上下文思路推广到更多词。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/1a.html` 新增上下文扩展逻辑：
     - 对单字命中自动提取前后邻字，生成候选（前+字、字+后、前三字）；
     - 逐个候选发起检索，优先返回首个可解析结果。
   - 新增 `hasUsableSearchData(...)` 判定，避免把空壳响应误判为成功。
   - 在 debug 模式下记录 `queryFallbackFrom/queryFallbackUsed`，便于定位实际命中的候选词。
4. 解决 / Outcome
   - 单字词检索从“只查单字”升级为“单字+上下文候选”策略，提升可解析结果命中概率。
5. 复盘 / Retrospective
   - 对外部检索接口，词粒度过小会显著放大风控和噪声；结合局部上下文可在不改数据源的前提下提升可用性。

## [2026-03-05] 回退单字上下文拼词策略（消除噪声双词结果）
0. Tags / 标签
   - ctext, search
1. Time
   - 2026-03-05
2. 需求明确 / Goal
   - 取消单字自动拼接前后文候选词，避免返回“有结果但无语义价值”的双词噪声。
3. 操作 / Actions
   - 在 `src/transcriptions/tei_hanshu/1a.html` 删除：
     - 单字上下文候选构造函数；
     - 多候选逐次查询逻辑；
     - 由双击事件传入的上下文候选参数。
   - 保留既有主链路：middleware 优先、失败自动 JSON fallback。
4. 解决 / Outcome
   - 检索恢复为“按原词本身查询”，不再展示由邻字拼接得到的噪声组合词结果。
5. 复盘 / Retrospective
   - 当“召回提升”引入明显语义噪声时，应优先回退到稳定基线，再以可控词表策略逐步恢复召回。

## [2026-03-13] CText stats 解析回归修复与安全静态缓存导出链路
0. Tags / 标签
   - ctext, infra
1. Time
   - 2026-03-13
2. 需求明确 / Goal
   - 修复 `1a` 页面里 CText 文本名/章节名被错误标题覆盖或直接显示 `—` 的回归问题。
   - 在不破坏当前 localhost 检索与显示逻辑的前提下，把“本地正确结果”安全导出为可发布的静态缓存，供线上站点复用。
3. 操作 / Actions
   - 在 `server/ctextSearchMiddleware.js` 修正当前 live `reqtype=stats` 解析：
     - 放宽对 `searchu/reqtype` 链接的过滤，恢复合法 stats 行识别；
     - 兼容纯文本章节标签（如 `方田/粟米/卷上`）与右侧计数链接补 URL；
     - 将运行时缓存 schema 升级到 `8`，淘汰旧的空 `textGroups` 缓存。
   - 在 `src/transcriptions/tei_hanshu/1a.html` 移除错误 fallback：
     - 当 `textGroups` 缺失时，不再使用主结果页首个标题冒充文本名/章节名。
   - 新增当前 CText 统计表 fixture 与 parser test：
     - `tests/fixtures/ctext-stats/current-statstable.html`
     - `tests/ctext-stats-parser.test.mjs`
   - 新增 `scripts/build-ctext-cache.mjs` 与发布流程：
     - 默认从 localhost middleware 强制 `refresh=1` 抓取；
     - 默认全量重建，不合并现有正式缓存；
     - 先写 `candidate` 与 `report`，通过后再 `promote` 到 `static/ctext-cache.json`；
     - 对正命中但 `textGroups` 为空、gated、parse fail 的条目直接拒收。
   - 将构建 transport 从 Node `fetch` 切到默认 `curl`，避免 localhost 批量采集阶段出现整批 `fetch failed`。
   - 更新 `README.md`、`package.json`、`DEBUG_FLAGS_REFERENCE.md`，补齐静态缓存构建与当前 source 行为说明。
4. 解决 / Outcome
   - localhost 的 CText 检索已恢复按真实文本名/章节名显示，不再被 `《九章算術細草圖說》` 这类错误标题整体污染，也不再因旧缓存导致统一显示 `—`。
   - 已建立独立于运行时缓存的发布缓存流程，并成功从 `1a.xml` 映射词生成 9 条有效静态缓存，`failureCount=0`，静态缓存模式下与 localhost 动态结果一致。
5. 复盘 / Retrospective
   - 失败经验：
     - 不能把“parser 修复、前端 fallback、旧缓存复用”混在一起判断；这三层一旦同时带病，会制造看似随机、实则被缓存放大的假象。
     - 直接在正式 `ctext-cache.json` 上边抓边改风险很高；一旦中途失败或混入旧值，线上文件会立刻被污染，且难以回溯是哪一步写坏的。
     - 这次也验证了 localhost 批量采集里 Node `fetch` 并不比手动抓取更稳；对本机场景，`curl` 更接近人工验证路径，也更容易排障。
   - 方案收获：
     - 最稳的思路不是“继续补 fallback”，而是明确分层：localhost middleware 负责真实检索，发布缓存只做单向导出，不反向影响运行时判断。
     - 运行时缓存 `tmp/ctext_cache/` 与发布缓存 `static/ctext-cache.json` 必须分离，并且发布流程要坚持“candidate -> report -> promote”的原子替换模型。
     - 对外部检索做静态化时，质量门槛要前置到构建阶段；宁可拒收有疑点的条目，也不要让错误标题或空分组进入正式发布缓存。

## [2026-03-21] Windows 迁移基线固化与本地验证补齐
0. Tags / 标签
   - infra, project-docs
1. Time
   - 2026-03-21
2. 需求明确 / Goal
   - 在旧 Mac 仍可用时，把迁移到 Windows 后继续开发所需的环境锚点、变量模板与验证步骤固化到仓库里。
   - 确认当前代码是否存在写死的旧 Mac 绝对路径，并验证项目在 Node 20 基线下仍可测试与构建。
3. 操作 / Actions
   - 审计仓库中的构建配置、脚本与转写页面资源路径，确认当前运行路径主要基于相对仓库路径或相对网页路由，而非 `/Users/...` 这类机器绝对路径。
   - 新增环境与迁移文件：
     - `/.nvmrc` 固定 Node 主版本为 `20`；
     - `/.env.example` 汇总 `CTEXT_*`、`PORT`、`HOST` 等变量模板，并明确项目当前不会自动加载 `.env`；
     - `/requirements.txt` 固定 `generate_simp_trad_map.py` 依赖的 `opencc-python-reimplemented==0.1.7`；
     - `/迁移说明_Windows环境与验证.md`，集中记录迁移策略、不会随 Git 迁移的本地状态、Windows 安装步骤与验证清单。
   - 更新 `README.md`，增加环境与迁移入口说明。
   - 利用旧 Mac 上已安装但未自动进入当前 shell PATH 的 Node 20 路径，完成本地验证：
     - 运行 `scripts/generate-debug-flags-doc.mjs`；
     - 运行 `scripts/generate-log-by-tag.mjs`；
     - 运行 `node --test tests/ctext-stats-parser.test.mjs`；
     - 运行生产构建 `NODE_ENV=production eleventy`。
4. 解决 / Outcome
   - 仓库内已具备最小可复现的迁移基线说明，Windows 新机器可直接按 `git clone -> npm ci -> pip install -r requirements.txt -> verify` 路线启动。
   - 本轮未发现写死到旧 Mac 文件系统的运行路径；当前主要风险已明确为 `.env`、`tmp/`、浏览器 `localStorage` 等不会随 Git 迁移的本地状态。
   - Node 20 基线下 parser test 与生产构建均验证通过，可作为迁移前的稳定参考点。
5. 复盘 / Retrospective
   - “当前机器能跑”不等于“仓库已足够可迁移”；真正需要固化的是版本锚点、环境变量清单、不会随 Git 迁移的本地状态边界。
   - 对跨系统迁移，最稳的工作方式仍是“仓库提交完整基线 + 新机器重新安装依赖 + 原机器保留整目录备份”，而不是直接复用旧机器生成物。

## [2026-03-24] 环境迁移自动化与跨平台安装基线
0. Tags / 标签
   - infra, project-docs
1. Time
   - 2026-03-24
2. 需求明确 / Goal
   - 把“旧 Mac -> 新 Windows”迁移从手工记忆型流程收敛为仓库内可追溯的环境清单、跨平台安装脚本与统一验收脚本，降低换机后的环境对齐成本。
3. 操作 / Actions
   - 新增环境矩阵文档 `环境清单_安装矩阵_Environment_Matrix.md`，明确共享依赖真相源、旧 Mac 已知基线、Windows 对应安装方式与脚本职责。
   - 新增 `scripts/setup-mac.sh` 与 `scripts/setup-windows.ps1`，统一使用 `.nvmrc` 目标版本安装 Node，并串联 `npm ci`、Python 依赖安装、Playwright Chromium 安装与安装后验收。
   - 新增 `scripts/verify-install.mjs`，检查 Node/Python/OpenCC/Playwright/关键文件存在性，并自动执行 `npm run test:ctext-stats-parser` 与 `npm run build`。
   - 新增 `scripts/load-local-env.cjs`，让本地 Node 入口自动读取 `.env` / `.env.local`，同时保持 shell 或部署平台已有环境变量优先，不做覆盖。
   - 更新 `.eleventy.js`、CText middleware / proxy / Netlify function 与静态缓存构建脚本，使本地环境变量加载逻辑在主要 Node 入口上一致；同步更新 `README.md`、`.env.example`、`.gitignore` 与 `迁移说明_Windows环境与验证.md`。
   - 在旧 Mac 上执行 `npm run verify:install`，确认 parser test、生产构建以及 Playwright Chromium 可执行文件检查全部通过。
4. 解决 / Outcome
   - 仓库具备了面向新 Mac / 新 Windows 的统一迁移基线，clone 后可以通过系统对应脚本快速安装并验收整站基础环境。
   - 本地环境变量从“每次手工 export”收敛为“模板 + 自动加载 + 机器私有覆盖”模式，降低换机后遗漏配置的概率。
   - 这轮改动未触及前端页面 UI 与 canonical data 源文件，主要影响限定在安装、文档与本地 Node 运行入口。
5. 复盘 / Retrospective
   - 环境真相源必须保持共享，不能按操作系统拆成两套依赖清单；更稳妥的做法是“共享依赖文件 + 按系统分开的安装包装脚本 + 统一验收器”。
   - `.env` 自动加载应当作为低风险本地增强实现，前提是不覆盖 shell / CI / 部署平台已有变量，否则会引入新的排障成本。
   - 安装自动化能显著降低迁移风险，但不能替代实机验证；像 CText 动态链路这类受网络和上游站点影响的部分，仍需在新机器完成首次运行后单独确认。

## [2026-03-25] Windows 新机器实机验收与 VS Code 终端收口
0. Tags / 标签
   - infra, project-docs
1. Time
   - 2026-03-25
2. 需求明确 / Goal
   - 在用户从旧 Mac 切换到新 Windows 机器后，完成首次实机环境安装与验收，确认站点可在本机稳定启动，并收口 VS Code 内新开终端仍无法直接使用 `node` / `npm` 的最后一段落差。
3. 操作 / Actions
   - 在新 Windows 机器上实际执行 `scripts/setup-windows.ps1`，通过 winget / fnm 安装并接通 Git、Python 3.11、Node 20、npm 依赖、OpenCC 与 Playwright Chromium。
   - 修正 `scripts/verify-install.mjs` 的 Windows 子进程启动方式，使 `npm.cmd` / `npx.cmd` 可在验收脚本中正常执行，恢复 `npm run verify:install` 的完整链路。
   - 加固 `scripts/setup-windows.ps1`：
     - 新增统一命令失败检查，避免安装中途失败却继续输出“Setup complete”；
     - 将 Node 路径固化为 fnm 管理下的稳定安装目录，而非临时 multishell 路径；
     - 清理 PATH 中旧的 fnm 临时目录残留。
   - 新增 `.vscode/settings.json`，为本仓库内新开的 VS Code PowerShell 终端自动注入 `fnm env`，减少用户在仅使用 VS Code 时反复手动刷新 PATH 的负担。
   - 在新机器上做实机验证：
     - 运行 `npm run verify:install`；
     - 运行本地 `npm run start`；
     - 验证 `/`、`/transcriptions/`、`/transcriptions/tei_hanshu/1a/`、`/transcriptions/tei_brhat/1r/` 以及对应 XML / 图片资源可返回 `200`。
4. 解决 / Outcome
   - 新 Windows 机器上的环境安装、验收、构建与本地启动已全部打通，站点可以在本机正常运行。
   - `npm run verify:install` 现已在 Windows 上通过，补齐了此前只在旧 Mac 上验证通过的缺口。
   - VS Code 工作区内后续新开的终端可自动接通 fnm 环境；即使在旧终端未关闭的情况下，也可以通过一次性刷新 PATH 临时继续工作。
5. 复盘 / Retrospective
   - “脚本能跑通一次”不等于“用户日常工作流已打通”；这次最后真正卡住的不是依赖本身，而是 VS Code 已打开终端的环境继承与新终端 PATH 注入体验。
   - Windows 上通过 fnm 管理 Node 时，应优先写入稳定安装目录，而不是依赖临时 multishell 路径；否则表面看似装好了，实际在新终端里仍会随机失效。
   - 对迁移类任务，最稳的收口方式不是只看安装日志，而是把“命令能否直接在用户实际使用的 IDE 终端里启动”也纳入验收标准。
