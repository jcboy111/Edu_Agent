# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')
from agents.nodes import _extract_clean_question

test_cases = [
    "用户要求我生成一个苏格拉底式支架问题。让我分析当前情况：\n首先，你需要理解奇函数的核心特征。奇函数有什么特点呢？想想 f(-x) 和 -f(x) 的关系。\n你能观察一下 y=x 这个函数图像吗？",

    "用户请求生成一个苏格拉底式提问。让我分析：\n你观察过生活中的对称现象吗？比如蝴蝶的翅膀、人的左右手？\n你能举出一个生活中对称的例子吗？",

    "让我分析当前情况：首先，让我们从具体的例子开始。你知道 y=x 这个函数吗？\n它的图像有什么特点呢？试着画一画，你会发现什么？\n当你把 x 换成 -x 时，y 会变成什么呢？",
]

print("=" * 60)
print("Test _extract_clean_question")
print("=" * 60)

results = []
for i, case in enumerate(test_cases, 1):
    print("\n[Test Case %d]" % i)
    print("-" * 40)
    print("Input:")
    print(case)
    print("-" * 40)
    result = _extract_clean_question(case)
    print("Output: " + result)
    results.append(result)

print("\n" + "=" * 60)
print("Summary:")
for i, r in enumerate(results, 1):
    print("Case %d: %s" % (i, r))

with open('d:/VSwork/Edu_Agent/test_results.txt', 'w', encoding='utf-8') as f:
    f.write("Test Results\n")
    f.write("=" * 60 + "\n\n")
    for i, case in enumerate(test_cases, 1):
        f.write("[Test Case %d]\n" % i)
        f.write("-" * 40 + "\n")
        f.write("Input:\n%s\n" % case)
        f.write("-" * 40 + "\n")
        f.write("Output: %s\n" % results[i-1])
        f.write("=" * 60 + "\n\n")