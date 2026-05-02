"""
简单的RAG体验脚本（无需启动服务器）
使用TF-IDF + 语义相似度进行知识检索
"""

import os
import re
import math
from collections import Counter

# 读取知识库
def read_knowledge_files():
    """读取所有知识库markdown文件"""
    knowledge_dir = "d:/VSwork/Edu_Agent/knowledge/第一章_集合与常用逻辑用语"

    files_content = {}
    for filename in os.listdir(knowledge_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(knowledge_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                files_content[filename] = f.read()

    return files_content

def preprocess_text(text):
    """简单的文本预处理"""
    # 移除markdown格式符号
    text = re.sub(r'#+ ', '', text)  # 移除标题符号
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 移除链接
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # 移除粗体
    text = re.sub(r'\$([^$]+)\$', r'\1', text)  # 保留LaTeX内容但移除$符号
    return text

def tokenize(text):
    """简单分词"""
    # 简单的中文字符分词 + 英文单词
    chinese_chars = re.findall(r'[一-鿿]+', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    math_expressions = re.findall(r'[A-Za-z0-9^{}<>=]+', text)

    tokens = []
    for chars in chinese_chars:
        # 简单的2-gram分词
        for i in range(len(chars) - 1):
            tokens.append(chars[i:i+2])
        tokens.append(chars)  # 单字也保留

    tokens.extend(english_words)
    tokens.extend(math_expressions)

    return tokens

def compute_tf(tokens):
    """计算词频"""
    counter = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counter.items()}

def compute_idf(corpus):
    """计算逆文档频率"""
    num_docs = len(corpus)
    idf = {}
    all_words = set()
    for tokens in corpus:
        all_words.update(tokens.keys())

    for word in all_words:
        doc_count = sum(1 for tokens in corpus if word in tokens)
        idf[word] = math.log(num_docs / (doc_count + 1)) + 1

    return idf

def compute_tfidf(tokens, idf):
    """计算TF-IDF向量"""
    tf = compute_tf(tokens)
    return {word: tf_val * idf.get(word, 0) for word, tf_val in tf.items()}

def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    common_words = set(vec1.keys()) & set(vec2.keys())
    if not common_words:
        return 0

    dot_product = sum(vec1[word] * vec2[word] for word in common_words)
    norm1 = math.sqrt(sum(v**2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v**2 for v in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot_product / (norm1 * norm2)

def search_knowledge(query, files_content, top_k=3):
    """搜索最相关的知识库内容"""
    # 分词和处理
    query_tokens = tokenize(preprocess_text(query))
    query_tfidf = compute_tfidf(query_tokens, {})

    # 对每个文档计算TF-IDF和相似度
    results = []

    # 先计算所有文档的IDF
    corpus = []
    for filename, content in files_content.items():
        # 按段落分割
        sections = content.split('\n\n')
        for section in sections:
            if len(section.strip()) > 20:  # 过滤太短的段落
                section_tokens = tokenize(preprocess_text(section))
                if section_tokens:
                    corpus.append(compute_tf(section_tokens))

    idf = compute_idf(corpus)
    query_tfidf = compute_tfidf(query_tokens, idf)

    # 计算每个文档的相似度
    for filename, content in files_content.items():
        sections = content.split('\n\n')
        for i, section in enumerate(sections):
            if len(section.strip()) > 20:
                section_tokens = tokenize(preprocess_text(section))
                section_tfidf = compute_tfidf(section_tokens, idf)
                similarity = cosine_similarity(query_tfidf, section_tfidf)

                if similarity > 0.1:  # 阈值
                    results.append({
                        'filename': filename,
                        'section_id': i,
                        'content': section.strip()[:300] + '...' if len(section) > 300 else section.strip(),
                        'similarity': similarity
                    })

    # 排序并返回top_k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("[Math Knowledge Base] RAG Demo")
    print("=" * 60)

    # 加载知识库
    print("\n📖 加载知识库...")
    files_content = read_knowledge_files()
    print(f"   已加载 {len(files_content)} 个文件")

    # 示例问题
    example_questions = [
        "什么是集合？",
        "子集和真子集有什么区别？",
        "如何求两个集合的交集？",
        "什么是充分条件？",
        "全称量词和存在量词是什么？"
    ]

    print("\n📝 示例问题：")
    for i, q in enumerate(example_questions, 1):
        print(f"   {i}. {q}")

    print("\n" + "-" * 60)
    print("Auto-testing with predefined questions...")
    print("-" * 60)

    # Auto-test with predefined questions
    test_questions = [
        "什么是集合？",
        "子集和真子集有什么区别？",
        "如何求两个集合的交集？",
        "什么是充分条件？",
        "全称量词和存在量词是什么？"
    ]

    for query in test_questions:
        print()
        print(f"Question: {query}")
        print("-" * 40)

        results = search_knowledge(query, files_content, top_k=2)

        if results:
            print(f"Found {len(results)} related results:\n")
            for i, result in enumerate(results, 1):
                print(f"[Result {i}] (Similarity: {result['similarity']:.3f})")
                print(f"Source: {result['filename']}")
                print(result['content'][:300])
                print()
        else:
            print("No related content found")
        print("=" * 60)

if __name__ == "__main__":
    main()
