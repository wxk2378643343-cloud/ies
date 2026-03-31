from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.orm_models import Behavior, Content, User
from backend.utils.deps import get_db, get_current_user, require_admin

router = APIRouter(prefix="/api/behavior", tags=["行为日志"])


# ---------- Schemas ----------

class BehaviorReport(BaseModel):
    content_id: int
    action: str          # click | read | collect
    duration_sec: float = 0.0


class BehaviorOut(BaseModel):
    id: int
    user_id: int
    content_id: int
    action: str
    duration_sec: float
    timestamp: str


# ---------- Routes ----------

@router.post("/report", status_code=204)
def report_behavior(
    body: BehaviorReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.action not in ("click", "read", "collect"):
        raise HTTPException(status_code=400, detail="无效的行为类型")
    content = db.get(Content, body.content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    b = Behavior(
        user_id=current_user.id,
        content_id=body.content_id,
        action=body.action,
        duration_sec=body.duration_sec,
        timestamp=datetime.utcnow(),
    )
    db.add(b)
    db.commit()


@router.get("/my", response_model=list[BehaviorOut])
def my_behaviors(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Behavior)
        .filter(Behavior.user_id == current_user.id)
        .order_by(Behavior.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(b) for b in rows]


# ---------- Admin ----------

@router.get("/admin/stats")
def behavior_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from sqlalchemy import func

    rows = (
        db.query(Behavior.action, func.count(Behavior.id).label("cnt"))
        .group_by(Behavior.action)
        .all()
    )
    total_users = db.query(func.count(func.distinct(Behavior.user_id))).scalar()
    total_contents = db.query(func.count(func.distinct(Behavior.content_id))).scalar()

    return {
        "by_action": {r.action: r.cnt for r in rows},
        "total_users_with_behavior": total_users,
        "total_contents_interacted": total_contents,
    }


@router.get("/admin/user/{user_id}", response_model=list[BehaviorOut])
def user_behaviors(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        db.query(Behavior)
        .filter(Behavior.user_id == user_id)
        .order_by(Behavior.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(b) for b in rows]


# ---------- Helper ----------

def _to_out(b: Behavior) -> BehaviorOut:
    return BehaviorOut(
        id=b.id,
        user_id=b.user_id,
        content_id=b.content_id,
        action=b.action,
        duration_sec=b.duration_sec or 0.0,
        timestamp=b.timestamp.isoformat() if b.timestamp else "",
    )
