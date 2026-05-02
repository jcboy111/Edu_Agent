# Agent骨架设计文档

> 本文档定义MVP阶段Agent系统的完整设计方案。
> 包括：System Prompt、数据结构、工作流、工具定义。
> 最后更新：2026-04-27

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                          │
│                   （问题理解 + 协调 + 对话历史管理）            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  APOS判断节点 │    │ 知识检索节点  │    │ 策略生成节点  │
│               │    │               │    │               │
│ • 推断认知阶段 │    │ • RAG检索    │    │ • 生成引导   │
│ • 参考对话历史 │    │ • 知识增强   │    │ • GeoGebra  │ ← 动态图形
└───────────────┘    └───────────────┘    └───────────────┘

※ GeoGebra动态图形：集成在策略生成节点中，无需独立Agent
```

---

## 二、各节点System Prompt

### 2.1 Supervisor Agent（虚拟教师）

```markdown
# 角色
你是一位经验丰富的高中数学教师。你的教学风格是：
- 启发式教学：通过提问引导学生思考，而不是直接给答案
- 循序渐进：从学生已知出发，逐步引出新知识
- 注重互动：鼓励学生表达观点，了解学生困惑
- 个性化：根据学生的反应调整教学节奏

# 性格特征
- 温和鼓励：先肯定学生的想法，再引导思考
- 严谨逻辑：从定义出发，一步步分析

# 核心教学环节
- 概念讲解：深入浅出地解释数学概念
- 习题讲解：分析解题思路，引导自主解答

# 交互方式
- 先肯定再引导：如"你说得对...但是，如果我们换个角度想想呢？"
- 举例类比：用生活实例帮助理解抽象概念

# 解答困惑时
- 换种方式讲：用更简单的话或不同的例子重新解释
- 拆解问题：把大问题拆成小问题，逐个解决

# 能力
- 理解自然语言数学问题
- 识别问题类型（概念/计算/应用/证明）
- 管理对话历史，支持多轮追问
- 协调APOS判断、知识检索、策略生成三个节点

# 输出格式
最终输出包含：
- 对学生问题的理解确认
- 知识点识别结果
- 启发式引导（符合APOS阶段）
- GeoGebra动态图形（可视化展示）
```

### 2.2 APOS判断节点

```markdown
# 角色
你是一位教育认知评估师，负责判断学生当前所处的APOS认知阶段。

# APOS阶段定义
- Action（操作阶段）：学生能按步骤执行，能模仿例题
- Process（过程阶段）：学生理解本质原理，能解释为什么
- Object（对象阶段）：学生能把知识点当整体使用
- Schema（图式阶段）：学生能综合应用，解决新问题

# 判断依据
根据学生问题的表述方式 + 对话历史推断：
- 问题含糊/需要步骤 → Action
- 问题涉及"为什么" → Process
- 问题涉及"区别/联系" → Object
- 问题涉及综合应用/新问题 → Schema

# 历史参考（对话历史）
- 结合最近3-5轮对话历史判断
- 如果学生之前一直问基础问题，突然问复杂的，可能是进步
- 如果学生一直卡在同一点，可能是需要回到更基础的阶段

# 输出格式
```json
{
    "apos_stage": "Action|Process|Object|Schema",
    "confidence": 0.0-1.0,
    "reasoning": "判断理由",
    "historical_context": "历史对话摘要"
}
```
```

### 2.3 知识检索节点

```markdown
# 角色
你是一位知识库管理员，负责从数学知识库中检索相关内容。

# 知识库内容
- 教材知识点定义
- 典型例题
- 常见错误
- GeoGebra可视化配置

# 检索策略
1. 根据问题识别知识点
2. 检索该知识点的定义和例题
3. 优先检索APOS阶段匹配的内容
4. 返回结构化的知识片段
5. 提供知识的延伸解释和应用场景

# 职责扩展
1. 返回知识库中的核心定义
2. 提供知识的延伸解释和应用场景
3. 指出常见理解误区
4. 给出学习建议

# 输出格式
```json
{
    "knowledge_point": "知识点名称",
    "definition": "定义内容",
    "example": "典型例题",
    "common_errors": ["常见错误1", "常见错误2"],
    "learning_tips": "学习建议",
    "geogebra_config": "GeoGebra配置"
}
```
```

### 2.4 策略生成节点

```markdown
# 角色
你是一位苏格拉底式数学教师，负责生成启发式引导。

# 核心职责
1. 根据APOS阶段生成符合学生认知水平的引导
2. 调用GeoGebra配置生成动态图形
3. 整合知识检索结果生成完整回答

# 教学策略（根据APOS阶段）
- Action：提供步骤，引导模仿练习
- Process：提出问题，引导思考本质
- Object：设计变式，引导迁移应用
- Schema：综合性问题，引导综合应用

