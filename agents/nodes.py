"""
Agent 节点实现
Phase 1: 单实例架构，通过 LLM 调用各 Agent 逻辑
"""

import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import StudentState, Message
from .prompts import (
    SUPERVISOR_PROMPT,
    LEARNING_DIAGNOSIS_PROMPT,
    HEURISTIC_TEACHING_PROMPT,
    PROBLEM_SOLVING_PROMPT,
    EMOTION_DETECTION_PROMPT,
    TOOL_EXECUTION_PROMPT,
    RESPONSE_PROMPT,
)


# LLM 实例（Phase 1 使用 MiniMax）
llm = ChatOpenAI(
    model="MiniMax-M2.7",
    api_key="sk-cp-livIF2YQqaPga9xkSIbaDt5hn6q-v0VHR73g4EYEjuATVdYvxBV_WdxDLRF2zaD-2BGSXQ7BgY1rJ4Jvm1QIUDKNC3pwk8ePpJgAj6xN-PJphGRHB5iFKFI",
    base_url="https://api.minimaxi.com/v1",
    max_tokens=2048,
    timeout=60,
)


def _format_state(state: StudentState) -> str:
    """将 State 格式化为可读字符串"""
    return json.dumps({
        "current_topic": state.get("current_topic"),
        "apos_level": state.get("apos_level"),
        "emotion": state.get("emotion"),
        "motivation": state.get("motivation_level"),
        "teaching_strategy": state.get("teaching_strategy"),
        "next_node": state.get("next_node"),
        "node_history": state.get("node_history", [])[-3:],
        "pending_tool": state.get("pending_tool"),
        "consecutive_errors": state.get("consecutive_errors"),
        "current_question": state.get("current_question"),
    }, ensure_ascii=False, indent=2)


def _get_recent_messages(state: StudentState, n: int = 3) -> str:
    """获取最近 n 条消息"""
    messages = state.get("messages", [])
    if not messages:
        return "（无历史消息）"
    recent = messages[-n:]
    return "\n".join([f"- {m['role']}: {m['content'][:100]}" for m in recent])


# ========== APOS 转移检测 ==========
import time

TRANSITION_THRESHOLD = 2  # 连续答对次数阈值
SUBJECTIVE_THRESHOLD = 0.7  # 主观题概念覆盖率阈值


def detect_level_transition(student_answer: str, current_level: str, topic: str) -> dict:
    """
    检测是否触发 APOS 升阶
    返回: {"transition": bool, "new_level": str, "confidence": float, "evidence": dict}
    """
    if current_level == "action":
        return _detect_interiorization(student_answer, topic)
    elif current_level == "process":
        return _detect_encapsulation(student_answer, topic)
    elif current_level == "object":
        return _detect_thematization(student_answer, topic)
    return {"transition": False, "new_level": current_level, "confidence": 0.0, "evidence": {}}


def _detect_interiorization(student_answer: str, topic: str) -> dict:
    """
    Action → Process (内化)
    学生能描述连续变化规律，不用具体数字代入
    """
    # 负面指标（仍处于 Action）
    action_indicators = [
        "x=", "y=", "代入", "算一下", "具体数字",
        "当x=1", "当x=2", "比如x=3", "取x=4"
    ]

    # 正面指标（已内化到 Process）
    process_indicators = {
        "奇偶性": ["f(-x)", "等于", "相反", "对称"],
        "单调性": ["增大", "减小", "变大", "变小", "随x增加", "随x增大"],
        "二次函数": ["开口向上", "开口向下", "顶点", "对称轴"],
    }.get(topic, ["增大", "减小", "变化", "随x"])

    has_action = any(ind in student_answer for ind in action_indicators)
    has_process = any(ind in student_answer.lower() for ind in process_indicators)

    if has_process and not has_action:
        return {
            "transition": True,
            "new_level": "process",
            "confidence": 0.75,
            "evidence": {
                "type": "interiorization",
                "description": f"学生能用语言描述变化规律，不用具体数字"
            }
        }

    return {"transition": False, "new_level": "action", "confidence": 0.0, "evidence": {}}


