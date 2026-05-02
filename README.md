# 数学AI智能体教学平台

高中数学智能辅导系统，采用苏格拉底式引导教学法。

## 功能

- 智能对话辅导：基于 WebSocket 的实时对话
- 知识图谱：第三章函数知识体系
- 苏格拉底引导：通过提问帮助学生理解概念
- 多Agent协作：学习诊断、启发式教学

## 运行

```bash
# 启动对话服务器
python simple_server.py

# 访问前端
http://127.0.0.1:5500/index.html
```

## 目录结构

```
agents/          - Agent系统核心代码
knowledge/       - 知识图谱与教材内容
docs/            - 设计文档与会话摘要
pic_resource/    - 教材图片资源
```

## 技术栈

- Python + FastAPI + WebSocket
- LangGraph Agent架构
- MiniMax API
