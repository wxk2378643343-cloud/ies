# 基于注意力机制的用户兴趣演化分析与预测系统

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | Python + FastAPI |
| 数据库 | SQLite + SQLAlchemy |
| ML模型 | PyTorch（LSTM + Attention） |
| 通信 | RESTful API + WebSocket（实时推荐） |

---

## 系统架构

```
浏览器
  │
  ├── 普通用户界面（内容浏览、推荐展示）
  └── 管理员界面（数据看板、模型监控）
        │
        ▼
   前端 Vue 3
        │  REST API
        ▼
   后端 FastAPI
   ├── 用户模块      /api/user
   ├── 内容模块      /api/content
   ├── 行为日志模块  /api/behavior
   ├── 推荐模块      /api/recommend
   └── 管理员模块    /api/admin
        │
        ├──────────────────┐
        ▼                  ▼
   SQLite 数据库       ML 模块（PyTorch）
   ├── users           ├── 数据预处理
   ├── contents        ├── LSTM + Attention 模型
   ├── behaviors       ├── 模型训练 / 增量更新
   ├── interest_tags   └── 预测推理（兴趣演化）
   └── model_results
```

---

## 数据库核心表

| 表名 | 说明 |
|------|------|
| users | 用户信息、角色（普通/管理员） |
| contents | 平台内容（文章/视频等） |
| behaviors | 用户行为日志（点击、收藏、停留时长） |
| interest_tags | 用户兴趣标签及权重 |
| model_results | LSTM预测结果及时间戳 |

---

## ML 模型设计

```
用户行为序列（时间序列）
        │
        ▼
   Embedding 层
        │
        ▼
   LSTM 层（捕捉时序兴趣变化）
        │
        ▼
   Attention 层（加权近期重要行为）
        │
        ▼
   兴趣向量输出
        │
        ▼
   Top-N 内容推荐
```

---

## 功能模块

### 普通用户
- 注册/登录
- 浏览内容（行为自动记录）
- 查看个性化推荐
- 个人兴趣标签展示

### 平台管理员
- 用户管理
- 内容管理
- 用户行为数据看板
- 模型训练触发与效果监控

---

## 开发阶段规划

| 阶段 | 内容 |
|------|------|
| 1 | 数据库建表 + 用户认证（注册/登录） |
| 2 | 内容模块 + 行为日志采集 |
| 3 | LSTM+Attention 模型训练与推理 |
| 4 | 推荐接口对接前端 |
| 5 | 管理员看板 + 模型监控 |
| 6 | 功能测试 + 性能测试 + 文档撰写 |