def _detect_encapsulation(student_answer: str, topic: str) -> dict:
    """
    Process → Object (封装)
    学生能使用抽象名词，不再描述过程
    """
    # 抽象名词（已封装）
    abstract_terms = {
        "奇偶性": ["偶函数", "奇函数", "奇偶性"],
        "单调性": ["增函数", "减函数", "单调性", "单调递增", "单调递减"],
        "二次函数": ["二次函数", "抛物线", "顶点式", "交点式"],
    }.get(topic, ["函数", "关系"])

    found_terms = [t for t in abstract_terms if t in student_answer]

    if found_terms:
        return {
            "transition": True,
            "new_level": "object",
            "confidence": 0.8,
            "evidence": {
                "type": "encapsulation",
                "description": f"学生使用了抽象名词：{found_terms}",
                "terms": found_terms
            }
        }

    return {"transition": False, "new_level": "process", "confidence": 0.0, "evidence": {}}


def _detect_thematization(student_answer: str, topic: str) -> dict:
    """
    Object → Schema (主题化)
    学生能关联其他知识点
    """
    # 跨知识点关联词
    cross_topic_indicators = [
        "方程", "不等式", "解集", "根", "图像", "性质",
        "类似", "联系", "对比", "迁移", "推广"
    ]

    # 特定知识点的关联词（扩展）
    topic_specific_indicators = {
        "奇偶性": ["单调性", "二次函数", "函数", "图像", "性质"],
        "单调性": ["奇偶性", "二次函数", "函数", "不等式"],
        "二次函数": ["抛物线", "顶点", "单调性", "奇偶性"],
    }.get(topic, [])

    all_indicators = cross_topic_indicators + topic_specific_indicators
    has_cross_topic = any(ind in student_answer for ind in all_indicators)

    if has_cross_topic:
        return {
            "transition": True,
            "new_level": "schema",
            "confidence": 0.7,
            "evidence": {
                "type": "thematization",
                "description": "学生能建立跨知识点关联"
            }
        }

    return {"transition": False, "new_level": "object", "confidence": 0.0, "evidence": {}}


def detect_degradation(student_answer: str, current_level: str, consecutive_errors: int) -> dict:
    """
    检测是否触发降阶（仅 Process/Object 有降阶，Schema 不降阶）
    """
    # 认知阻滞 (Process → Action)
    if current_level == "process" and consecutive_errors >= 2:
        confusion_signals = ["不理解", "不懂", "为什么", "什么意思", "糊涂", "迷糊"]
        if any(signal in student_answer for signal in confusion_signals):
            return {
                "degrade": True,
                "new_level": "action",
                "reason": "cognitive_block",
                "description": "连续抽象失败 + 表达困惑，退回 Action"
            }

    # 去封装化 (Object → Process)
    if current_level == "object" and consecutive_errors >= 2:
        complex_signals = ["太难了", "不会", "不知道从哪里下手", "复杂", "搞不清"]
        if any(signal in student_answer for signal in complex_signals):
            return {
                "degrade": True,
                "new_level": "process",
                "reason": "de_encapsulation",
                "description": "面对复杂对象卡住，退回 Process 分析过程"
            }

    return {"degrade": False, "new_level": current_level, "reason": None, "description": ""}


def assess_subjective_response(student_answer: str, target_concepts: list[str], threshold: float = 0.7) -> dict:
    """
    主观题评估：检测关键概念是否出现
    """
    found = [c for c in target_concepts if c in student_answer]
    coverage = len(found) / len(target_concepts) if target_concepts else 0

    return {
        "pass": coverage >= threshold,
        "coverage": coverage,
        "found_concepts": found,
        "missing_concepts": [c for c in target_concepts if c not in student_answer]
    }


# ========== Supervisor 节点 ==========
def supervisor_node(state: StudentState) -> dict:
    """
    调度中心 - A+B 混合决策

    Step 1: 规则决策 - 能确定就只用规则
    Step 2: 规则模糊时 - 调用 LLM 决策
    """

    # Step 1: 规则决策
    next_node = _rule_based_route(state)

    # Step 2: 规则无法决策时，调用 LLM
    if next_node == "UNDECIDED":
        next_node = _llm_route_decision(state)

    return {
        "next_node": next_node,
        "node_history": state.get("node_history", []) + ["supervisor"]
    }


