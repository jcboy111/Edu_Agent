# -*- coding: utf-8 -*-
"""
知识图谱模块
提供知识点查询、学习路径推荐等功能
"""
import json
import os

class KnowledgeGraph:
    def __init__(self, graph_path=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "knowledge_graph.json"
            )
        with open(graph_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_point(self, point_id: str) -> dict:
        """获取知识点详情"""
        for p in self.data.get("knowledge_points", []):
            if p["id"] == point_id:
                return p
        return None

    def get_prerequisites(self, point_id: str) -> list:
        """获取知识点的前置知识"""
        point = self.get_point(point_id)
        return point.get("prerequisites", []) if point else []

    def get_related(self, point_id: str) -> list:
        """获取相关知识点"""
        point = self.get_point(point_id)
        return point.get("related_points", []) if point else []

    def get_learning_sequence(self) -> list:
        """获取学习路径"""
        return self.data.get("learning_sequence", [])

    def get_misconceptions(self, topic: str = None) -> list:
        """获取常见错误"""
        if topic:
            return [m for m in self.data.get("common_misconceptions", [])
                    if topic in m.get("topic", "")]
        return self.data.get("common_misconceptions", [])

    def find_point_by_name(self, name: str) -> dict:
        """根据名称查找知识点"""
        for p in self.data.get("knowledge_points", []):
            if name in p.get("name", "") or name in p.get("keywords", []):
                return p
        return None

    def get_next_learning(self, learned_points: list) -> dict:
        """根据已学知识点推荐下一个学习内容"""
        sequence = self.get_learning_sequence()
        for seq in sequence:
            # 检查是否包含未学的知识点
            unlearned = [p for p in seq["points"] if p not in learned_points]
            if unlearned:
                return {
                    "step": seq["step"],
                    "topic": seq["topic"],
                    "description": seq["description"],
                    "next_points": unlearned
                }
        return None


# 全局实例
kg = KnowledgeGraph()


if __name__ == "__main__":
    # 测试
    print("=== 知识图谱测试 ===")
    print(f"章节: {kg.data['chapter']}")
    print(f"知识点数量: {len(kg.data['knowledge_points'])}")

    # 测试查询奇函数
    odd = kg.get_point("odd_function")
    print(f"\n奇函数: {odd['name']}")
    print(f"定义: {odd['definition']}")
    print(f"前置知识: {kg.get_prerequisites('odd_function')}")
    print(f"相关知识: {kg.get_related('odd_function')}")

    # 测试学习路径
    print("\n=== 学习路径 ===")
    for seq in kg.get_learning_sequence():
        print(f"Step {seq['step']}: {seq['topic']} - {seq['description']}")

    # 测试推荐
    print("\n=== 学习推荐 ===")
    next_learning = kg.get_next_learning(["function_basic", "domain", "interval"])
    print(f"已学: function_basic, domain, interval")
    print(f"推荐: {next_learning}")