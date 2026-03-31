# API 接口文档

> 基础地址：`http://localhost:8000`
> 鉴权：Bearer Token（登录/注册后获取，附在 `Authorization: Bearer <token>` 头）
> 完整 Swagger 文档：`http://localhost:8000/docs`

---

## 用户模块 `/api/user`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/user/register` | 无 | 注册，返回 access_token |
| POST | `/api/user/login`    | 无 | 登录，返回 access_token |
| GET  | `/api/user/me`       | 登录 | 获取当前用户信息 |
| GET  | `/api/user/profile/{id}` | 登录 | 获取指定用户公开信息 |

**注册请求体**
```json
{ "username": "string", "email": "string", "password": "string" }
```

**登录请求体**
```json
{ "email": "string", "password": "string" }
```

**Token 响应**
```json
{ "access_token": "string", "token_type": "bearer", "role": "user|admin" }
```

---

## 内容模块 `/api/content`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET  | `/api/content/list`         | 登录 | 分页列表，支持 `category`/`keyword`/`page`/`page_size` |
| GET  | `/api/content/categories`   | 登录 | 所有内容分类 |
| GET  | `/api/content/{id}`         | 登录 | 内容详情 |
| POST | `/api/content/`             | 管理员 | 创建内容 |
| PUT  | `/api/content/{id}/status`  | 管理员 | 更新状态（published/draft/removed） |
| GET  | `/api/content/admin/all`    | 管理员 | 全量内容列表（含草稿/下架） |

**内容创建请求体**
```json
{
  "title": "string",
  "body": "string",
  "category": "科技|体育|娱乐|财经|教育|健康|游戏|旅游",
  "tags_json": "[\"tag1\", \"tag2\"]"
}
```

---

## 行为日志模块 `/api/behavior`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/behavior/report`           | 登录 | 上报行为（点击/阅读/收藏） |
| GET  | `/api/behavior/my`               | 登录 | 当前用户行为历史 |
| GET  | `/api/behavior/admin/stats`      | 管理员 | 行为汇总统计 |
| GET  | `/api/behavior/admin/user/{id}`  | 管理员 | 指定用户行为历史 |

**行为上报请求体**
```json
{
  "content_id": 1,
  "action": "click|read|collect",
  "duration_sec": 0.0
}
```

---

## 推荐模块 `/api/recommend`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET  | `/api/recommend`           | 登录 | Top-N 推荐内容（`?top_n=10`） |
| GET  | `/api/recommend/interests` | 登录 | 当前用户兴趣标签列表 |
| GET  | `/api/recommend/history`   | 登录 | 历史推理快照（兴趣演化数据源） |

**推荐内容响应**：返回 `Content` 对象列表，字段同内容详情。

**兴趣标签响应**
```json
[{ "tag": "科技", "weight": 0.3142, "updated_at": "2026-01-01T00:00:00" }]
```

**兴趣历史响应**
```json
[{
  "snapshot_time": "2026-01-01T00:00:00",
  "model_version": "v20260101_120000",
  "tags": [{"tag": "科技", "score": 0.31}],
  "confidence": 0.31
}]
```

---

## 管理员模块 `/api/admin`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/admin/stats/overview`      | 概览统计（用户/内容/行为总量） |
| GET  | `/api/admin/stats/behaviors`     | 近N天每日行为趋势（`?days=30`） |
| GET  | `/api/admin/stats/categories`    | 各分类内容数量 |
| GET  | `/api/admin/stats/action_summary`| 行为类型汇总 |
| GET  | `/api/admin/users`               | 用户列表（`?keyword=&page=1`） |
| PUT  | `/api/admin/users/{id}/role`     | 修改用户角色（`?role=admin\|user`） |
| GET  | `/api/admin/model/versions`      | 模型版本历史 |
| GET  | `/api/admin/model/status`        | 当前训练状态 |
| POST | `/api/admin/model/train`         | 触发训练（`?epochs=20`） |

---

## 错误码说明

| HTTP 状态码 | 含义 |
|-------------|------|
| 400 | 请求参数错误（如重复注册、无效行为类型） |
| 401 | 未登录或 Token 无效/过期 |
| 403 | 权限不足（需要管理员角色） |
| 404 | 资源不存在 |
| 409 | 冲突（如训练任务已在运行） |
| 500 | 服务器内部错误 |