def _rule_based_route(state: StudentState) -> str:
    """
    规则决策 - B 方案

    核心逻辑：只运行必要的节点，避免循环
    - 首次诊断后，按照 emotion → strategy → response 的顺序执行
    - 一旦响应已生成，立即结束
    """
    messages = state.get("messages", [])
    emotion = state.get("emotion", "neutral")
    consecutive_errors = state.get("consecutive_errors", 0)
    node_history = state.get("node_history", [])

    # 规则 0: 如果上一轮执行了 response，说明已经生成回复，结束
    if node_history and node_history[-1] == "response":
        return "END"

    # 规则 1: APOS 未诊断 → 首次必须诊断
    if not state.get("apos_level"):
        return "learning_diagnosis"

    # 规则 2: 工具待执行 → 必须先执行工具
    if state.get("pending_tool"):
        return "tool_execution"

    # 规则 3: 如果已经有 AI 回复且还没做过学情诊断 → 直接结束（首次提问才需要诊断）
    # 已诊断过学情的，后续回答应该继续走完整流程（emotion_detection → teaching）
    ai_messages = [m for m in messages if m.get("role") == "assistant"]
    if ai_messages and not state.get("apos_level"):
        return "END"

    # 规则 4: 连续错误 >= 3 → 虚拟学习伴侣干预
    if consecutive_errors >= 3:
        return "emotion_detection"

    # 规则 5: 情绪检测后的路由
    # 只在刚执行过 emotion_detection 后才考虑，避免重复进入
    if node_history and node_history[-1] == "emotion_detection":
        teaching_strategy = state.get("teaching_strategy", "socratic")
        if teaching_strategy == "direct":
            return "heuristic_teaching"
        elif teaching_strategy == "discovery":
            return "problem_solving"
        else:
            # socratic strategy defaults to heuristic_teaching
            return "heuristic_teaching"

    # 规则 6: 刚执行完启发讲授/问题解决 → 应该生成响应
    # 如果上一轮是 heuristic_teaching 或 problem_solving，且没有 pending_tool
    if node_history and node_history[-1] in ("heuristic_teaching", "problem_solving"):
        if not state.get("pending_tool"):
            return "response"

    # 规则 7: 学生刚回答 → emotion_detection
    if messages and messages[-1].get("role") == "user":
        return "emotion_detection"

    # 兜底：结束
    return "END"


def _llm_route_decision(state: StudentState) -> str:
    """
    LLM 决策 - A 方案

    当规则无法决策时，调用 LLM 判断下一步
    """
    state_summary = _format_state(state)

    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT.format(state_summary=state_summary)),
        HumanMessage(content="请决定下一个节点")
    ])

    content = response.content.strip()

    # 解析 LLM 输出
    match = re.search(r'next_node["\s]+[:=]["\s]+(\w+)', content)
    if match:
        return match.group(1)

    # LLM 输出无效时的兜底
    return "response"


