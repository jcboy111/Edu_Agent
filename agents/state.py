"""
Global State 定义
维护整个对话上下文和学生学情
"""

from typing import TypedDict


class Message(TypedDict):
    """单条消息"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float


class AposLevel(str):
    """APOS 理论模型阶段"""
    ACTION = "action"      # 操作阶段 - 能模仿执行步骤
    PROCESS = "process"    # 过程阶段 - 能描述过程但不能抽象
    OBJECT = "object"       # 对象阶段 - 能把过程对象化
    SCHEMA = "schema"       # 图式阶段 - 能建立知识间联系


class Emotion(str):
    """情绪状态"""
    FRUSTRATED = "frustrated"    # 挫败感
    CONFUSED = "confused"        # 困惑
    NEUTRAL = "neutral"          # 中性
    CONFIDENT = "confident"      # 自信
    EXCITED = "excited"          # 兴奋


class AposTopicState(TypedDict):
    """单知识点的 APOS 状态"""
    level: str                         # "action" | "process" | "object" | "schema"
    consecutive_correct: int          # 连续正确次数（升阶用）
    consecutive_errors: int          # 连续错误次数（降阶用）
    last_practice: float             # 上次练习时间戳
    evidence: list[dict]             # 证据记录
    mastered_at: float | None         # 达成 Schema 时间（仅 Schema 有）


class StudentState(TypedDict):
    """
    全局状态 - Phase 1 使用单实例架构
    所有 Agent 共享同一个 LLM 实例，通过 State 传递上下文
    """

    # ========== 对话历史 ==========
    messages: list[Message]  # 对话消息列表

    # ========== 学情认知 ==========
    current_topic: str  # 当前知识点，如 "奇偶性"、"二次函数"
    apos_level: str | None  # APOS 阶段（独立维度1）
    learning_history: list[dict]  # 答题/学习历史

    # ========== 知识点掌握度 ==========
    knowledge_mastery: dict[str, float]  # 各知识点掌握度 {"奇偶性": 0.6, ...}
    weak_points: list[str]  # 薄弱知识点
    misconceptions: list[str]  # 概念混淆点

    # ========== 核心素养能力（独立维度2）============
    math_abilities: dict[str, float]  # 6大核心素养能力

    # ========== ZPD 近侧发展区 ==========
    zpd_min: float  # 学生当前能力下限
    zpd_max: float  # 学生当前能力上限
    hints_given: list[str]  # 已给出的提示（避免重复）

    # ========== 情绪与动机 ==========
    emotion: str  # 当前情绪状态
    motivation_level: float  # 动机水平 0.0-1.0

    # ========== 路由控制 ==========
    next_node: str  # 下一个执行的节点，由 Supervisor 决定
    node_history: list[str]  # 节点执行历史

    # ========== 工具调用 ==========
    pending_tool: str | None  # 待执行的工具名
    tool_params: dict | None  # 工具参数
    tool_result: dict | None  # 工具执行结果

    # ========== 教学策略 ==========
    teaching_strategy: str  # "socratic" | "direct" | "discovery"
    current_question: str | None  # 当前给出的支架问题
    question_sequence: list[str]  # 问题序列（递进式引导）
    current_question_index: int  # 当前问题在序列中的索引

    # ========== 错误追踪 ==========
    consecutive_errors: int  # 连续错误次数
    error_patterns: list[str]  # 错误模式识别

    # ========== APOS 追踪（按知识点）============
    apos_tracking: dict[str, AposTopicState]  # {"奇偶性": {...}, "单调性": {...}}
    schema_network: dict[str, list[str]]        # topic -> 关联的 topics（Schema 级别）
    schema_completed: bool                      # Schema 达成后的分流选择标志


def create_initial_state(topic: str = "奇偶性") -> StudentState:
    """创建初始状态"""
    import time
    return StudentState(
        messages=[],
        current_topic=topic,
        apos_level=None,
        learning_history=[],

        # 知识点掌握度
        knowledge_mastery={},
        weak_points=[],
        misconceptions=[],

        # 核心素养能力（6大素养，初始0.0）
        math_abilities={
            "数学抽象": 0.0,
            "逻辑推理": 0.0,
            "数学建模": 0.0,
            "直观想象": 0.0,
            "数学运算": 0.0,
            "数据分析": 0.0,
        },

        zpd_min=0.0,
        zpd_max=1.0,
        hints_given=[],
        emotion=Emotion.NEUTRAL,
        motivation_level=0.7,
        next_node="supervisor",
        node_history=[],
        pending_tool=None,
        tool_params=None,
        tool_result=None,
        teaching_strategy="socratic",
        current_question=None,
        question_sequence=[],
        current_question_index=0,
        consecutive_errors=0,
        error_patterns=[],

        # APOS 追踪
        apos_tracking={},  # 动态初始化，按 topic 添加
        schema_network={},  # topic -> [关联 topics]
        schema_completed=False
    )


def create_topic_state(topic: str) -> AposTopicState:
    """为单个知识点创建 APOS 状态"""
    import time
    return AposTopicState(
        level="action",
        consecutive_correct=0,
        consecutive_errors=0,
        last_practice=time.time(),
        evidence=[],
        mastered_at=None
    )
