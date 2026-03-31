# 基于注意力机制的用户兴趣演化分析与预测系统 — 实施方案

> 对应毕业设计任务书要求，结合 ARCHITECTURE.md 技术栈制定。

---

## 一、需求分析

### 1.1 普通用户需求

| 功能 | 说明 |
|------|------|
| 注册 / 登录 | 邮箱+密码，JWT 鉴权 |
| 内容浏览 | 文章列表、详情页，行为自动上报 |
| 个性化推荐 | 首页展示 Top-N 推荐内容 |
| 兴趣标签展示 | 用户个人页展示当前兴趣画像 |
| 兴趣演化趋势 | 折线图展示历史兴趣权重变化 |

### 1.2 平台管理员需求

| 功能 | 说明 |
|------|------|
| 用户管理 | 查看 / 封禁用户 |
| 内容管理 | 发布 / 下架内容，打标签 |
| 行为数据看板 | 点击 / 停留 / 收藏统计图表 |
| 模型管理 | 手动触发训练、查看损失曲线、评估指标 |

---

## 二、系统设计

### 2.1 数据库设计（SQLite + SQLAlchemy）

```sql
-- 用户表
users(id, username, email, password_hash, role, created_at)

-- 内容表
contents(id, title, body, category, tags_json, author_id, created_at, status)

-- 行为日志表
behaviors(id, user_id, content_id, action,   -- click/collect/read
          duration_sec, timestamp)

-- 兴趣标签表
interest_tags(id, user_id, tag, weight, updated_at)

-- 模型结果表
model_results(id, user_id, predicted_tags_json,
              confidence, model_version, created_at)

-- 模型训练记录表
model_train_logs(id, version, loss, accuracy,
                 precision, recall, ndcg, trained_at, note)
```

### 2.2 系统架构（三层）

```
用户层   浏览器 → Vue 3 SPA
          ↕  REST API / WebSocket
应用层   FastAPI
          ├── /api/user       注册、登录、个人信息
          ├── /api/content    内容 CRUD、搜索
          ├── /api/behavior   行为上报（埋点）
          ├── /api/recommend  Top-N 推荐
          └── /api/admin      管理员专用接口
          ↕
数据层   SQLite  ←→  ML 模块（PyTorch 离线训练 + 在线推理）
```

### 2.3 前端页面设计

| 路由 | 页面 | 角色 |
|------|------|------|
| /login  /register | 登录注册 | 所有 |
| / | 首页（推荐流） | 普通用户 |
| /content/:id | 内容详情 | 普通用户 |
| /profile | 个人中心（兴趣标签+演化图） | 普通用户 |
| /admin/dashboard | 数据看板 | 管理员 |
| /admin/users | 用户管理 | 管理员 |
| /admin/contents | 内容管理 | 管理员 |
| /admin/model | 模型训练与监控 | 管理员 |

---

## 三、ML 模型设计

### 3.1 模型结构

```
输入：用户最近 N 条行为序列（content_id, action, timestamp）
  │
  ▼
Embedding 层（content_id → 64 维向量）
  │
  ▼
LSTM 层（hidden_size=128, num_layers=2, dropout=0.2）
  │  捕捉兴趣随时间的演化规律
  ▼
Self-Attention 层（对 LSTM 各时间步加权）
  │  突出近期或高频行为的影响
  ▼
兴趣向量（128 维）
  │
  ▼
全连接 + Softmax → 预测下一个感兴趣的内容类别
```

### 3.2 训练策略

- **数据集**：从 behaviors 表提取序列，按时间排序，滑窗切分
- **损失函数**：交叉熵（分类）+ 余弦相似度正则
- **优化器**：Adam，lr=1e-3，weight decay=1e-4
- **增量更新**：每天定时任务（APScheduler）触发增量训练
- **模型版本**：每次训练生成版本号，写入 model_train_logs

### 3.3 评估指标

| 指标 | 说明 |
|------|------|
| Loss / Accuracy | 训练过程监控 |
| Precision@K / Recall@K | 推荐质量 |
| NDCG@K | 排序质量 |
| 点击率 CTR | 线上 A/B 效果（模拟） |

---

## 四、开发阶段与任务分解

### 阶段 1：基础框架搭建（数据库 + 认证）

**后端**
- [ ] `database/` SQLAlchemy 建表（5 张表）
- [ ] `backend/api/user.py` 注册、登录、JWT 中间件
- [ ] `backend/config/` 配置文件（DB路径、SECRET_KEY、跨域）

