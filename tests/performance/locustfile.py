"""
Locust 压测脚本：模拟真实用户行为。

运行方式（项目根目录）：
  locust -f tests/performance/locustfile.py --host=http://localhost:8000

  或无 UI 模式（CI 用）：
  locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
         --headless -u 50 -r 5 --run-time 60s

场景覆盖：
  NormalUser  - 注册 → 获取内容列表 → 浏览详情 → 上报行为 → 查看推荐
  AdminUser   - 登录 → 查看看板统计 → 查看用户列表 → 查看模型版本
"""
import random
import string
from locust import HttpUser, task, between, events


def random_str(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class NormalUser(HttpUser):
    wait_time = between(1, 3)
    token: str = ""
    content_ids: list = []

    def on_start(self):
        """每个虚拟用户启动时注册并登录。"""
        suffix = random_str()
        payload = {
            "username": f"perf_{suffix}",
            "email":    f"perf_{suffix}@test.com",
            "password": "perf1234",
        }
        with self.client.post("/api/user/register", json=payload,
                              catch_response=True) as r:
            if r.status_code == 201:
                self.token = r.json()["access_token"]
            else:
                r.failure(f"注册失败: {r.text}")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def browse_content_list(self):
        page = random.randint(1, 3)
        with self.client.get(f"/api/content/list?page={page}&page_size=12",
                             headers=self._headers(), catch_response=True) as r:
            if r.status_code == 200:
                items = r.json().get("items", [])
                self.content_ids = [i["id"] for i in items]
            else:
                r.failure(f"内容列表失败: {r.status_code}")

    @task(5)
    def view_content_detail(self):
        if not self.content_ids:
            return
        cid = random.choice(self.content_ids)
        with self.client.get(f"/api/content/{cid}",
                             headers=self._headers(), catch_response=True) as r:
            if r.status_code not in (200, 404):
                r.failure(f"内容详情失败: {r.status_code}")

    @task(4)
    def report_behavior(self):
        if not self.content_ids:
            return
        cid = random.choice(self.content_ids)
        action = random.choices(["click", "read", "collect"], weights=[5, 3, 2])[0]
        payload = {"content_id": cid, "action": action}
        if action == "read":
            payload["duration_sec"] = random.uniform(10, 120)
        with self.client.post("/api/behavior/report", json=payload,
                              headers=self._headers(), catch_response=True) as r:
            if r.status_code not in (204, 404):
                r.failure(f"行为上报失败: {r.status_code}")

    @task(2)
    def get_recommendations(self):
        with self.client.get("/api/recommend?top_n=8",
                             headers=self._headers(), catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"推荐失败: {r.status_code}")

    @task(1)
    def view_interests(self):
        with self.client.get("/api/recommend/interests",
                             headers=self._headers(), catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"兴趣标签失败: {r.status_code}")

    @task(1)
    def search_content(self):
        kws = ["科技", "体育", "游戏", "健康", "Python"]
        kw = random.choice(kws)
        with self.client.get(f"/api/content/list?keyword={kw}&page_size=10",
                             headers=self._headers(), catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"搜索失败: {r.status_code}")


class AdminUser(HttpUser):
    """模拟管理员操作，权重低（1:10 比例）。"""
    wait_time = between(2, 5)
    weight = 1
    token: str = ""

    def on_start(self):
        with self.client.post("/api/user/login", json={
            "email": "admin@ies.com",
            "password": "admin123",
        }, catch_response=True) as r:
            if r.status_code == 200:
                self.token = r.json()["access_token"]
            else:
                r.failure("管理员登录失败，请先运行 generate_mock_data.py")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def dashboard_overview(self):
        self.client.get("/api/admin/stats/overview", headers=self._headers())

    @task(2)
    def behavior_trend(self):
        self.client.get("/api/admin/stats/behaviors?days=30", headers=self._headers())

    @task(2)
    def user_list(self):
        self.client.get("/api/admin/users?page=1", headers=self._headers())

    @task(1)
    def model_versions(self):
        self.client.get("/api/admin/model/versions", headers=self._headers())

    @task(1)
    def model_status(self):
        self.client.get("/api/admin/model/status", headers=self._headers())


# ---------- 压测完成后打印汇总 ----------

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.stats
    print("\n========== 压测汇总 ==========")
    print(f"  总请求数:    {stats.total.num_requests}")
    print(f"  失败请求数:  {stats.total.num_failures}")
    print(f"  平均响应时间: {stats.total.avg_response_time:.1f} ms")
    print(f"  P95 响应时间: {stats.total.get_response_time_percentile(0.95):.1f} ms")
    print(f"  P99 响应时间: {stats.total.get_response_time_percentile(0.99):.1f} ms")
    print(f"  RPS:          {stats.total.current_rps:.1f}")
    print("==============================")
