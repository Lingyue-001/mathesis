# M1.5 / M1.5b — Procedure Workbench

本阶段连接真实 repo corpus → SourcePacket 3.0 → 原 v3.1 compiler/IR → 研究者投影视图 → 同源本地网站。M1.5b 将技术 smoke 的独立 shell 替换为站内 Procedure Workbench；主轴是 Source ↔ hierarchical procedure structure ↔ graph，数值执行是辅助验证。基点为 M1 commit `a3eca4f4d2b062e670ca3cd901b3163b6b434140`。停在本地人工查看，不进入 M2。

## 启动与操作

在 repo 根目录，使用项目现有 Node 20 和 Python 3.11（无需新增依赖）：

```powershell
node node_modules/@11ty/eleventy/cmd.js --output=.cache/workbench/site
python -X utf8 -B -m workbench.api --port 8789
```

打开 <http://127.0.0.1:8789/adjudication/>，或从网站侧栏选择 Procedure Workbench。Python 同时提供 Eleventy 构建产物与 API；`/` 是真实 MATHesis 首页，Pattern Lab 也在同一站点内可访问。无需代理或第二个端口。默认仅监听 IPv4 loopback；前台启动后可用 Ctrl+C 停止。端口占用时用 `--port` 指定空闲端口。修改页面/JS/CSS 后重新执行构建；修改 Python 后重启服务。单独 Eleventy 静态服务没有 Python API，页面会明确显示未连接分析服务。

本地构建要求根路径 `/`，构建时不要设置 `GITHUB_ACTIONS=true`。带 `/mathesis/` 前缀的 GitHub Pages 产物不作为本地 API 的站点目录；服务会在启动前明确拒绝该不兼容配置，不会启动后留下失效的资源/API 链接。线上构建规则保持原样。

1. 选择「四分历 · 推天正術（Cullen Proc. 3.5）」。自动读取真实 corpus 第 38 段及第 15、16 段上下文，并编译结构；此时不调用 executor。
2. 点击「以章月乘之」：同时定位 Multiply 步骤和 `e7`。点击 DivMod 步骤或图中 `e8`：反向高亮「滿章法得一」，在选中对象详情查看 quotient / remainder 端口、角色、依赖、unit / scale、scope / control。
3. 在结构栏浏览 procedure、query/stage 和按原文排序的语法步骤。图显示 12 events、13 values、11 条数据依赖边。展开「原始 IR / graph JSON」查看未修改的编译结果。
4. 「Unresolved / structure diagnostics」明确保留 `missing_import: 入蔀年` 和 `quantity_unresolved: v7`。原 smoke 只统计顶层 compiler diagnostics；新投影同时显示 linker 与 quantity 层，因此这 2 项不是本轮新产生的 parser 错误。
5. 需要数值校验时，展开默认折叠的「Numerical reconstruction / consistency check」，输入 `25` 后 Execute，得到 `main:積月 = 296`、`main:閏餘 = 16`。结构选择状态保持不变，数值成功不消除上述结构提示。
6. 清空输入再执行可见 `missing_inputs`；输入 `77` 被拒绝，上一轮数值结果隐藏。

Proc. 3.5 只是一个 example，当前范围是以入蔀年（1–76）为输入的局部过程。投影与 UI 不读取该 procedure ID 或原文来选择专用流程；新增登记可进入同一视图。投影测试另外覆盖不同术文、未解析步骤和嵌套 QueryDef。此页面不宣称完整历史链条闭合或 scholar adjudication 已完成。

## Module boundaries

| 位置 | 职责 |
|---|---|
| `config/workbench-procedures.json` | 有限 procedure 登记、Cullen 定位、corpus 段号/文本 hash、局部输入契约；不含源文副本、图或预设答案 |
| `source_adapters/corpus.py` | 复用现有 pipeline config 的 source path；按已登记段号提取精确原文；生成 SourcePacket 3.0 |
| `workbench/projection.py` | 纯只读 IR → frames、ordered steps、event nodes、typed quantities、port edges、跨层 issues；不解析、不执行、不修补图 |
| `workbench/service.py` | `analyze_procedure()` 只编译及投影；`compile_procedure()` 再按既有输入契约调用 execute |
| `workbench/api.py` | 同源 localhost API + Eleventy 构建目录；拒绝目录穿越，不暴露 repo 源文件 |
| `src/adjudication.md`、`src/js/procedure-workbench.js` | 使用真实 base layout 和导航的独立分页；只维护本页 selection/loading 状态 |
| `src/js/ui/source-links.js`、`procedure-view.js` | 无状态 source-range、hierarchy、graph 和 typed detail 渲染；复用 `ui/heatmap.js` 的安全文本工具 |
| `src/css/research.css`、`workbench.css` | 可复用研究对象交互样式 / 本页布局；卡片、表单、字体和详情列表复用原全局 CSS |
| `tests/workbench/` | adapter、真实执行、HTTP 边界及浏览器集成测试 |