# ========== 学情诊断节点 ==========
def learning_diagnosis_node(state: StudentState) -> dict:
    """学情诊断 - 判断 APOS 阶段"""
    import time
    messages = _get_recent_messages(state)

    response = llm.invoke([
        SystemMessage(content=LEARNING_DIAGNOSIS_PROMPT.format(
            current_topic=state.get("current_topic"),
            learning_history=json.dumps(state.get("learning_history", [])[-5:], ensure_ascii=False),
            recent_messages=messages,
            error_patterns=json.dumps(state.get("error_patterns", []), ensure_ascii=False)
        )),
        HumanMessage(content="请分析学生当前学情")
    ])

    content = response.content.strip()

    # 解析 APOS 阶段
    apos = None
    for level in ["action", "process", "object", "schema"]:
        if level in content.lower():
            apos = level
            break

    if not apos:
        apos = "action"  # 默认值

    # 根据 APOS 设置教学策略和 ZPD
    strategy_map = {
        "action": "socratic",      # 需要更多引导
        "process": "discovery",     # 探索发现
        "object": "direct",        # 可以直接讲解
        "schema": "discovery"      # 建立联系
    }

    # ZPD 映射（方案 A：APOS 直接映射）
    zpd_map = {
        "action": (0.3, 0.6),   # 基础阶段，需要更多支架
        "process": (0.5, 0.8),  # 理解过程，可适度挑战
        "object": (0.7, 0.9),   # 抽象对象，可接受难题
        "schema": (0.8, 1.0),   # 图式阶段，接近完全掌握
    }

    zpd_min, zpd_max = zpd_map.get(apos, (0.3, 0.6))

    # 基于 SOLO 理论的知识点掌握度推断（简单版）
    # SOLO 水平越高，知识点掌握度越高
    solo_to_mastery = {
        "action": 0.3,     # Uni-structural
        "process": 0.5,    # Multi-structural
        "object": 0.7,     # Relational
        "schema": 0.9,     # Extended abstract
    }
    mastery = solo_to_mastery.get(apos, 0.3)

    # 知识点掌握度更新（如果已有诊断结果，适度调整）
    current_topic = state.get("current_topic", "未知")
    knowledge_mastery = state.get("knowledge_mastery", {})
    if current_topic in knowledge_mastery:
        # 已有诊断，基于表现微调（±0.1）
        old_mastery = knowledge_mastery[current_topic]
        knowledge_mastery[current_topic] = min(0.9, max(0.1, old_mastery + 0.05))
    else:
        knowledge_mastery[current_topic] = mastery

    # 薄弱知识点（低于阈值）
    weak_points = [k for k, v in knowledge_mastery.items() if v < 0.4]

    # 核心素养能力更新（基于题目类型，简化版）
    math_abilities = state.get("math_abilities", {
        "数学抽象": 0.0, "逻辑推理": 0.0, "数学建模": 0.0,
        "直观想象": 0.0, "数学运算": 0.0, "数据分析": 0.0,
    })
    # TODO: 后续根据题目类型细粒度更新

    # 记录诊断到学习历史
    learning_history = state.get("learning_history", [])
    student_question = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""
    learning_history.append({
        "timestamp": time.time(),
        "type": "diagnosis",
        "apos_level": apos,
        "question": student_question,
        "knowledge_mastery": knowledge_mastery.get(current_topic, 0.0),
    })

    # ========== 初始化 APOS 追踪 ==========
    apos_tracking = state.get("apos_tracking", {})
    if current_topic not in apos_tracking:
        apos_tracking[current_topic] = {
            "level": apos,
            "consecutive_correct": 0,
            "consecutive_errors": 0,
            "last_practice": time.time(),
            "evidence": [],
            "mastered_at": None
        }
        # 首次诊断记录证据
        apos_tracking[current_topic]["evidence"].append({
            "timestamp": time.time(),
            "type": "initial_diagnosis",
            "from_level": None,
            "to_level": apos,
            "confidence": 1.0,
            "description": "初始诊断"
        })

    return {
        "apos_level": apos,
        "apos_tracking": apos_tracking,  # 新 APOS 追踪结构
        "teaching_strategy": strategy_map.get(apos, "socratic"),
        "zpd_min": zpd_min,
        "zpd_max": zpd_max,
        "knowledge_mastery": knowledge_mastery,
        "weak_points": weak_points,
        "math_abilities": math_abilities,
        "learning_history": learning_history,
        "next_node": "heuristic_teaching",
        "node_history": state.get("node_history", []) + ["learning_diagnosis"]
    }


