"""
管理员专用 API

GET  /api/admin/stats/overview     概览统计（用户/内容/行为总量）
GET  /api/admin/stats/behaviors    近 30 天每日行为趋势
GET  /api/admin/stats/categories   各分类内容数量
GET  /api/admin/users              用户列表（分页）
PUT  /api/admin/users/{id}/role    修改用户角色
GET  /api/admin/model/versions     模型版本列表
GET  /api/admin/model/status       当前训练任务状态
POST /api/admin/model/train        触发训练（后台异步）
"""
import asyncio
import threading
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.orm_models import (
    Behavior, Content, ModelTrainLog, User
)
from backend.utils.deps import get_db, require_admin

router = APIRouter(prefix="/api/admin", tags=["管理员"])

# 简单内存状态：训练任务状态（启动时从数据库恢复最新记录）
def _load_last_result_from_db() -> dict | None:
    try:
        from sqlalchemy.orm import sessionmaker
        from backend.models.orm_models import engine
        Session = sessionmaker(bind=engine)
        db = Session()
        log = db.query(ModelTrainLog).order_by(ModelTrainLog.trained_at.desc()).first()
        db.close()
        if log is None:
            return None
        return {
            "version":      log.version,
            "val_loss":     round(log.loss or 0, 4),
            "val_accuracy": round(log.accuracy or 0, 4),
            "precision@1":  round(log.precision_at_k or 0, 4),
            "recall@1":     round(log.recall_at_k or 0, 4),
            "ndcg@1":       round(log.ndcg or 0, 4),
            "history":      None,
        }
    except Exception:
        return None

_train_status: dict = {"running": False, "last_result": _load_last_result_from_db(), "error": None}


# ---------- Schemas ----------

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int


# ---------- 统计接口 ----------

@router.get("/stats/overview")
def stats_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_users    = db.query(func.count(User.id)).scalar()
    total_contents = db.query(func.count(Content.id)).filter(Content.status == "published").scalar()
    total_behaviors= db.query(func.count(Behavior.id)).scalar()
    active_users   = db.query(func.count(func.distinct(Behavior.user_id))).scalar()
    new_today      = db.query(func.count(User.id)).filter(
        User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).scalar()

    return {
        "total_users": total_users,
        "total_contents": total_contents,
        "total_behaviors": total_behaviors,
        "active_users": active_users,
        "new_users_today": new_today,
    }


@router.get("/stats/behaviors")
def stats_behaviors_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """近 N 天每日行为量（按行为类型拆分）。"""
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Behavior.timestamp).label("day"),
            Behavior.action,
            func.count(Behavior.id).label("cnt"),
        )
        .filter(Behavior.timestamp >= since)
        .group_by(func.date(Behavior.timestamp), Behavior.action)
        .order_by(func.date(Behavior.timestamp))
        .all()
    )

    # 构建 {date: {action: count}} 结构
    data: dict = {}
    for row in rows:
        day = str(row.day)
        data.setdefault(day, {"click": 0, "read": 0, "collect": 0})
        data[day][row.action] = row.cnt

    dates = sorted(data.keys())
    return {
        "dates": dates,
        "click":   [data[d].get("click", 0) for d in dates],
        "read":    [data[d].get("read", 0) for d in dates],
        "collect": [data[d].get("collect", 0) for d in dates],
    }


@router.get("/stats/categories")
def stats_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        db.query(Content.category, func.count(Content.id).label("cnt"))
        .filter(Content.status == "published")
        .group_by(Content.category)
        .all()
    )
    return [{"category": r.category, "count": r.cnt} for r in rows]


@router.get("/stats/action_summary")
def stats_action_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        db.query(Behavior.action, func.count(Behavior.id).label("cnt"))
        .group_by(Behavior.action)
        .all()
    )
    return {r.action: r.cnt for r in rows}


# ---------- 用户管理 ----------

@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(User)
    if keyword:
        q = q.filter(User.username.contains(keyword) | User.email.contains(keyword))
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return UserListResponse(
        items=[_user_out(u) for u in users],
        total=total,
    )


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Query(..., pattern="^(user|admin)$"),
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    u.role = role
    db.commit()
    return {"ok": True}


# ---------- 模型管理 ----------

@router.get("/model/versions")
def model_versions(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    logs = (
        db.query(ModelTrainLog)
        .order_by(ModelTrainLog.trained_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "version":      log.version,
            "loss":         round(log.loss or 0, 4),
            "accuracy":     round(log.accuracy or 0, 4),
            "precision_k":  round(log.precision_at_k or 0, 4),
            "recall_k":     round(log.recall_at_k or 0, 4),
            "ndcg":         round(log.ndcg or 0, 4),
            "trained_at":   log.trained_at.isoformat() if log.trained_at else "",
            "note":         log.note or "",
        }
        for log in logs
    ]


@router.get("/model/status")
def model_train_status(_: User = Depends(require_admin)):
    return _train_status


@router.post("/model/train")
def trigger_train(
    epochs: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
):
    if _train_status["running"]:
        raise HTTPException(status_code=409, detail="训练任务已在运行中")
    threading.Thread(target=_run_training, args=(epochs,), daemon=True).start()
    return {"message": "训练任务已启动", "epochs": epochs}


# ---------- Helpers ----------

def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        email=u.email,
        role=u.role,
        created_at=u.created_at.isoformat() if u.created_at else "",
    )


def _run_training(epochs: int):
    global _train_status
    _train_status["running"] = True
    _train_status["error"] = None
    try:
        from backend.services.interest_service import trigger_training
        result = trigger_training(epochs=epochs)
        _train_status["last_result"] = result
    except Exception as e:
        _train_status["error"] = str(e)
    finally:
        _train_status["running"] = False
