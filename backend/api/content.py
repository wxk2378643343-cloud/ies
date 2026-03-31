import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.orm_models import Content, User
from backend.utils.deps import get_db, get_current_user, require_admin

router = APIRouter(prefix="/api/content", tags=["内容"])


# ---------- Schemas ----------

class ContentOut(BaseModel):
    id: int
    title: str
    body: str
    category: str
    tags_json: str
    author_id: Optional[int]
    status: str
    created_at: str

    class Config:
        from_attributes = True

    def model_post_init(self, __context):
        # 格式化时间为字符串
        if hasattr(self.created_at, 'isoformat'):
            object.__setattr__(self, 'created_at', self.created_at.isoformat())


class ContentSummary(BaseModel):
    id: int
    title: str
    category: str
    tags_json: str
    created_at: str

    class Config:
        from_attributes = True


class ContentCreate(BaseModel):
    title: str
    body: str
    category: str
    tags_json: str = "[]"


class ContentListResponse(BaseModel):
    items: list[ContentSummary]
    total: int
    page: int
    page_size: int


# ---------- Routes ----------

@router.get("/list", response_model=ContentListResponse)
def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Content).filter(Content.status == "published")
    if category:
        q = q.filter(Content.category == category)
    if keyword:
        q = q.filter(Content.title.contains(keyword))
    total = q.count()
    items = q.order_by(Content.created_at.desc()) \
              .offset((page - 1) * page_size) \
              .limit(page_size) \
              .all()
    return ContentListResponse(
        items=[_to_summary(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/categories")
def get_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Content.category).filter(Content.status == "published").distinct().all()
    return [r[0] for r in rows]


@router.get("/{content_id}", response_model=ContentOut)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.get(Content, content_id)
    if not c or c.status != "published":
        raise HTTPException(status_code=404, detail="内容不存在")
    return _to_out(c)


# ---------- Admin ----------

@router.post("/", response_model=ContentOut, status_code=201)
def create_content(
    body: ContentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    c = Content(**body.model_dump(), author_id=admin.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.put("/{content_id}/status")
def update_status(
    content_id: int,
    status: str = Query(..., pattern="^(published|draft|removed)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    c = db.get(Content, content_id)
    if not c:
        raise HTTPException(status_code=404, detail="内容不存在")
    c.status = status
    db.commit()
    return {"ok": True}


@router.get("/admin/all", response_model=ContentListResponse)
def admin_list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Content)
    total = q.count()
    items = q.order_by(Content.created_at.desc()) \
              .offset((page - 1) * page_size) \
              .limit(page_size) \
              .all()
    return ContentListResponse(
        items=[_to_summary(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------- Helpers ----------

def _to_summary(c: Content) -> ContentSummary:
    return ContentSummary(
        id=c.id,
        title=c.title,
        category=c.category,
        tags_json=c.tags_json,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )


def _to_out(c: Content) -> ContentOut:
    return ContentOut(
        id=c.id,
        title=c.title,
        body=c.body,
        category=c.category,
        tags_json=c.tags_json,
        author_id=c.author_id,
        status=c.status,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )
