"""
推荐系统评估指标：Precision@K、Recall@K、NDCG@K
"""
import math
import numpy as np


def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / k


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended: list, relevant: set, k: int) -> float:
    """Normalized Discounted Cumulative Gain @ K"""
    dcg = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            dcg += 1.0 / math.log2(i + 2)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal > 0 else 0.0


def evaluate_batch(
    all_recommended: list[list],
    all_relevant: list[set],
    k: int = 5,
) -> dict:
    """
    all_recommended : 每个用户的推荐列表（已排序）
    all_relevant    : 每个用户的真实相关集合
    """
    p_list, r_list, n_list = [], [], []
    for rec, rel in zip(all_recommended, all_relevant):
        p_list.append(precision_at_k(rec, rel, k))
        r_list.append(recall_at_k(rec, rel, k))
        n_list.append(ndcg_at_k(rec, rel, k))
    return {
        f"precision@{k}": float(np.mean(p_list)),
        f"recall@{k}": float(np.mean(r_list)),
        f"ndcg@{k}": float(np.mean(n_list)),
    }
