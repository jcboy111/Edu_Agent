# Agent 设计文档

> 记录多 Agent 协作系统的详细设计。
> 最后更新：2026-04-29

---

## 一、架构概览

### 1.1 多 Agent 协作架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Global State (LangGraph)                  │
│              学情 / 情绪 / 历史消息 / 工具调用               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                 Supervisor（调度中心）                       │
│        职责：状态读取 + 路由决策 + next_node写入            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  学情诊断Agent │   │ 启发讲授Agent │   │ 问题解决Agent │
│  APOS判断     │   │ 苏格拉底提问  │   │ ReAct推理     │
│  学习路径     │   │ ZPD内支架问题 │   │ 逻辑启发      │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │ 虚拟学习伴侣Agent      │
                  │ 常驻监听 + 情绪检测    │
                  │ 动机调节               │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │    工具执行层          │
                  │ render_graph/animate   │
                  │ show_card/derivation   │
                  └───────────────────────┘
```

### 1.2 Phase 演进路线

| 阶段 | 架构 | 说明 |
|------|------|------|
| **Phase 1** | 单实例 | 所有 Agent 共用同一个 LLM 实例，通过 State 传递上下文 |
| **Phase 2** | 拆分推理重的 Agent | 问题解决 Agent 独立成单独实例 |
| **Phase 3** | 完全多实例 | 各 Agent 独立 LLM，通过 LangGraph 共享状态 |

---

## 二、Global State 设计

### 2.1 StudentState 字段定义

```python
class StudentState(TypedDict):
    # ========== 对话历史 ==========
    messages: list[Message]           # 对话消息列表

    # ========== 学情认知 ==========
    current_topic: str               # 当前知识点
    apos_level: str | None           # APOS 阶段（独立维度1）
    learning_history: list[dict]     # 答题/学习历史

    # ========== 知识点掌握度 ==========
    knowledge_mastery: dict[str, float]  # 各知识点掌握度 {"奇偶性": 0.6, ...}
    weak_points: list[str]              # 薄弱知识点
    misconceptions: list[str]            # 概念混淆点

    # ========== 核心素养能力（独立维度2）============
    math_abilities: dict[str, float]  # 6大核心素养能力

    # ========== ZPD ==========
    zpd_min: float                  # ZPD 下限
    zpd_max: float                  # ZPD 上限
    hints_given: list[str]          # 已给出的提示

    # ========== 情绪与动机 ==========
    emotion: str                    # 情绪状态
    motivation_level: float         # 动机水平 0.0-1.0

    # ========== 路由控制 ==========
    next_node: str                  # 下一个节点
    node_history: list[str]         # 节点执行历史

    # ========== 工具调用 ==========
    pending_tool: str | None        # 待执行工具
    tool_params: dict | None        # 工具参数
    tool_result: dict | None        # 工具执行结果

    # ========== 教学策略 ==========
    teaching_strategy: str          # 教学策略
    current_question: str | None   # 当前支架问题

    # ========== 错误追踪 ==========
    consecutive_errors: int         # 连续错误次数
    error_patterns: list[str]        # 错误模式
