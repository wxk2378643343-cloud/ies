# 用户兴趣演化分析与预测系统

![FastAPI](https://img.shields.io/badge/FastAPI-2563EB?style=flat-square)
![Vue 3](https://img.shields.io/badge/Vue%203-0F766E?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-334155?style=flat-square)
![PyTorch](https://img.shields.io/badge/PyTorch-B45309?style=flat-square)

## 📌 项目简介

记录用户对内容的行为，分析兴趣随时间的变化，并用带注意力机制的 LSTM 生成个性化推荐。

## 🏗️ 系统架构

- Vue 用户端和管理端调用 FastAPI，浏览、点击等行为写入 SQLite。
- 训练模块读取行为序列、生成模型检查点，后端在推荐流程中加载模型。

## 📁 项目结构

| 路径 | 用途 |
| --- | --- |
| [`frontend`](frontend) | 用户端和管理端界面 |
| [`backend`](backend) | API、推荐和调度 |
| [`ml`](ml) | 序列预处理、模型和训练 |
| [`database`](database) | 模拟数据生成 |
| [`tests`](tests) | 单元、集成及压测 |

## 🚀 如何启动

建议先启动 Compose 并生成演示数据。模型训练可以在容器里单独运行。

### Docker 本地部署

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

### 快速开始

#### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install
```

#### 2. 生成测试数据

```bash
python -m database.seeds.generate_mock_data
# 生成：1 管理员 + 10 普通用户 + 32 篇内容 + 行为日志
# 管理员账号：admin@ies.com  密码：admin123
# 普通用户：user01@ies.com   密码：password123
```

#### 3. 训练模型

```bash
python -m ml.training.trainer --epochs 20
```

#### 4. 启动服务

```bash
# 后端（http://localhost:8000）
python -m uvicorn backend.main:app --reload

# 前端（http://localhost:5173）
cd frontend && npm run dev
```

#### 5. 运行测试

```bash
python -m pytest          # 全部（60个）
python -m pytest tests/unit/         # 单元测试（28个）
python -m pytest tests/integration/  # 集成测试（32个）
```

#### 6. 压测

```bash
# 需要后端运行中
locust -f tests/performance/locustfile.py --host=http://localhost:8000
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

---
## ✨ 核心算法与工程亮点

1. **为什么采用「行为加权 + 2 层 LSTM + Self-Attention」？**
   - **差异化行为信号建模**：将 `collect(3) / read(2) / click(1)` 显式转化为动作权重乘入 64 维内容 Embedding，避免把偶然误点与深度收藏混为一谈；
   - **时序兴趣演化捕捉**：采用 2 层 LSTM（`hidden=128, dropout=0.2`）对用户最近 20 条行为序列建模，自然捕获兴趣随时间的迁移与衰减；
   - **Self-Attention 聚焦高价值时刻**：对 LSTM 各时间步输出动态分配注意力权重，突出近期关键交互对当前偏好的决定性影响，提升 Top-N 推荐相关度。
2. **端到端可观测的推荐闭环**：推理结果不仅写回 `interest_tags` 驱动实时推荐，还沉淀 `model_results` 推理快照与 `model_train_logs`（`loss / accuracy / NDCG`），支持前端直观展示用户兴趣演化轨迹。
3. **高标准工程验证体系**：内置 60 个自动化测试（28 个单元测试 + 32 个集成测试）与 Locust 性能压测脚本，支持 Docker Compose 一键拉起模拟数据生成、模型训练与在线推理全流程。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源，详见根目录 [LICENSE](LICENSE) 文件。