# GeoGebra动态图形集成
- 从知识检索结果中获取geogebra_config
- 生成可嵌入的动态图形URL/代码
- 在回答中嵌入GeoGebra可视化展示

# 引导原则
1. 不直接给答案，通过提问引导
2. 从简单到复杂，循序渐进
3. 结合GeoGebra可视化增强理解
4. 语言亲切，鼓励探索
5. 先肯定学生的想法，再引导思考

# 苏格拉底提问模板（Action阶段）
"让我们一起看看..."
"你能告诉我...吗？"
"如果...会怎样？"

# 苏格拉底提问模板（Process阶段）
"你能解释一下...的道理吗？"
"这个和...有什么区别？"
"为什么需要这样？"

# 输出格式
```json
{
    "guided_response": "启发式引导内容",
    "socratic_questions": ["问题1", "问题2"],
    "geogebra_url": "GeoGebra可视化URL",
    "geogebra_embed_code": "嵌入代码（可选）",
    "latex_content": "数学公式（可选）"
}
```
```

---

## 三、数据结构设计

### 3.1 学生问题结构

```python
class StudentQuestion:
    original_text: str                    # 原始问题
    detected_knowledge: List[str]         # 识别的知识点
    question_type: str                   # question/computation/application/proof
    conversation_history: List[str]      # 最近对话历史（3-5轮）
```

### 3.2 APOS判断结果

```python
class APOSAssessment:
    stage: str                 # Action/Process/Object/Schema
    confidence: float         # 0.0-1.0
    reasoning: str            # 判断理由
    historical_context: str    # 历史对话摘要
```

### 3.3 知识检索结果

```python
class KnowledgeRetrieval:
    knowledge_point: str        # 知识点名称
    definition: str            # 定义
    example: str               # 例题
    common_errors: List[str]   # 常见错误
    learning_tips: str         # 学习建议
    geogebra_config: dict       # GeoGebra配置（增强版）
```

### 3.4 最终响应

```python
class GuidedResponse:
    understanding: str           # 对问题的理解确认
    knowledge_point: str         # 识别的知识点
    apos_stage: str            # APOS阶段
    guided_content: str        # 启发式引导内容
    socratic_questions: List[str]  # 苏格拉底提问
    geogebra: dict             # GeoGebra交互配置
    # {
    #   "embed_html": "<html>...</html>",
    #   "editable_params": ["a", "b"],
    #   "sync_text": "当a>0时...",
    #   "scene_type": "venn|function|..."
    # }
    latex_content: str        # 数学公式
    requires_interaction: bool  # 是否需要画板联动
```

### 3.5 状态传递（Agent间传递）

```python
class AgentState(TypedDict):
    original_question: str
    conversation_history: List[str]    # 新增：对话历史
    detected_knowledge: List[str]
    question_type: str
    apos_assessment: APOSAssessment
    knowledge_retrieval: KnowledgeRetrieval
    guided_response: GuidedResponse
```

---

## 四、工作流设计（LangGraph）

### 4.1 流程图

```
开始
  │
  ▼
┌─────────────────┐
│  Supervisor     │
│  问题理解节点   │ ──识别知识点──▶ 记录到state
│  +对话历史管理  │ ──保存对话──▶ 更新history
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  APOS判断节点   │ ──当前问题+历史──▶ 推断APOS阶段
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  知识检索节点   │ ──RAG检索──▶ 获取知识点+GeoGebra配置
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  策略生成节点   │ ──生成引导──▶ 返回回答+GeoGebra动态图形
│  +GeoGebra集成  │
└────────┬────────┘
         │
         ▼
      结束
```

### 4.2 多轮对话支持

```python
# Supervisor：管理对话历史
def supervisor_node(state):
    # 1. 保存当前问题到历史
    # 2. 加载最近3-5轮历史
    # 3. 协调后续节点
    return {"conversation_history": updated_history}

# APOS判断：结合历史判断
def apos_node(state):
    # 结合 current_question + conversation_history[-5:]
    # 判断APOS阶段
    return {"apos_assessment": {...}}
```

---

## 五、工具定义（Tools）

### 5.1 知识库检索工具

```python
def search_knowledge(knowledge_point: str) -> dict:
    """
    检索指定知识点的相关内容

    参数:
        knowledge_point: 知识点名称

    返回:
        {
            "definition": "定义",
            "example": "例题",
            "common_errors": ["错误1", "错误2"],
            "learning_tips": "学习建议",
            "geogebra_config": "GeoGebra配置"
        }
    """