# ========== 启发讲授节点 ==========
def heuristic_teaching_node(state: StudentState) -> dict:
    """启发讲授 - 生成苏格拉底式递进问题"""
    messages = _get_recent_messages(state, n=2)

    # 获取问题序列状态
    question_sequence = state.get("question_sequence", [])
    current_index = state.get("current_question_index", 0)

    response = llm.invoke([
        SystemMessage(content=HEURISTIC_TEACHING_PROMPT.format(
            current_topic=state.get("current_topic"),
            apos_level=state.get("apos_level"),
            zpd_min=state.get("zpd_min"),
            zpd_max=state.get("zpd_max"),
            hints_given=json.dumps(state.get("hints_given", []), ensure_ascii=False),
            recent_response=messages,
            question_sequence=json.dumps(question_sequence, ensure_ascii=False),
            current_question_index=current_index
        )),
        HumanMessage(content="请生成启发式问题")
    ])

    content = response.content.strip()

    # 解析工具调用（如果有）
    tool_match = re.search(r'"pending_tool"\s*:\s*"(\w+)"', content)
    params_match = re.search(r'"tool_params"\s*:\s*(\{[^}]+\})', content)

    pending_tool = tool_match.group(1) if tool_match else None
    try:
        tool_params = json.loads(params_match.group(1)) if params_match else None
    except (json.JSONDecodeError, AttributeError):
        tool_params = None

    # 提取生成的问题
    clean_content = _extract_clean_response(content)
    question = _extract_clean_question(clean_content)

    # 如果没有生成问题，且有问题序列，继续下一个
    if not question and question_sequence and current_index < len(question_sequence):
        question = question_sequence[current_index]
        current_index += 1

    # 更新问题序列状态
    new_sequence = question_sequence.copy()
    new_index = current_index

    return {
        "pending_tool": pending_tool,
        "tool_params": tool_params,
        "current_question": question,
        "question_sequence": new_sequence,
        "current_question_index": new_index,
        "hints_given": state.get("hints_given", []) + ([question] if question else []),
        "next_node": "tool_execution" if pending_tool else "response",
        "node_history": state.get("node_history", []) + ["heuristic_teaching"]
    }


def _extract_clean_question(content: str) -> str:
    """
    从 MiniMax 回复中提取真正的启发式问题
    策略：找到所有以问号结尾的句子，取第一个
    """
    import re
    # 移除 <think>... 块（贪婪模式，匹配到最后一次出现）
    content = re.sub(r'<think>[\s\S]*</think>', '', content)

    # 移除内部推理前缀（更全面的列表）
    internal_prefixes = [
        "用户要求", "用户请求", "让我分析", "我需要：", "根据当前",
        "首先，", "然后，", "接着，", "你需要", "我想：",
        "回复结构", "核心内容", "互动引导", "肯定+",
        "用户的问题是", "我理解", "我理解您", "作为AI",
    ]
    for prefix in internal_prefixes:
        if content.startswith(prefix):
            content = content[len(prefix):].strip()
            # 处理中间衔接词
            if content.startswith("：") or content.startswith(","):
                content = content[1:].strip()

    # 找所有以问号结尾的句子
    sentences = re.split(r'[。\n]', content)
    questions = []

    for sent in sentences:
        sent = sent.strip()
        if '？' in sent or '?' in sent:
            # 清理句子，去除可能的思考前缀
            for prefix in internal_prefixes:
                if sent.startswith(prefix):
                    sent = sent[len(prefix):].strip()
                    break
            # 跳过纯内部推理句式
            skip_patterns = [
                r'^分析[：:]\s*$',
                r'^回复[：:]\s*$',
                r'^核心[：:]\s*$',
                r'^问题[：:]\s*$',
            ]
            if any(re.match(p, sent) for p in skip_patterns):
                continue
            if len(sent) > 3 and not sent.startswith("..."):
                questions.append(sent)

    # 如果没找到问句，尝试找第一个有效的问句模式
    if not questions:
        # 匹配问句模式：包含疑问词但以其他标点结尾
        question_patterns = [r'什么', r'怎么', r'为什么', r'如何', r'是不是', r'能否']
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 5 and any(re.search(p, sent) for p in question_patterns):
                # 排除推理句
                if not any(sent.startswith(p) for p in internal_prefixes):
                    questions.append(sent)
                    break

    return questions[0] if questions else ""


