"""
从 SQLite 数据库提取行为序列，构建训练样本并保存词表。

输出：
  - sequences: list of (content_id_seq, action_weight_seq, label_category_idx)
  - vocab: {content_id(int) -> index(int)}  (index 0 保留为 padding)
  - category_map: {category(str) -> idx(int)}
"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.orm import sessionmaker
from backend.models.orm_models import engine, Behavior, Content

CATEGORIES = ["科技", "体育", "娱乐", "财经", "教育", "健康", "游戏", "旅游"]
CATEGORY2IDX = {c: i for i, c in enumerate(CATEGORIES)}
ACTION_WEIGHT = {"click": 1.0, "read": 2.0, "collect": 3.0}
SEQ_LEN = 20          # 每条序列长度
MIN_BEHAVIORS = 5     # 用户至少有这么多行为才参与训练

VOCAB_PATH = Path(__file__).parent / "vocab.json"

SessionLocal = sessionmaker(bind=engine)


def build_dataset(seq_len: int = SEQ_LEN):
    db = SessionLocal()

    # content_id -> category 映射
    contents = db.query(Content.id, Content.category).all()
    cid2cat = {c.id: c.category for c in contents}

    # 构建 content_id 词表（0 保留为 padding）
    all_cids = sorted(cid2cat.keys())
    vocab = {cid: idx + 1 for idx, cid in enumerate(all_cids)}  # 从 1 开始

    # 保存词表
    VOCAB_PATH.write_text(json.dumps({
        "vocab": {str(k): v for k, v in vocab.items()},
        "category2idx": CATEGORY2IDX,
        "categories": CATEGORIES,
        "num_contents": len(vocab),
        "num_categories": len(CATEGORIES),
    }, ensure_ascii=False))

    # 按用户分组行为，时间排序
    behaviors = (
        db.query(Behavior)
        .order_by(Behavior.user_id, Behavior.timestamp)
        .all()
    )

    user_behaviors: dict[int, list] = {}
    for b in behaviors:
        user_behaviors.setdefault(b.user_id, []).append(b)

    db.close()

    sequences = []
    for uid, blist in user_behaviors.items():
        if len(blist) < MIN_BEHAVIORS:
            continue

        # 滑动窗口切分
        for i in range(len(blist) - seq_len):
            window = blist[i: i + seq_len]
            next_b = blist[i + seq_len]

            cat = cid2cat.get(next_b.content_id)
            if cat not in CATEGORY2IDX:
                continue

            cid_seq = [vocab.get(b.content_id, 0) for b in window]
            weight_seq = [ACTION_WEIGHT.get(b.action, 1.0) for b in window]
            label = CATEGORY2IDX[cat]

            sequences.append((cid_seq, weight_seq, label))

    print(f"[preprocess] 样本数: {len(sequences)}  词表大小: {len(vocab)}")
    return sequences, vocab, CATEGORY2IDX


def load_vocab():
    data = json.loads(VOCAB_PATH.read_text())
    data["vocab"] = {int(k): v for k, v in data["vocab"].items()}
    return data


if __name__ == "__main__":
    build_dataset()
