# 基于注意力机制的用户兴趣演化分析与预测系统

> 毕业设计项目 · Python + Vue 3 + PyTorch（LSTM + Attention）

---

## 项目简介

本系统是一个内容推荐平台，通过记录用户的浏览、阅读、收藏等行为，利用 **LSTM + Self-Attention** 模型对用户兴趣进行时序建模，动态分析兴趣演化趋势，并向用户提供个性化内容推荐。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | Python 3.11 + FastAPI |
| 数据库 | SQLite + SQLAlchemy ORM |
| ML 模型 | PyTorch（LSTM + Self-Attention） |
| 鉴权 | JWT（python-jose + passlib/bcrypt） |
| 定时任务 | APScheduler（每日增量更新兴趣标签） |
| 测试 | pytest + Locust |

---

## 系统架构

```
浏览器
  │
  ├── 普通用户界面（内容浏览、推荐展示、兴趣演化图）
  └── 管理员界面（数据看板、模型监控）
        │
        ▼
   前端 Vue 3（Vite + Element Plus）
        │  REST API
        ▼
   后端 FastAPI
   ├── /api/user       注册、登录、个人信息
   ├── /api/content    内容 CRUD、分类、搜索
   ├── /api/behavior   行为埋点（click/read/collect）
   ├── /api/recommend  个性化推荐 + 兴趣标签 + 演化历史
   └── /api/admin      统计看板、用户/内容管理、模型训练
        │
        ├──────────────────────┐
        ▼                      ▼
   SQLite 数据库           ML 模块（PyTorch）
   ├── users               ├── 数据预处理（滑窗序列）
   ├── contents            ├── LSTM + Attention 模型
   ├── behaviors           ├── 训练 / 增量更新
   ├── interest_tags       └── 推理（兴趣演化 → 推荐）
   ├── model_results
   └── model_train_logs
```

---

## ML 模型结构

```
输入：用户最近 20 条行为序列（content_id, action_weight）
        │
  Embedding 层（content_id → 64 维向量）
        │  × action_weight（collect=3 / read=2 / click=1）
        │
  LSTM 层（hidden=128, layers=2, dropout=0.2）
        │  捕捉兴趣随时间的演化规律
        │
  Self-Attention 层（对各时间步加权，突出近期高价值行为）
        │
  兴趣向量 (128 维)
        │
  全连接 + Softmax → 类别兴趣概率分布 → Top-N 推荐
```

---

## 目录结构

```
ies/
├── README.md
├── requirements.txt          Python 依赖
├── pytest.ini                pytest 配置
├── backend/
│   ├── main.py               FastAPI 入口
│   ├── api/                  user / content / behavior / recommend / admin
│   ├── config/settings.py    全局配置（数据库路径、JWT 密钥等）
│   ├── models/orm_models.py  SQLAlchemy 表定义（6张表）
│   ├── services/             interest_service（训练触发 + 批量推理）
│   └── utils/                auth（JWT/bcrypt）、deps（依赖注入）
├── database/
│   ├── ies.db                运行时数据库（自动生成）
│   ├── migrations/           Alembic 迁移脚本（预留）
│   └── seeds/                generate_mock_data.py
├── frontend/
│   └── src/
│       ├── pages/            Login / Register / Home / Profile / admin/*
│       ├── stores/auth.js    Pinia 认证状态
│       ├── utils/request.js  axios 封装（自动附 token）
│       └── router/           路由 + 权限守卫
├── ml/
│   ├── data/                 preprocess.py / dataset.py / vocab.json
│   ├── models/               lstm_attention.py
│   ├── training/             trainer.py
│   ├── evaluation/           metrics.py（Precision/Recall/NDCG@K）
│   ├── utils/                inference.py / model_registry.py
│   └── checkpoints/          模型权重（自动生成）
├── tests/
│   ├── conftest.py           测试 DB + Token 夹具
│   ├── ies_test.db           测试数据库（自动生成）
│   ├── unit/                 test_model.py / test_metrics.py（28 个）
│   ├── integration/          test_api.py（32 个）
│   └── performance/          locustfile.py
└── docs/
    ├── design/               PLAN.md（实施方案）
    ├── api/                  README.md（接口文档）
    └── thesis/               outline.md（论文提纲）
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2. 生成测试数据

```bash
python -m database.seeds.generate_mock_data
# 生成：1 管理员 + 10 普通用户 + 32 篇内容 + 行为日志
# 管理员账号：admin@ies.com  密码：admin123
# 普通用户：user01@ies.com   密码：password123
```

### 3. 训练模型

```bash
python -m ml.training.trainer --epochs 20
```

### 4. 启动服务

```bash
# 后端（http://localhost:8000）
python -m uvicorn backend.main:app --reload

# 前端（http://localhost:5173）
cd frontend && npm run dev
```

### 5. 运行测试

```bash
python -m pytest          # 全部（60个）
python -m pytest tests/unit/         # 单元测试（28个）
python -m pytest tests/integration/  # 集成测试（32个）
```

### 6. 压测

```bash
# 需要后端运行中
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## 数据库表说明

| 表名 | 说明 |
|------|------|
| users | 用户信息、角色（user / admin） |
| contents | 平台内容（标题、正文、分类、标签） |
| behaviors | 行为日志（click / read / collect，含停留时长） |
| interest_tags | 用户当前兴趣标签及权重（模型推理结果写入） |
| model_results | 每次推理快照（兴趣演化历史数据源） |
| model_train_logs | 模型训练记录（loss / accuracy / NDCG） |

---

## API 文档

运行后端后访问：`http://localhost:8000/docs`（Swagger UI 自动生成）

详细接口说明见 [docs/api/README.md](docs/api/README.md)


## Docker 本地部署

需要 Docker 和 Compose v2。在仓库根目录创建 `.env`，填写以下变量。

```dotenv
SECRET_KEY=replace_with_a_long_random_value
APP_PORT=5173
```

```sh
docker compose config --quiet
docker compose up -d --build
docker compose exec backend python -m database.seeds.generate_mock_data
docker compose exec backend python -m ml.training.trainer --epochs 20
docker compose ps
```

打开 [http://localhost:5173](http://localhost:5173)，API 文档位于 [http://localhost:5173/docs](http://localhost:5173/docs)。

镜像使用 CPU 版 PyTorch。`database` 和 `models` 数据卷分别保存 SQLite 与模型文件。生成脚本用于初始化演示数据，请在新测试数据卷上运行。模型训练可在进入页面后独立运行，耗时取决于 CPU。

使用 `docker compose logs --tail=100` 查看日志。使用 `docker compose down` 停止服务并保留数据卷。