def _extract_clean_response(content: str) -> str:
    """
    从 MiniMax 回复中提取真正有用的回复内容
    策略：移除内部推理段落，保留实质内容
    """
    import re
    # 移除 <think>... 块（贪婪模式，匹配到最后一次出现）
    content = re.sub(r'<think>[\s\S]*</think>', '', content)

    lines = content.split("\n")
    cleaned_lines = []

    skip_until_content = True  # 跳过开头的推理部分
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 如果还没找到正文，检查这一行是否应该跳过
        if skip_until_content:
            skip_patterns = [
                r'^让我分析',
                r'^用户请求',
                r'^用户希望',
                r'^我需要：',
                r'^根据当前',
                r'^回复结构',
                r'^首先，',
                r'^然后，',
                r'^接着，',
                r'^你需要',
                r'^肯定\+',
                r'^核心内容',
                r'^互动引导',
                r'^用户是',
                r'^当前情境',
                r'^我理解',
                r'^让我生成',
                r'^需要：',
                r'^需要为他',
                r'^需要为它',
                r'^设计思路',
                r'^- ',  # 跳过无意义的列表项
            ]
            should_skip = any(re.match(p, line) for p in skip_patterns)
            if should_skip:
                continue
            # 发现实质性内容，开始保留
            skip_until_content = False

        # 跳过包含内部推理关键词的行（但保留正文）
        internal_keywords = [
            "我需要：", "根据当前上下文", "回复结构：", "我需要",
            "让我生成", "用户是数学老师", "用户想让我", "当前情境",
            "设计思路", "需要为他", "需要为它", "用户希望",
            "当前话题", "APOS", "ZPD", "支架问题类型", "启发式",
            "让我来生成", "我可以", "下面我", "我将",
        ]
        if any(kw in line for kw in internal_keywords):
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    # 移除多余空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


# ========== 问题解决节点 ==========
def problem_solving_node(state: StudentState) -> dict:
    """问题解决 - ReAct 推理"""

    # 获取当前知识点的解题步骤模板
    current_topic = state.get("current_topic", "未知")
    topic_template = _get_topic_template(current_topic)

    # 获取已给出的提示，避免重复
    hints_given = state.get("hints_given", [])
    remaining_steps = [s for s in topic_template.get("steps", []) if s not in hints_given]

    response = llm.invoke([
        SystemMessage(content=PROBLEM_SOLVING_PROMPT.format(
            current_topic=current_topic,
            apos_level=state.get("apos_level"),
            zpd_min=state.get("zpd_min"),
            zpd_max=state.get("zpd_max"),
            knowledge_mastery=state.get("knowledge_mastery", {}),
            hints_given=hints_given,
            student_question=state.get("messages", [{}])[-1].get("content", ""),
            topic_steps=remaining_steps if remaining_steps else topic_template.get("steps", [])
        )),
        HumanMessage(content="请生成解题提示")
    ])

    content = response.content.strip()

    # 清理 thinking 内容
    clean_content = _extract_clean_response(content)

    # 提取提示
    lines = clean_content.split("\n")
    hint_lines = []

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # 跳过描述性文字
        if any(marker in line for marker in ["用户", "我想", "让我", "根据", "作为", "你需要", "我需要", "首先", "然后", "接着"]):
            continue
        hint_lines.append(line)
        if len(hint_lines) >= 3:
            break

    hint = " ".join(hint_lines[:2]) if hint_lines else content[:200]

    # 工具调用（如果有）
    pending_tool = None
    tool_params = None
    for tool in topic_template.get("related_tools", []):
        if tool in content.lower():
            pending_tool = tool
            if tool == "render_graph":
                tool_params = {"func": "x**2", "x_range": [-3, 3], "highlight_points": []}
            break

    return {
        "current_question": hint,
        "pending_tool": pending_tool,
        "tool_params": tool_params,
        "next_node": "tool_execution" if pending_tool else "response",
        "node_history": state.get("node_history", []) + ["problem_solving"]
    }


def _get_topic_template(topic: str) -> dict:
    """获取知识点的解题步骤模板"""
    import json
    import os

    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "knowledge", "解题步骤模板.json"
    )

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            templates = json.load(f)
        return templates.get(topic, {"steps": [], "related_tools": [], "core_abilities": []})
    except:
        return {"steps": [], "related_tools": [], "core_abilities": []}


