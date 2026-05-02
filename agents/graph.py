"""
LangGraph StateGraph 定义
Phase 1: 单实例协作架构
"""

from langgraph.graph import StateGraph, END
from .state import StudentState, create_initial_state
from .nodes import NODES


def _route_edge(state: StudentState) -> str:
    """路由边 - 根据 next_node 决定下一个节点"""
    next_node = state.get("next_node", "supervisor")
    # 如果是 END 字符串，返回 "__end__" 字符串与字典映射对应
    if next_node == "END":
        return "__end__"
    return next_node


def create_graph():
    """创建 StateGraph"""
    graph = StateGraph(StudentState)

    # 添加节点
    for node_name, node_func in NODES.items():
        graph.add_node(node_name, node_func)

    # 设置入口点
    graph.set_entry_point("supervisor")

    # 添加条件边 - 由 Supervisor 的 next_node 决定路由
    graph.add_conditional_edges(
        "supervisor",
        _route_edge,
        {
            "learning_diagnosis": "learning_diagnosis",
            "heuristic_teaching": "heuristic_teaching",
            "problem_solving": "problem_solving",
            "emotion_detection": "emotion_detection",
            "tool_execution": "tool_execution",
            "response": "response",
            "__end__": END,
        }
    )

    # 其他节点的边 - 都回到 Supervisor
    for node_name in NODES.keys():
        if node_name != "supervisor":
            graph.add_edge(node_name, "supervisor")

    return graph


# 创建全局图实例
app = create_graph().compile()


# ========== 对话接口 ==========
def chat(message: str, topic: str = "奇偶性", history: list = None) -> dict:
    """
    对话接口

    Args:
        message: 学生的问题/回答
        topic: 当前知识点
        history: 可选的对话历史（用于恢复会话）

    Returns:
        dict: {
            "response": str,  # AI 回复
            "tool_result": dict,  # 工具执行结果（如果有）
            "state": dict  # 当前状态快照
        }
    """
    import time

    # 初始化或恢复状态
    if history is None:
        state = create_initial_state(topic)
    else:
        state = history[-1] if history else create_initial_state(topic)

    # 添加用户消息
    state["messages"] = state.get("messages", []) + [
        {"role": "user", "content": message, "timestamp": time.time()}
    ]
    state["next_node"] = "supervisor"

    # 运行图
    final_state = None
    response_state = None  # Track the state with actual response
    max_iterations = 10  # 防止无限循环
    iteration_count = 0

    for event in app.stream(state):
        final_state = event
        last_node = list(event.keys())[0] if event else None
        iteration_count += 1

        # Track state with messages (from response node)
        if isinstance(event, dict) and last_node in event:
            if event[last_node].get("messages"):
                response_state = event[last_node]

        # 防止无限循环
        if iteration_count >= max_iterations:
            break

        # 如果到达 END，停止
        if last_node == "__end__" or last_node == END:
            break

    # 提取结果 - use response_state if available, otherwise fall back to final_state
    if response_state:
        state_data = response_state
    elif final_state and isinstance(final_state, dict):
        if last_node and last_node in final_state:
            state_data = final_state[last_node]
        else:
            state_data = final_state
    else:
        state_data = state

    return {
        "response": state_data.get("messages", [{}])[-1].get("content", "") if state_data else "",
        "tool_result": state_data.get("tool_result") if state_data else None,
        "state": state_data if state_data else state,
    }


# ========== 工具调用接口 ==========
def execute_tool(tool_name: str, params: dict) -> dict:
    """
    直接调用工具（用于前端渲染）

    Args:
        tool_name: 工具名称
        params: 工具参数

    Returns:
        dict: 渲染数据，用于前端组件
    """
    import uuid

    # 生成唯一的容器 ID
    container_id = f"geogebra-{uuid.uuid4().hex[:8]}"

    # 基础绘图工具
    if tool_name == "render_graph":
        return {
            "type": "graph",
            "tool": "render_graph",
            "func": params.get("func", "x**2"),
            "x_range": params.get("x_range", [-3, 3]),
            "y_range": params.get("y_range", [-3, 3]),
            "highlight_points": params.get("highlight_points", []),
            "show_axis": True,
            "show_grid": True,
        }

    elif tool_name == "animate":
        return {
            "type": "animation",
            "tool": "animate",
            "from": params.get("from"),
            "to": params.get("to"),
            "duration": params.get("duration", 1000),
            "easing": "ease-in-out",
        }

    elif tool_name == "show_card":
        return {
            "type": "card",
            "tool": "show_card",
            "card_type": params.get("card_type", "definition"),
            "title": params.get("title", ""),
            "content": params.get("content", ""),
        }

    elif tool_name == "show_derivation":
        return {
            "type": "derivation",
            "tool": "show_derivation",
            "expr": params.get("expr", ""),
            "steps": params.get("steps", []),
        }

    # GeoGebra 工具
    elif tool_name == "geogebra_function":
        return {
            "type": "geogebra",
            "tool": "geogebra_function",
            "render_data": {
                "type": "geogebra_function",
                "func": params.get("func", "x^2"),
                "x_range": params.get("x_range", [-5, 5]),
                "y_range": params.get("y_range", [-5, 5]),
                "editable_params": params.get("editable_params", []),
                "default_values": params.get("default_values", {}),
                "annotations": params.get("annotations", []),
                "container_id": container_id,
            }
        }

    elif tool_name == "geogebra_geometry":
        return {
            "type": "geogebra",
            "tool": "geogebra_geometry",
            "render_data": {
                "type": "geogebra_geometry",
                "figure": params.get("figure", "triangle"),
                "vertices": params.get("vertices", []),
                "show_labels": params.get("show_labels", True),
                "show_angles": params.get("show_angles", False),
                "draggable": params.get("draggable", True),
                "container_id": container_id,
            }
        }

    elif tool_name == "geogebra_venn":
        return {
            "type": "geogebra",
            "tool": "geogebra_venn",
            "render_data": {
                "type": "geogebra_venn",
                "sets": params.get("sets", []),
                "operation": params.get("operation", "intersection"),
                "highlight_result": params.get("highlight_result", True),
                "container_id": container_id,
            }
        }

    elif tool_name == "geogebra_interval":
        return {
            "type": "geogebra",
            "tool": "geogebra_interval",
            "render_data": {
                "type": "geogebra_interval",
                "intervals": params.get("intervals", []),
                "operation": params.get("operation", "union"),
                "container_id": container_id,
            }
        }

    return {"type": "unknown", "error": f"Unknown tool: {tool_name}"}
