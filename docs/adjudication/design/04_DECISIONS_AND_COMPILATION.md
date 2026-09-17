# 04 决策模型、应用时点与证据传播

## 1. 原始自动图与人工审定图分存
一次会话至少包含：source packet、自动analysis snapshot、candidate index、decision log、reviewed snapshot、validation、execution trace。
`parse_packet(packet)`保持自动模式；新增显式入口：

```python
compile_reviewed(packet: dict, session: dict) -> dict
```

外层review bundle有独立schema标识，不把字符串`schema_version=4.0`直接送入现有parse_packet：当前代码只有`3.`路由和旧兼容路由。

## 2. 决策地址
决策引用来源地址和可重复定位的语义地址，不能只存运行时`v127`或`ast9`：

```text
doc_id + reading_id + source_sha256 + [start,end) + quote
+ interpretation_branch + definition_anchor
+ role_path + invocation_path (when relevant)
```

运行时顺序ID可在UI显示，回放前由稳定地址重新解析。歧义时要求人工重绑定，不靠近似字符串迁移。

## 3. 审定账字段
- session_id、source/engine/ontology/profile hashes。
- decision_id、actor.type（human/agent/scripted_fixture）、actor.id、created_at。
- action、targets、payload、evidence_refs、reason、supersedes、depends_on。
- 原candidate snapshot及其hash，选择时存selected_candidate_id；人工新增时存authored_structure，不伪装成原候选。
- actor.type=human只能来自真实用户操作；可接受学者来源不等于真人执行过按钮。

动作目录：select_candidate、resegment、set_scope、assemble_known_structure、bind_value、bind_call、set_quantity_semantics、select_profile、attach_context、declare_parameter、mark_noncomputational、defer、approve_scope、retract。

`declare_parameter`需要source/evidence定位和合法参数角色。不得将程序应派生的量变成常数以绕开编译。自由文本理由是审计材料，不进入计算。

## 4. 应用位置
1. 校验source reading和会话版本；加载上次审定账。
2. 在词法/AST阶段应用resegment、term role和select/assemble。原自动候选保留，覆层产生新的审定树。
3. 在compile_frames阶段应用parent/query base/stage等范围判断；未知类别仍允许过程存在。
4. 重新计算def/use和导出端口；link_entry使用已验证的binding constraints选择producer及调用返回口。
5. lower_linked通过同一semantic backend生成图；新增操作使用P1–P5目录的验证与执行。
6. audit、完整目标闭包和执行检查；任何人工决策都不能绕过这些检查。
7. 保存新快照及差异；受影响下游决策置needs_revalidation。

不要在输出图上直接换几条边后宣布完成，也不要把审定AST转换成伪古文再喂旧parser。

## 5. 决策的一致性
- 两项活动决策对同一role设置不同producer：冲突，要求撤销其一或分为两个分析分支。
- 人工选了不兼容单位：拒绝执行；可附有来源的转换或解释profile后重验。
- 先改切分后原binding地址失效：标陈旧，不能沿用旧value序号。
- 更新分母/基态/方法体：使受影响执行记录失效；不能复用旧trace。
- attach_context加入新的定义，可能改变候选集合：已确认的链接必须重验，不能无声切换。
- 只审定一个局部阶段时，允许局部图；覆盖不足不得导出为完整主过程。

## 6. 证据的两条轴
`evidence_basis`表示原文/语法推断/学者解释/外部数据；`decision_origin`表示自动/人工选择/人工构造/代理示例。

机器自动传播一条由人工指定producer引出的边，可以标mechanically_derived，同时携带其decision_refs。不能恢复成纯text_overt。原Environment.event默认text_overt/declared_edited，必须增加覆层证据支持；简单改最后显示标签不够。

## 7. 可比图的承诺
同一版本目录下，同一种操作和端口采用相同语义契约；同名量仍可不同实体，不同名称也可对应同一角色。对语义/尺度尚未知的量，保留opaque或symbolic，限制可比维度。
审定通过不等于历史争议已经解决；图是采用已记录解释的可复查模型。