```

### 2.2 两个独立评估维度

| 维度 | 说明 | 评估方式 |
|------|------|---------|
| **APOS** | 认知发展阶段 | Action → Process → Object → Schema |
| **核心素养** | 能力维度 | 6大素养独立评分（0.0-1.0）|

### 2.3 核心素养定义

详见 `knowledge/高中数学核心素养.txt`

| 素养 | 说明 |
|------|------|
| 数学抽象 | 从具体到一般的归纳能力 |
| 逻辑推理 | 归纳/演绎推理能力 |
| 数学建模 | 实际问题数学化能力 |
| 直观想象 | 空间想象+数形结合 |
| 数学运算 | 计算准确性、技巧 |
| 数据分析 | 数据处理、统计推断 |

### 2.2 ZPD 映射（方案 A）

**当前使用方案 A：APOS 直接映射**

| APOS 阶段 | ZPD 范围 | 说明 |
|-----------|---------|------|
| Action | [0.3, 0.6] | 基础阶段，需要更多支架 |
| Process | [0.5, 0.8] | 理解过程，可适度挑战 |
| Object | [0.7, 0.9] | 抽象对象，可接受难题 |
| Schema | [0.8, 1.0] | 图式阶段，接近完全掌握 |

**后续可升级为方案 B：基于答题反馈渐进调整**

```python
class StudentState(TypedDict):
    messages: list[Message]           # 对话消息列表
    current_topic: str               # 当前知识点
    apos_level: str | None           # APOS 阶段
    learning_history: list[dict]     # 答题/学习历史
    zpd_min: float                  # ZPD 下限
    zpd_max: float                  # ZPD 上限
    hints_given: list[str]          # 已给出的提示
    emotion: str                    # 情绪状态
    motivation_level: float         # 动机水平 0.0-1.0
    next_node: str                  # 下一个节点
    node_history: list[str]         # 节点执行历史
    pending_tool: str | None        # 待执行工具
    tool_params: dict | None        # 工具参数
    tool_result: dict | None        # 工具执行结果
    teaching_strategy: str          # 教学策略
    current_question: str | None   # 当前支架问题
    consecutive_errors: int         # 连续错误次数
    error_patterns: list[str]        # 错误模式
```

### 2.2 待讨论字段

| 字段 | 问题 | 状态 |
|------|------|------|
| `session_id` | 多轮对话需要标识会话 | 待定 |
| `zpd_min/max` | 如何初始化和更新？ | 待讨论 |

---

## 三、Supervisor 设计

### 3.1 职责
- 状态读取 + 路由决策 + 状态更新

### 3.2 路由规则
```
1. apos_level 为空 → learning_diagnosis
2. pending_tool 存在 → tool_execution
3. 学生刚回答 → emotion_detection
4. 情绪检测完成 → heuristic_teaching / problem_solving
5. 其他 → 根据 teaching_strategy
```

### 3.3 实现方案：A+B 混合

**核心思路**：先用规则决策，规则无法决策时调用 LLM

```
学生发消息
    ↓
Step 1: 规则决策（B）
    ↓
if 规则能确定：
    直接使用规则结果
elif 规则模糊/冲突：
    ↓
Step 2: LLM 决策（A）
    ↓
调用 LLM，传入 State，LLM 输出 next_node
```

**什么情况需要 LLM 决策？**

| 情况 | 例子 |
|------|------|
| 多节点可能都适用 | 刚答对 → 可以启发讲授，也可以问题解决 |
| 教学策略需要调整 | 连续失败 → 策略从 socratic 切到 direct |
| 历史模式识别 | 学生连续 3 次在同一类型题卡住 |
| 情绪和学情冲突 | 情绪自信但 APOS 很低 |

### 3.4 B 规则详细定义

```
┌─────────────────────────────────────────────────────────────────┐
│                        规则决策流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  规则 1：APOS 未诊断                                             │
│  ─────────────────                                              │
│  IF apos_level is None                                          │
│  THEN → learning_diagnosis                                      │
│                                                                  │
│  规则 2：工具待执行                                               │
│  ─────────────────                                              │
│  IF pending_tool is not None                                    │
│  THEN → tool_execution                                          │
│                                                                  │
│  规则 3：学生刚回答                                               │
│  ─────────────────                                              │
│  IF messages[-1].role == "user"                                 │
│  THEN → emotion_detection                                       │
│                                                                  │
│  规则 4：情绪检测后的路由                                         │
│  ─────────────────                                              │
│  IF emotion == "frustrated" AND motivation < 0.4               │
│  THEN → heuristic_teaching (降难度，鼓励模式)                   │
│                                                                  │
│  IF emotion == "confident" OR emotion == "excited"              │
│  THEN → problem_solving (趁热打铁，推挑战题)                     │
│                                                                  │
│  ELSE                                                          │
│  THEN → heuristic_teaching                                      │
│                                                                  │
│  规则 5：连续错误处理                                             │
│  ─────────────────                                              │
│  IF consecutive_errors >= 3                                      │
│  THEN → emotion_detection (触发虚拟学习伴侣干预)                  │
│                                                                  │
│  兜底：无法决策 → LLM 决策                                       │
│  ─────────────────                                              │
│  THEN → llm_route_decision                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、各 Agent 详细设计