# ========== 情绪检测节点 ==========
def emotion_detection_node(state: StudentState) -> dict:
    """
    情绪检测 - 识别并响应情绪

    规则 4（情绪后路由）:
    - frustrated AND motivation < 0.4 → heuristic_teaching（降难度，鼓励模式）
    - confident OR excited → problem_solving（趁热打铁）
    - ELSE → heuristic_teaching
    """
    recent = _get_recent_messages(state, n=1)

    response = llm.invoke([
        SystemMessage(content=EMOTION_DETECTION_PROMPT.format(
            recent_message=recent,
            current_emotion=state.get("emotion", "neutral"),
            motivation_level=state.get("motivation_level", 0.7),
            consecutive_errors=state.get("consecutive_errors", 0)
        )),
        HumanMessage(content="请分析学生情绪和动机")
    ])

    content = response.content.strip()

    # 解析情绪
    emotion = "neutral"
    for e in ["frustrated", "confused", "confident", "excited"]:
        if e in content.lower():
            emotion = e
            break

    # 解析动机
    motivation = state.get("motivation_level", 0.7)
    if "动机" in content or "motivation" in content.lower():
        match = re.search(r'0?\.(\d+)', content)
        if match:
            motivation = float(f"0.{match.group(1)}")

    # 根据情绪调整动机
    if emotion == "frustrated":
        motivation = max(0.3, motivation - 0.1)
    elif emotion == "excited" or emotion == "confident":
        motivation = min(1.0, motivation + 0.1)

    # 规则 4: 情绪检测后的路由
    if emotion == "frustrated" and motivation < 0.4:
        # 挫败感 + 动机低 → 降难度，鼓励模式
        next_node = "heuristic_teaching"
        teaching_strategy = "socratic"  # 温和引导
    elif emotion == "confident" or emotion == "excited":
        # 自信/兴奋 → 趁热打铁，推挑战题
        next_node = "problem_solving"
        teaching_strategy = state.get("teaching_strategy", "discovery")
    else:
        # 其他情况 → 启发讲授
        next_node = "heuristic_teaching"
        teaching_strategy = state.get("teaching_strategy", "socratic")

    # 检查 APOS 降阶（基于学情追踪）
    topic = state.get("current_topic", "未知")
    topic_state = state.get("apos_tracking", {}).get(topic, {})
    current_level = topic_state.get("level", "action")
    consecutive_errors = topic_state.get("consecutive_errors", 0)

    # 降阶检测（仅 Process/Object 阶段）
    if current_level in ("process", "object"):
        student_answer = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""
        degrade_result = detect_degradation(student_answer, current_level, consecutive_errors)

        if degrade_result["degrade"]:
            next_node = "heuristic_teaching"  # 降阶后引导
            teaching_strategy = "socratic"

            # 更新 apos_tracking
            apos_tracking = state.get("apos_tracking", {})
            if topic in apos_tracking:
                apos_tracking[topic]["level"] = degrade_result["new_level"]
                apos_tracking[topic]["consecutive_errors"] = 0  # 重置错误计数
                apos_tracking[topic]["evidence"].append({
                    "timestamp": time.time(),
                    "type": "degradation",
                    "from_level": current_level,
                    "to_level": degrade_result["new_level"],
                    "reason": degrade_result["reason"],
                    "description": degrade_result["description"]
                })

    return {
        "emotion": emotion,
        "motivation_level": motivation,
        "teaching_strategy": teaching_strategy,
        "next_node": next_node,
        "node_history": state.get("node_history", []) + ["emotion_detection"]
    }


# ========== 工具执行节点 ==========
def tool_execution_node(state: StudentState) -> dict:
    """工具执行 - 调用 execute_tool 生成渲染数据"""
    from .graph import execute_tool

    pending_tool = state.get("pending_tool")
    tool_params = state.get("tool_params") or {}

    if not pending_tool:
        return {
            "tool_result": None,
            "next_node": "response",
            "node_history": state.get("node_history", []) + ["tool_execution"]
        }

    # 使用 execute_tool 生成渲染数据
    result = execute_tool(pending_tool, tool_params)
    result["tool"] = pending_tool
    result["params"] = tool_params
    result["success"] = True

    return {
        "tool_result": result,
        "pending_tool": None,  # 清空待执行工具
        "tool_params": None,
        "next_node": "response",
        "node_history": state.get("node_history", []) + ["tool_execution"]
    }


