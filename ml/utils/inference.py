"""
在线推理：给定 user_id，返回推荐内容 ID 列表及兴趣分布。
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.data.preprocess import ACTION_WEIGHT, SEQ_LEN
from ml.utils.model_registry import load_latest_model


def predict_user_interest(user_id: int, top_n: int = 10) -> dict:
    """
    返回：
      - interest_probs : {category: probability}
      - top_categories : 按概率排序的类别列表
      - recommended_content_ids : 推荐内容 ID 列表
      - attn_weights   : 注意力权重（可视化用）
    """
    model, meta = load_latest_model()
    if model is None:
        return {"error": "模型尚未训练"}

    vocab_data = meta["vocab"]
    vocab: dict = {int(k): v for k, v in vocab_data["vocab"].items()}
    categories: list = vocab_data["categories"]
    cat2idx: dict = vocab_data["category2idx"]
    idx2cat = {v: k for k, v in cat2idx.items()}

    from sqlalchemy.orm import sessionmaker
    from backend.models.orm_models import engine, Behavior, Content, InterestTag
    from datetime import datetime

    Session = sessionmaker(bind=engine)
    db = Session()

    # 获取用户最近 SEQ_LEN 条行为
    behaviors = (
        db.query(Behavior)
        .filter(Behavior.user_id == user_id)
        .order_by(Behavior.timestamp.desc())
        .limit(SEQ_LEN)
        .all()
    )
    behaviors = list(reversed(behaviors))  # 时间正序

    if not behaviors:
        db.close()
        return {"error": "该用户暂无行为记录"}

    # 填充到 SEQ_LEN
    pad_len = SEQ_LEN - len(behaviors)
    cid_seq = [0] * pad_len + [vocab.get(b.content_id, 0) for b in behaviors]
    w_seq = [1.0] * pad_len + [ACTION_WEIGHT.get(b.action, 1.0) for b in behaviors]

    cid_tensor = torch.tensor([cid_seq], dtype=torch.long)    # (1, SEQ_LEN)
    w_tensor = torch.tensor([w_seq], dtype=torch.float)        # (1, SEQ_LEN)

    with torch.no_grad():
        logits, attn_weights = model(cid_tensor, w_tensor)
        probs = torch.softmax(logits, dim=-1)[0].tolist()

    interest_probs = {categories[i]: round(probs[i], 4) for i in range(len(categories))}
    top_categories = sorted(interest_probs, key=lambda c: interest_probs[c], reverse=True)

    # 更新 interest_tags 表
    _update_interest_tags(db, user_id, interest_probs)

    # 推荐：优先取概率最高的类别的内容
    recommended_ids = _get_top_n_contents(db, top_categories, top_n)

    # 持久化本次推理结果到 model_results
    _save_model_result(db, user_id, interest_probs, meta["version"])

    db.close()
    return {
        "interest_probs": interest_probs,
        "top_categories": top_categories[:3],
        "recommended_content_ids": recommended_ids,
        "attn_weights": attn_weights[0].tolist(),
    }


def _update_interest_tags(db, user_id: int, interest_probs: dict):
    from backend.models.orm_models import InterestTag
    from datetime import datetime

    existing = {t.tag: t for t in db.query(InterestTag).filter_by(user_id=user_id).all()}
    for cat, prob in interest_probs.items():
        if cat in existing:
            existing[cat].weight = prob
            existing[cat].updated_at = datetime.utcnow()
        else:
            db.add(InterestTag(user_id=user_id, tag=cat, weight=prob))
    db.commit()


def _save_model_result(db, user_id: int, interest_probs: dict, version: str):
    from backend.models.orm_models import ModelResult
    top_tags = sorted(interest_probs.items(), key=lambda x: x[1], reverse=True)
    predicted_tags = [{"tag": t, "score": s} for t, s in top_tags]
    confidence = top_tags[0][1] if top_tags else 0.0
    db.add(ModelResult(
        user_id=user_id,
        predicted_tags_json=json.dumps(predicted_tags, ensure_ascii=False),
        confidence=confidence,
        model_version=version,
    ))
    db.commit()


def _get_top_n_contents(db, top_categories: list, n: int) -> list[int]:
    from backend.models.orm_models import Content

    result = []
    per_cat = max(1, n // 3)  # 每个 top 分类取 per_cat 条

    for cat in top_categories[:3]:
        items = (
            db.query(Content.id)
            .filter(Content.category == cat, Content.status == "published")
            .order_by(Content.created_at.desc())
            .limit(per_cat)
            .all()
        )
        result.extend([r[0] for r in items])
        if len(result) >= n:
            break

    return result[:n]