**前端**
- [ ] Vite + Vue 3 + Element Plus 初始化
- [ ] axios 封装 + token 拦截器
- [ ] 登录 / 注册页面

---

### 阶段 2：内容模块 + 行为埋点

**后端**
- [ ] `backend/api/content.py` 列表、详情、搜索接口
- [ ] `backend/api/behavior.py` 行为上报接口（点击/收藏/阅读时长）

**前端**
- [ ] 首页内容流（分页）
- [ ] 内容详情页（进入/离开自动埋点）

---

### 阶段 3：LSTM + Attention 模型

**ML 模块**
- [ ] `ml/data/` 数据预处理脚本（序列构建、归一化）
- [ ] `ml/models/lstm_attention.py` 模型定义
- [ ] `ml/training/trainer.py` 训练循环（含 TensorBoard 日志）
- [ ] `ml/evaluation/metrics.py` Precision / Recall / NDCG 计算
- [ ] `ml/utils/inference.py` 在线推理（加载最新版本模型）

**数据种子**
- [ ] `database/seeds/` 生成模拟用户行为数据（用于冷启动演示）

---

### 阶段 4：推荐接口 + 前端推荐展示

**后端**
- [ ] `backend/api/recommend.py` 调用 inference.py，返回 Top-N
- [ ] `backend/services/interest_service.py` 更新 interest_tags 表
- [ ] WebSocket 推送实时推荐更新（可选）

**前端**
- [ ] 首页推荐流接入 /api/recommend
- [ ] 个人中心：兴趣标签云 + ECharts 演化折线图

---

### 阶段 5：管理员看板 + 模型监控

**后端**
- [ ] `backend/api/admin.py` 用户列表、内容管理、看板统计
- [ ] 训练触发接口 + APScheduler 定时任务

**前端**
- [ ] 行为统计看板（ECharts 柱图 / 折线图）
- [ ] 模型训练触发按钮 + 实时损失曲线
- [ ] 模型版本对比表格

---

### 阶段 6：测试 + 文档

**测试**
- [ ] `tests/unit/` 模型精度单元测试
- [ ] `tests/integration/` API 接口集成测试（pytest）
- [ ] `tests/performance/` Locust 压测（并发用户数、响应时间）

**文档**
- [ ] `docs/api/` OpenAPI（FastAPI 自动生成）+ 补充说明
- [ ] `docs/thesis/` 论文各章节草稿

---

## 五、文件结构总览

```
ies/
├── backend/
│   ├── api/          user.py  content.py  behavior.py  recommend.py  admin.py
│   ├── config/       settings.py
│   ├── models/       orm_models.py（SQLAlchemy 表定义）
│   ├── services/     interest_service.py  scheduler.py
│   └── utils/        auth.py（JWT）  deps.py（依赖注入）
├── database/
│   ├── migrations/   alembic 脚本
│   └── seeds/        generate_mock_data.py
├── frontend/
│   └── src/
│       ├── components/  RecommendCard  InterestChart  BehaviorDashboard
│       ├── pages/       Home  ContentDetail  Profile  Admin/*
│       └── utils/       request.js  auth.js
├── ml/
│   ├── data/         preprocess.py  dataset.py
│   ├── models/       lstm_attention.py
│   ├── training/     trainer.py  scheduler_job.py
│   ├── evaluation/   metrics.py
│   └── utils/        inference.py  model_registry.py
└── tests/
    ├── unit/
    ├── integration/
    └── performance/
```

---

## 六、关键技术要点（论文写作对应）

| 论文章节 | 技术内容 |
|----------|----------|
| 需求分析 | 用户故事、用例图、功能模块划分 |
| 系统设计 | ER图、架构图、接口文档、UI原型 |
| 模型设计 | LSTM原理、Attention机制、兴趣演化建模 |
| 实现 | 核心代码片段、数据库建表、API设计 |
| 测试 | 功能测试用例、性能压测数据、模型评估指标对比 |
| 总结 | 实验结论、不足与改进方向 |

---

## 七、里程碑时间节点（参考）

| 里程碑 | 交付物 |
|--------|--------|
| M1 阶段1完成 | 可登录系统，数据库初始化脚本 |
| M2 阶段2完成 | 可浏览内容并记录行为 |
| M3 阶段3完成 | 模型可训练并输出评估指标 |
| M4 阶段4完成 | 首页显示个性化推荐 |
| M5 阶段5完成 | 管理员可查看看板并触发训练 |
| M6 阶段6完成 | 测试通过，文档齐全，论文初稿完成 |