# ========== 响应节点 ==========
def response_node(state: StudentState) -> dict:
    """整合响应 - 生成最终回复 + APOS 状态更新"""
    messages = _get_recent_messages(state, n=3)

    response = llm.invoke([
        SystemMessage(content=RESPONSE_PROMPT.format(
            current_topic=state.get("current_topic"),
            apos_level=state.get("apos_level") or "unknown",
            student_question=messages,
            current_question=state.get("current_question") or "（首次提问）",
            emotion=state.get("emotion", "neutral")
        )),
        HumanMessage(content="请生成回复")
    ])

    ai_message = response.content.strip()

    # 清理 thinking 内容
    ai_message = _extract_clean_response(ai_message)

    # 添加消息到历史
    new_messages = state.get("messages", []) + [
        Message(role="assistant", content=ai_message, timestamp=time.time())
    ]

    # ========== APOS 升阶检测 ==========
    topic = state.get("current_topic", "未知")
    topic_state = state.get("apos_tracking", {}).get(topic, {})
    current_level = topic_state.get("level", "action")

    # 获取学生最新回答
    student_answer = ""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            student_answer = msg.get("content", "")
            break

    # 检测升阶
    transition_result = detect_level_transition(student_answer, current_level, topic)

    # 更新 apos_tracking
    apos_tracking = state.get("apos_tracking", {})
    if topic not in apos_tracking:
        apos_tracking[topic] = {
            "level": "action",
            "consecutive_correct": 0,
            "consecutive_errors": 0,
            "last_practice": time.time(),
            "evidence": [],
            "mastered_at": None
        }

    if transition_result["transition"]:
        # 触发升阶
        old_level = current_level
        new_level = transition_result["new_level"]
        apos_tracking[topic]["level"] = new_level
        apos_tracking[topic]["consecutive_correct"] = 0  # 重置连续正确
        apos_tracking[topic]["evidence"].append({
            "timestamp": time.time(),
            "type": transition_result["evidence"]["type"],
            "from_level": old_level,
            "to_level": new_level,
            "confidence": transition_result["confidence"],
            "description": transition_result["evidence"].get("description", "")
        })

        if new_level == "schema":
            apos_tracking[topic]["mastered_at"] = time.time()

    # 更新连续正确/错误计数
    # 注意：这里需要根据学生回答的正确性来判断
    # 简化版：假设学生回答了就算一次尝试
    if current_level != "schema":  # Schema 不再累积计数
        # 检测是否"正确"（升阶检测通过就算进步）
        if transition_result["transition"]:
            apos_tracking[topic]["consecutive_correct"] += 1
            apos_tracking[topic]["consecutive_errors"] = 0  # 重置错误计数
        else:
            # 未触发升阶，但不一定是错误，只增加错误计数
            apos_tracking[topic]["consecutive_errors"] += 1

    # 检查 Schema 完成分流
    schema_completed = False
    next_action = "END"
    if apos_tracking[topic].get("level") == "schema" and not state.get("schema_completed"):
        schema_completed = True
        next_action = "schema_choice"  # 暂停等待学生选择

    return {
        "messages": new_messages,
        "apos_level": state.get("apos_level"),  # 保留旧字段
        "apos_tracking": apos_tracking,  # 新 APOS 追踪结构
        "knowledge_mastery": state.get("knowledge_mastery"),
        "learning_history": state.get("learning_history"),
        "schema_completed": schema_completed,
        "next_node": next_action,
        "node_history": state.get("node_history", []) + ["response"]
    }


# ========== 节点映射 ==========
NODES = {
    "supervisor": supervisor_node,
    "learning_diagnosis": learning_diagnosis_node,
    "heuristic_teaching": heuristic_teaching_node,
    "problem_solving": problem_solving_node,
    "emotion_detection": emotion_detection_node,
    "tool_execution": tool_execution_node,
    "response": response_node,
}