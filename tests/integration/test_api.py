"""
API 集成测试（使用测试数据库 + TestClient）

覆盖范围：
  - 用户注册 / 登录 / 获取个人信息
  - 内容列表 / 详情 / 管理员创建 / 状态变更
  - 行为上报 / 查询
  - 推荐接口（冷启动回退）
  - 管理员统计看板
"""
import pytest


# ============================================================
# 用户模块
# ============================================================

class TestUserAuth:
    def test_register_success(self, client):
        r = client.post("/api/user/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "pass1234",
        })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["role"] == "user"

    def test_register_duplicate_email(self, client):
        payload = {"username": "dup1", "email": "dup@test.com", "password": "pass1234"}
        client.post("/api/user/register", json=payload)
        r = client.post("/api/user/register", json={**payload, "username": "dup2"})
        assert r.status_code == 400

    def test_register_duplicate_username(self, client):
        client.post("/api/user/register", json={
            "username": "samename", "email": "a@test.com", "password": "pass1234"
        })
        r = client.post("/api/user/register", json={
            "username": "samename", "email": "b@test.com", "password": "pass1234"
        })
        assert r.status_code == 400

    def test_login_success(self, client):
        client.post("/api/user/register", json={
            "username": "logintest", "email": "login@test.com", "password": "pass1234"
        })
        r = client.post("/api/user/login", json={
            "email": "login@test.com", "password": "pass1234"
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        r = client.post("/api/user/login", json={
            "email": "login@test.com", "password": "wrongpass"
        })
        assert r.status_code == 401

    def test_get_me_authenticated(self, client, user_headers):
        r = client.get("/api/user/me", headers=user_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "user@test.com"
        assert data["role"]  == "user"

    def test_get_me_unauthenticated(self, client):
        r = client.get("/api/user/me")
        assert r.status_code == 401


# ============================================================
# 内容模块
# ============================================================

class TestContent:
    @pytest.fixture(autouse=True)
    def create_content(self, client, admin_headers):
        """每个测试类共用一份内容。"""
        r = client.post("/api/content/", json={
            "title": "测试文章",
            "body":  "这是测试文章的正文内容。" * 5,
            "category": "科技",
            "tags_json": '["科技","测试"]',
        }, headers=admin_headers)
        assert r.status_code == 201
        self.content_id = r.json()["id"]

    def test_list_contents(self, client, user_headers):
        r = client.get("/api/content/list", headers=user_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_list_with_category_filter(self, client, user_headers):
        r = client.get("/api/content/list", params={"category": "科技"}, headers=user_headers)
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["category"] == "科技"

    def test_list_with_keyword(self, client, user_headers):
        r = client.get("/api/content/list", params={"keyword": "测试文章"}, headers=user_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_get_content_detail(self, client, user_headers):
        r = client.get(f"/api/content/{self.content_id}", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["title"] == "测试文章"

    def test_get_nonexistent_content(self, client, user_headers):
        r = client.get("/api/content/99999", headers=user_headers)
        assert r.status_code == 404

    def test_get_categories(self, client, user_headers):
        r = client.get("/api/content/categories", headers=user_headers)
        assert r.status_code == 200
        assert "科技" in r.json()

    def test_update_status_admin(self, client, admin_headers):
        r = client.put(f"/api/content/{self.content_id}/status",
                       params={"status": "removed"}, headers=admin_headers)
        assert r.status_code == 200
        # 下架后普通用户无法访问
        from tests.conftest import create_access_token  # noqa

    def test_create_content_requires_admin(self, client, user_headers):
        r = client.post("/api/content/", json={
            "title": "非法创建", "body": "...", "category": "科技"
        }, headers=user_headers)
        assert r.status_code == 403


# ============================================================
# 行为日志模块
# ============================================================

class TestBehavior:
    @pytest.fixture(autouse=True)
    def setup(self, client, admin_headers, user_headers):
        r = client.post("/api/content/", json={
            "title": "行为测试文章",
            "body": "内容" * 20,
            "category": "教育",
            "tags_json": '["教育"]',
        }, headers=admin_headers)
        self.cid = r.json()["id"]
        self.user_headers = user_headers

    def test_report_click(self, client):
        r = client.post("/api/behavior/report", json={
            "content_id": self.cid, "action": "click"
        }, headers=self.user_headers)
        assert r.status_code == 204

    def test_report_read(self, client):
        r = client.post("/api/behavior/report", json={
            "content_id": self.cid, "action": "read", "duration_sec": 45.5
        }, headers=self.user_headers)
        assert r.status_code == 204

    def test_report_collect(self, client):
        r = client.post("/api/behavior/report", json={
            "content_id": self.cid, "action": "collect"
        }, headers=self.user_headers)
        assert r.status_code == 204

    def test_report_invalid_action(self, client):
        r = client.post("/api/behavior/report", json={
            "content_id": self.cid, "action": "invalid"
        }, headers=self.user_headers)
        assert r.status_code == 400

    def test_my_behaviors(self, client):
        r = client.get("/api/behavior/my", headers=self.user_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_stats(self, client, admin_headers):
        r = client.get("/api/behavior/admin/stats", headers=admin_headers)
        assert r.status_code == 200
        assert "by_action" in r.json()


# ============================================================
# 推荐模块
# ============================================================

class TestRecommend:
    def test_get_recommendations_cold_start(self, client, user_headers):
        """模型未训练时应回退到最新内容，不返回 500。"""
        r = client.get("/api/recommend", headers=user_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_interests_empty(self, client, user_headers):
        r = client.get("/api/recommend/interests", headers=user_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_interest_history(self, client, user_headers):
        r = client.get("/api/recommend/history", headers=user_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_recommend_requires_auth(self, client):
        r = client.get("/api/recommend")
        assert r.status_code == 401


# ============================================================
# 管理员看板
# ============================================================

class TestAdminStats:
    def test_overview(self, client, admin_headers):
        r = client.get("/api/admin/stats/overview", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_users"    in data
        assert "total_contents" in data
        assert "total_behaviors"in data

    def test_behaviors_trend(self, client, admin_headers):
        r = client.get("/api/admin/stats/behaviors", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "dates" in data and "click" in data

    def test_categories(self, client, admin_headers):
        r = client.get("/api/admin/stats/categories", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_user_list(self, client, admin_headers):
        r = client.get("/api/admin/users", headers=admin_headers)
        assert r.status_code == 200
        assert "items" in r.json()

    def test_model_versions(self, client, admin_headers):
        r = client.get("/api/admin/model/versions", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_model_status(self, client, admin_headers):
        r = client.get("/api/admin/model/status", headers=admin_headers)
        assert r.status_code == 200
        assert "running" in r.json()

    def test_admin_endpoint_requires_admin(self, client, user_headers):
        r = client.get("/api/admin/stats/overview", headers=user_headers)
        assert r.status_code == 403