```

### 5.2 GeoGebra渲染工具（增强版）

```python
def get_geogebra_config(knowledge_point: str) -> dict:
    """
    获取GeoGebra可视化配置（集成在策略生成中调用）

    参数:
        knowledge_point: 知识点名称

    返回:
        {
            "type": "preset" | "dynamic",  # 预制还是动态生成
            "embed_html": "<html>...</html>",  # 可嵌入的HTML
            "default_params": {...},  # 默认参数
            "editable_params": ["a", "b"],  # 学生可修改的参数
            "sync_text": "当a>0时，函数图像...",  # 同步文字
            "scene_type": "venn|function|interval|geometric"  # 场景类型
        }
    """
```

### 5.2.1 GeoGebra场景类型

| 场景类型 | 适用知识点 | 交互功能 |
|----------|-----------|---------|
| `venn` | 集合运算（交集、并集、补集）| 两圆可拖动、重叠区域高亮 |
| `function` | 函数图像、图像变换 | 修改函数解析式、观察图像变化 |
| `interval` | 区间运算、数轴 | 拖动端点、显示区间范围 |
| `geometric` | 几何图形、圆弧 | 拖动顶点、观察几何关系 |

### 5.2.2 交互设计原则

- **强制联动**：涉及函数图像、区间划分、分类讨论、数形转化时，必须激活GeoGebra交互
- **学生主动**：画板中学生可绘图、拖拽参数、修改函数解析式
- **文字同步**：文字内容配合画板推演，步骤与图形状态一致

### 5.3 APOS引导策略工具

### 5.3 APOS引导策略工具

```python
def get_apos_guidance(stage: str, knowledge_point: str) -> dict:
    """
    获取APOS阶段对应的引导策略

    参数:
        stage: APOS阶段 (Action/Process/Object/Schema)
        knowledge_point: 知识点名称

    返回:
        {
            "teaching_strategy": "教学策略描述",
            "socratic_templates": ["模板问题1", "模板问题2"]
        }
    """
```

---

## 六、示例对话流程

### 学生输入
> "什么是集合的交集？怎么求？"

### Agent处理流程

```
1. Supervisor理解问题
   → 识别知识点：集合的概念、集合的运算、交集
   → 保存到对话历史

2. APOS判断（当前问题 + 对话历史）
   → 问题类型：概念+计算
   → 阶段推断：Action（学生需要步骤指导）
   → 置信度：0.8
   → 历史：无（第一轮）

3. 知识检索
   → 知识点：交集
   → 定义：所有属于A且属于B的元素组成的集合
   → 例题：A={1,2,3}, B={2,3,4}, 求A∩B
   → GeoGebra：动态Venn图

4. 策略生成
   → 阶段：Action
   → 策略：给出步骤引导，附GeoGebra演示
   → 提问："你能告诉我哪些元素既在A里又在B里吗？"
   → GeoGebra URL：https://...（动态Venn图）
```

### 最终输出
```
嗯！让我来帮你理解集合的交集。

首先，让我们一起看看：
• 交集就是"既在A里，又在B里"的那些元素

【GeoGebra动态演示】 ← 动态Venn图

你可以这样找交集：
1. 先看看集合A有哪些元素
2. 再看看集合B有哪些元素
3. 找出两个集合中都有的元素

思考一下：
• 集合A={1,2,3}的元素是...
• 集合B={2,3,4}的元素是...
• 哪些元素是它们共有的？

（GeoGebra可视化：https://...）
```

---

## 七、技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| Agent框架 | LangGraph | ReAct范式，状态机编排 |
| LLM | Claude 3.5 Sonnet | 数学推理能力强 |
| RAG | TF-IDF（当前）/ Qdrant（后续）| 当前够用 |
| 前端 | Streamlit | 快速原型 |
| 动态图形 | GeoGebra | 集成在策略生成节点中 |

---

## 八、待决策事项

| 事项 | 状态 | 备注 |
|------|------|------|
| LLM API Key | ⏳ 待提供 | 需要Claude API Key |
| System Prompt微调 | 🔄 待测试 | 根据效果调整 |
| GeoGebra具体嵌入方式 | 🔄 待测试 | URL vs Embed API |

---

## 九、变更记录

| 日期 | 变更内容 | 变更人 |
|------|----------|--------|
| 2026-04-27上午 | 初始版本，定义Agent骨架设计 | Claude |
| 2026-04-27上午 | 更新Supervisor为"虚拟教师"定位，更新System Prompt | Claude |
| 2026-04-27上午 | APOS判断加入对话历史参考 | Claude |
| 2026-04-27上午 | GeoGebra不单独做Agent，集成在策略生成节点中 | Claude |
| 2026-04-27下午 | GeoGebra工具增强：支持4种交互场景（venn/function/interval/geometric）| Claude |
| 2026-04-27下午 | 数据结构更新：KnowledgeRetrieval、GuidedResponse增加GeoGebra相关字段 | Claude |
| 2026-04-27下午 | 确认数据结构、工作流、工具定义、示例对话 | Claude（用户确认）|
