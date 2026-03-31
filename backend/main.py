from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.config.settings import settings
from backend.models.orm_models import init_db
from backend.api import user, content, behavior, recommend, admin

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS — allow Vue dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(user.router)
app.include_router(content.router)
app.include_router(behavior.router)
app.include_router(recommend.router)
app.include_router(admin.router)

# 定时任务：每天凌晨 2 点增量更新所有用户兴趣标签
scheduler = BackgroundScheduler()


@app.on_event("startup")
def on_startup():
    init_db()
    scheduler.add_job(
        _daily_interest_update,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_interest_update",
    )
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown(wait=False)


def _daily_interest_update():
    try:
        from backend.services.interest_service import batch_update_all_users
        batch_update_all_users()
    except Exception as e:
        print(f"[scheduler] 定时更新失败: {e}")


@app.get("/")
def health():
    return {"status": "ok", "app": settings.app_name}
