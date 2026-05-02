import re

content = """学生刚刚问"什么是奇偶性"，这是一个非常基础的概念性问题。根据 APOS 理论，学生当前处于 action 阶段，需要通过具体操作来理解概念。 根据 ZPD 范围 0.3 - 0.6，这是一个相对较低的范围，问题要更具体、步子更小，多给具体例子。
</think>
没关系，我们慢慢来！奇偶性其实是个很有意思的概念。"""

# Current regex (non-greedy)
result1 = re.sub(r'<think>[\s\S]*?</think>', '', content)
print("Current (non-greedy):")
print(result1)
print()

# Fixed regex (greedy)
result2 = re.sub(r'<think>[\s\S]*</think>', '', content)
print("Fixed (greedy):")
print(result2)

with open('d:/VSwork/Edu_Agent/test_regex.txt', 'w', encoding='utf-8') as f:
    f.write("Original:\n" + content + "\n\n")
    f.write("Current (non-greedy):\n" + result1 + "\n\n")
    f.write("Fixed (greedy):\n" + result2)