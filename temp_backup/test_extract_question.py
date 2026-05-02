# -*- coding: utf-8 -*-
"""测试 _extract_clean_question 函数"""

import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.nodes import _extract_clean_question

# 测试用例
test_cases = [
    # 用例1: 用户遇到的真实问题
    """用户要求我生成一个苏格拉底式支架问题。让我分析当前情况：
1. **当前话题**：奇偶性
2. **APOS 阶段**：action

**回复结构**：
- 肯定+
- 核心内容
- 互动引导

首先，你需要理解奇函数的核心特征。奇函数有什么特点呢？想想 f(-x) 和 -f(x) 的关系。
你能观察一下 y=x 这个函数图像吗？它有什么特殊的地方？""",

    # 用例2: 典型内部推理输出
    """用户请求生成一个苏格拉底式提问。让我分析：

根据当前 APOS 阶段（action），学生处于操作阶段，需要具体例子引导。

**核心内容**：
你观察过生活中的对称现象吗？比如蝴蝶的翅膀、人的左右手？

**互动引导**：
你能举出一个生活中对称的例子吗？""",

    # 用例3: 正常但有过多前缀
    """让我分析当前情况：首先，让我们从具体的例子开始。你知道 y=x 这个函数吗？
它的图像有什么特点呢？试着画一画，你会发现什么？
当你把 x 换成 -x 时，y 会变成什么呢？""",
]

print("=" * 60)
print("测试 _extract_clean_question 函数")
print("=" * 60)

for i, case in enumerate(test_cases, 1):
    print(f"\n【用例 {i}】")
    print("-" * 40)
    print("输入内容:")
    print(case[:100] + "..." if len(case) > 100 else case)
    print("-" * 40)
    result = _extract_clean_question(case)
    print(f"提取结果: {result}")
    print("=" * 60)