每个 document 的 `source.start/end` 是完整 UTF-8 corpus 文件解码后、未转换换行的 Unicode code-point 范围，零基、尾端不包含。原文标点保留；段缺失、重复或文本 hash 改变会明确失败。Packet 含每段及完整 corpus 的 SHA-256，可追溯本次输入。已登记 Cullen → source 段号对应关系是固定入口，不使用运行时关键词猜测，不读 `tmp/` 重建快照。

登记保留 source reconstruction 的 `sifen:L74` 以及参数 `sifen:L28/L30` 身份、原审计/source-span-index hash，并给出 Cullen 原始 layout 的引文/译文/说明字符范围与 hash。旧审计的派生引文漏掉「得一」，原状态仍为 `fail` / `needs_human_review`，本轮没有改写或宣称它通过。为核实局部输入，本次 agent 直接核对已找回的原始 layout 第 177 页（印刷第 164 页）；完整引文包含「滿章法得一」，译文明列 19/235 两个参数，说明从入蔀序年减一。登记明确 `scholar_adjudicated: false`。这些是紧凑的证据引用，生产 adapter 不打开 layout、PDF 或历史审计文件。

API：`GET /api/procedures`、`GET /api/procedures/{id}`、`GET /api/analysis/{id}`、`POST /api/compile`。编译 body 只允许 `procedure_id` 和 `inputs`；每次从 repo 重建 packet，客户端不能提交源文或替换图。静态服务仅限独立 Eleventy 构建目录，不提供 repository 文件浏览。生产调用链不依赖 evaluation、review、checkpoint、Downloads 或历史结果。

投影中的 frame/step/event/value ID 保留原 IR 身份；procedure/stage 直接来自 definition 的 parent/body，不根据 Proc. 3.5 编造阶段。图边来自 event.reads → value.producer/output_port，保留 consumer input slot。`graph_links.basis` 区分编译器明确 `syntax_node_id` 与共享 source-span 对应；共享范围不是新增语义依赖。一段文字可关联多个节点；没有独立 event 的语法节点仍保留。浏览器使用 Unicode code-point 范围分段，覆盖补充平面字符，不以词形搜索替代范围定位。

本阶段没有 AdjudicationSession / ReviewedProcedureBundle，也没有改变 SourcePacket 3.x 路由。没有人工切分、candidate selection、decision log/replay 或 primitive 扩展；M2/M3 的版本和验收继续由原 [requirements matrix](adjudication/requirements.md) 管理。已增加一条共用导航链接，Pattern Lab 的页面状态、six-axis scoring、源文件与行为保持不变；没有新增线上 API 部署。

## 验证与重跑

2026-09-17，Windows、Python 3.11.9、Node 20.20.1：

| 检查 | 结果 |
|---|---|
| Workbench Python 测试 | 15/15：原有 7 项、新增 7 项投影/不执行分析测试，以及本地构建前缀检查 |
| 浏览器 smoke | 实际站内分页、双向 source/step/graph 联动、端口/scale、Unicode/键盘、默认不执行、辅助数值验证、390px/1600px 布局、导航进入旧 Pattern Lab；通过 |
| 旧 parser / v3 / rescue | 61/61、94/94、78/78 |
| 工程检查 | 35/35（已包括在 rescue 78 项中） |
| M1 integration / portability | 5/5 |
| A01–A04 严格 gate | 22/22 obligations、4/4 full chains；FP=FN=0、runtime guard clean、behavior changes=[] |
| 网站 | 4/4 原测试；Eleventy 14 页、88 个复制文件（新增本分页及 5 个 JS/CSS） |
| 生产身份 / 原站点保护 | core 16/16 原字节；106 个原保护文件中 105 个未改，唯一变更为 base layout 增加导航链接 |

```powershell
python -X utf8 -B -m unittest discover -s tests/workbench -v
# 先启动 workbench，再使用项目现有 Node 20 / Playwright：
node tests/workbench/browser-smoke.mjs
# 改端口时设置 WORKBENCH_URL，例如 http://127.0.0.1:8790
```

旧回归命令见 [M1 reconciliation](reconciliation/README.md#重跑命令)。本轮 runner 大输出、服务日志及浏览器截图在 ignored `.cache/workbench/`；不导入历史档案或大图。浏览器测试是软件验收，不能替代 M4 的真实 scholar 试用及实际人工负担记录。
