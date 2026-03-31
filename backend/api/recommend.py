"""
推荐模块 API

GET /api/recommend            当前用户 Top-N 推荐内容（完整信息）
GET /api/recommend/interests  当前用户兴趣标签
GET /api/recommend/history    历史推理记录（兴趣演化数据）
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.orm_models import Content, InterestTag, ModelResult, User
from backend.utils.deps import get_db, get_current_user
from backend.api.content import _to_out, ContentOut

router = APIRouter(prefix="/api/recommend", tags=["推荐"])

CATEGORIES = ["科技", "体育", "娱乐", "财经", "教育", "健康", "游戏", "旅游"]


# ---------- Schemas ----------

class InterestTagOut(BaseModel):
    tag: str
    weight: float
    updated_at: Optional[str]


class InterestHistory(BaseModel):
    snapshot_time: str
    model_version: str
    tags: list[dict]   # [{tag, score}]
    confidence: float


class InitInterestsRequest(BaseModel):
    tags: list[str]


# ---------- Routes ----------

@router.post("/interests/init", status_code=204)
def init_interests(
    body: InitInterestsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新用户引导页：保存初始选择的兴趣分类。"""
    valid = [t for t in body.tags if t in CATEGORIES]
    if not valid:
        raise HTTPException(status_code=400, detail="请至少选择一个有效分类")
    existing = {t.tag for t in db.query(InterestTag).filter_by(user_id=current_user.id).all()}
    for tag in valid:
        if tag not in existing:
            db.add(InterestTag(user_id=current_user.id, tag=tag, weight=0.5))
    db.commit()


@router.get("/has_interests")
def has_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """判断当前用户是否已完成兴趣初始化。"""
    count = db.query(InterestTag).filter_by(user_id=current_user.id).count()
    return {"has_interests": count > 0}


@router.get("/", response_model=list[ContentOut])
def get_recommendations(
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    推荐优先级：
      1. ML 模型推理（有足够行为数据时）
      2. 用户手动选择的兴趣标签（冷启动）
      3. 最新内容（兜底）
    """
    result = _run_inference(current_user.id, top_n)

    if "error" not in result and result.get("recommended_content_ids"):
        content_ids = result["recommended_content_ids"]
        id_map = {c.id: c for c in db.query(Content).filter(Content.id.in_(content_ids)).all()}
        return [_to_out(id_map[cid]) for cid in content_ids if cid in id_map]

    # 回退1：按已有兴趣标签推荐
    tags = (
        db.query(InterestTag)
        .filter_by(user_id=current_user.id)
        .order_by(InterestTag.weight.desc())
        .limit(3)
        .all()
    )
    if tags:
        top_cats = [t.tag for t in tags]
        items, seen = [], set()
        per = max(1, top_n // len(top_cats))
        for cat in top_cats:
            rows = (
                db.query(Content)
                .filter(Content.category == cat, Content.status == "published")
                .order_by(Content.created_at.desc())
                .limit(per).all()
            )
            for r in rows:
                if r.id not in seen:
                    items.append(r); seen.add(r.id)
        if items:
            return [_to_out(c) for c in items[:top_n]]

    # 回退2：最新内容兜底
    items = (
        db.query(Content)
        .filter(Content.status == "published")
        .order_by(Content.created_at.desc())
        .limit(top_n).all()
    )
    return [_to_out(c) for c in items]


@router.get("/interests", response_model=list[InterestTagOut])
def get_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回当前用户的兴趣标签（按权重降序）。"""
    tags = (
        db.query(InterestTag)
        .filter(InterestTag.user_id == current_user.id)
        .order_by(InterestTag.weight.desc())
        .all()
    )
    return [
        InterestTagOut(
            tag=t.tag,
            weight=round(t.weight, 4),
            updated_at=t.updated_at.isoformat() if t.updated_at else None,
        )
        for t in tags
    ]


@router.get("/history", response_model=list[InterestHistory])
def get_interest_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    返回历史推理记录，用于前端绘制兴趣演化折线图。
    每条记录包含推理时间、各标签得分。
    """
    records = (
        db.query(ModelResult)
        .filter(ModelResult.user_id == current_user.id)
        .order_by(ModelResult.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        InterestHistory(
            snapshot_time=r.created_at.isoformat() if r.created_at else "",
            model_version=r.model_version,
            tags=json.loads(r.predicted_tags_json or "[]"),
            confidence=round(r.confidence or 0.0, 4),
        )
        for r in records
    ]


# ---------- Helper ----------

def _run_inference(user_id: int, top_n: int) -> dict:
    try:
        from ml.utils.inference import predict_user_interest
        return predict_user_interest(user_id=user_id, top_n=top_n)
    except Exception as e:
        print(f"[recommend] 推理失败 user={user_id}: {e}")
        return {"error": str(e)}