### 4.1 学情诊断 Agent
- 判断 APOS 阶段
- 评估 ZPD 范围
- 推荐教学策略

### 4.2 启发讲授 Agent
- 苏格拉底式提问
- ZPD 内支架问题
- 调用工具（图像/动画/卡片）

### 4.3 问题解决 Agent
- ReAct 模式逻辑推理
- 启发式提示（非完整答案）
- 知识图谱集成（解题步骤模板）
- 强化学习机制（简化版）

### 4.4 响应整合 Agent

**职责**：
- 整合所有 Agent 的输出，生成最终回复
- 情绪适配：调整语气和风格
- APOS 适配：调整用词和抽象程度
- 工具整合：融入图像/动画/卡片内容

**回复结构**：
1. 肯定 + 承接上文
2. 核心内容（结合工具）
3. 互动引导

### 4.5 工具执行层

**基础绘图工具**：
- render_graph：函数图像
- animate：动画演示
- mark_point：标记特殊点
- show_card：卡片（定义/定理/例题）
- show_derivation：推导过程

**GeoGebra 工具**：
- geogebra_function：函数图像（动态可交互）
- geogebra_geometry：几何图形
- geogebra_venn：Venn 图
- geogebra_interval：数轴/区间

详见 `knowledge/解题步骤模板.json` 中的 related_tools 字段。

---

## 八、知识图谱

详见 `knowledge/解题步骤模板.json`

```json
{
  "奇偶性": {
    "steps": ["判断定义域", "计算f(-x)", "比较关系", "判断奇偶性"],
    "related_tools": ["render_graph", "show_derivation"],
    "core_abilities": ["逻辑推理", "数学运算"]
  }
}
```

后续扩展为 Neo4j 图数据库。

## 五、待讨论事项

1. Supervisor 用 LLM 决策还是规则决策？
2. zpd_min/max 如何初始化和更新？
3. 工具执行层返回格式是否满足前端？
4. 是否需要 session_id / student_id？

---

## 六、APOS 状态机设计

### 6.1 状态定义

| 阶段 | 业务定义 | 升阶触发 | 降阶触发 | 降阶后教学 |
|------|---------|---------|---------|-----------|
| **Action** | 初始态，需借助具体数字/图表思考 | 内化 (Interiorization) | — | GeoGebra 画板 |
| **Process** | 内化操作流程，想象动态映射关系 | 封装 (Encapsulation) | 认知阻滞 (cognitive_block) | 拆解过程分析 |
| **Object** | 将过程打包成名词/客体 | 主题化 (Thematization) | 去封装化 (de_encapsulation) | 退 Process 分析 |
| **Schema** | 知识网络建构完成，准许流转 | ✅ 达成 | **不降阶** | 复习激活 |

### 6.2 跃迁图

```
Action ──[内化]──→ Process ──[封装]──→ Object ──[主题化]──→ Schema
   ↑                  │               │
   │                  │               │
   └─[认知阻滞]───────┘──[去封装化]───┘
```

### 6.3 检测函数

| 转移 | 检测方式 | 正面指标 | 负面指标 |
|------|---------|---------|---------|
| Action→Process | 能描述连续规律，不用具体数字 | "增大"、"减小"、"随x变化" | "x=1"、"代入" |
| Process→Object | 使用抽象名词 | "增函数"、"偶函数" | 描述过程 |
| Object→Schema | 关联其他知识点 | "类似"、"联系"、"方程" | — |

### 6.4 降阶条件

| 回退 | 条件 | 教学响应 |
|------|------|---------|
| **认知阻滞** | Process 阶段连续失败 + 表达困惑 | 退回 Action，调 GeoGebra |
| **去封装化** | Object 阶段面对复杂对象卡住 | 退回 Process，拆解分析 |

### 6.5 主观题评估

- 关键概念覆盖率 ≥ 70% 视为通过
- 用于 Process/Object 阶段的理解判断

---

## 七、变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-27 | 初始版本（3 Agent 架构）|
| 2026-04-29 | 新架构：4 Agent + Supervisor + 虚拟学习伴侣 |
| 2026-05-01晚 | APOS 状态机设计：升阶/降阶检测函数、追踪数据结构、证据记录 |
