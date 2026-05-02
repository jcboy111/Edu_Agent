# 知识库数据库 Schema 说明

> 本文档说明当前MVP阶段使用的数据表结构。
> 后续可迁移到 MySQL/PostgreSQL/Neo4j 等数据库。

---

## 数据表总览

| 表名 | 用途 | 格式 |
|------|------|------|
| 知识点表 | 知识点元数据 | CSV → MySQL |
| 知识点关系表 | 知识点之间的关联 | CSV → Neo4j（图数据库）|
| 题目表 | 例题和习题 | CSV → MySQL |
| APOS定义表 | APOS四阶段标准定义 | CSV → MySQL |

---

## 表1：知识点表 (knowledge)

```sql
CREATE TABLE knowledge (
    knowledge_id VARCHAR(10) PRIMARY KEY,  -- 知识点唯一ID，如 K101
    chapter VARCHAR(10),                    -- 章节号，如 1.1
    name VARCHAR(100),                      -- 知识点名称
    default_apos ENUM('Action','Process','Object','Schema'),  -- 默认APOS阶段
    difficulty INT,                        -- 难度1-5
    md_file VARCHAR(100),                  -- 对应markdown文件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**说明**：
- `knowledge_id` 是主键，格式为 K + 章节号 + 序号
- `default_apos` 是学生初学该知识点时的默认阶段

---

## 表2：知识点关系表 (knowledge_relation)

```sql
CREATE TABLE knowledge_relation (
    relation_id VARCHAR(10) PRIMARY KEY,   -- 关系ID，如 R001
    source_knowledge VARCHAR(10),          -- 源知识点ID
    target_knowledge VARCHAR(10),          -- 目标知识点ID
    relation_type VARCHAR(50),             -- 关系类型
    description VARCHAR(200),             -- 关系描述
    FOREIGN KEY (source_knowledge) REFERENCES knowledge(knowledge_id),
    FOREIGN KEY (target_knowledge) REFERENCES knowledge(knowledge_id)
);
```

**关系类型说明**：

| 关系类型 | 说明 | 示例 |
|----------|------|------|
| 前置 | 学习A之前需要先学B | K102前置于K104 |
| 包含 | A知识点包含B知识点 | K104包含K105 |
| 互逆 | A和B互为逆关系 | K112互逆K113 |
| 互斥 | A和B互斥，不能同时 | K115互斥K116 |
| 相关 | A和B相关 | K108相关K109 |

---

## 表3：题目表 (question)

```sql
CREATE TABLE question (
    question_id VARCHAR(10) PRIMARY KEY,   -- 题目ID，如 Q001
    knowledge_id VARCHAR(10),              -- 关联知识点ID
    question_type ENUM('example','practice','exam'),
    difficulty INT,                        -- 难度1-5
    content TEXT,                          -- 题目内容
    answer TEXT,                           -- 答案
    geo_config TEXT,                       -- GeoGebra可视化配置（可选）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
);
```

**题目类型说明**：

| 类型 | 说明 |
|------|------|
| example | 教材例题，带详细解答 |
| practice | 练习题，可用于学生练习 |
| exam | 考试题，可用于测试 |

---

## 表4：APOS定义表 (apos_definition)

```sql
CREATE TABLE apos_definition (
    apos_id VARCHAR(10) PRIMARY KEY,       -- APOS阶段ID
    stage ENUM('Action','Process','Object','Schema'),
    description TEXT,                       -- 阶段描述
    teaching_strategy TEXT,                 -- 教学策略建议
    question_template TEXT,                -- 引导提问模板
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 后续扩展建议

### 短期扩展
1. 添加 `student_apos_progress` 表：记录学生APOS进度
2. 添加 `error_case` 表：常见错误案例

### 长期扩展
1. 迁移到 **Neo4j** 图数据库：用于构建完整知识图谱
2. 添加 `learning_path` 表：学习路径规划

---

## 文件位置

```
knowledge/
├── knowledge_graph/
│   ├── 知识点表.csv          # 当前使用CSV
│   ├── 知识点关系表.csv
│   ├── 题目表.csv
│   ├── APOS定义表.csv
│   └── 数据库Schema说明.md   # 本文档
```

---

## 变更记录

| 日期 | 变更内容 | 变更人 |
|------|----------|--------|
| 2026-04-27 | 创建数据库Schema文档 | Claude |
