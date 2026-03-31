"""
评估指标单元测试：Precision@K / Recall@K / NDCG@K
"""
import pytest
from ml.evaluation.metrics import precision_at_k, recall_at_k, ndcg_at_k, evaluate_batch


# ---------- Precision@K ----------

def test_precision_all_hit():
    assert precision_at_k([1, 2, 3], {1, 2, 3}, k=3) == 1.0

def test_precision_no_hit():
    assert precision_at_k([4, 5, 6], {1, 2, 3}, k=3) == 0.0

def test_precision_partial():
    assert precision_at_k([1, 4, 2], {1, 2, 3}, k=3) == pytest.approx(2/3)

def test_precision_k_larger_than_rec():
    # k=5 但推荐只有 3 个，分母仍为 k
    assert precision_at_k([1, 2, 3], {1, 2, 3, 4, 5}, k=5) == pytest.approx(3/5)

def test_precision_k1():
    assert precision_at_k([1, 2, 3], {1}, k=1) == 1.0
    assert precision_at_k([9, 2, 3], {1}, k=1) == 0.0


# ---------- Recall@K ----------

def test_recall_all_found():
    assert recall_at_k([1, 2, 3], {1, 2, 3}, k=3) == 1.0

def test_recall_none_found():
    assert recall_at_k([4, 5], {1, 2, 3}, k=2) == 0.0

def test_recall_partial():
    assert recall_at_k([1, 4], {1, 2, 3}, k=2) == pytest.approx(1/3)

def test_recall_empty_relevant():
    assert recall_at_k([1, 2], set(), k=2) == 0.0

def test_recall_k_less_than_relevant():
    assert recall_at_k([1, 2], {1, 2, 3, 4}, k=2) == pytest.approx(2/4)


# ---------- NDCG@K ----------

def test_ndcg_perfect():
    # 最优排序：所有命中且排在最前
    assert ndcg_at_k([1, 2, 3], {1, 2, 3}, k=3) == pytest.approx(1.0)

def test_ndcg_no_hit():
    assert ndcg_at_k([4, 5, 6], {1, 2, 3}, k=3) == 0.0

def test_ndcg_single_hit_first():
    val = ndcg_at_k([1, 4, 5], {1}, k=3)
    assert val == pytest.approx(1.0)   # DCG = 1/log2(2)=1, IDCG=1

def test_ndcg_single_hit_last():
    val = ndcg_at_k([4, 5, 1], {1}, k=3)
    import math
    expected = (1.0 / math.log2(4)) / (1.0 / math.log2(2))
    assert val == pytest.approx(expected, abs=1e-5)

def test_ndcg_partial_order():
    # 命中在第2位比第1位分数低
    v1 = ndcg_at_k([1, 2], {1, 2}, k=2)
    v2 = ndcg_at_k([2, 1], {1, 2}, k=2)
    # 两个命中位置不同但都命中，值相等（都是最优排列的一种）
    assert v1 == pytest.approx(v2)


# ---------- evaluate_batch ----------

def test_evaluate_batch_basic():
    recs = [[1, 2, 3], [4, 5, 6]]
    rels = [{1, 2}, {4}]
    result = evaluate_batch(recs, rels, k=3)
    assert "precision@3" in result
    assert "recall@3"    in result
    assert "ndcg@3"      in result
    assert 0.0 <= result["precision@3"] <= 1.0

def test_evaluate_batch_all_hit():
    recs = [[1, 2, 3]]
    rels = [{1, 2, 3}]
    result = evaluate_batch(recs, rels, k=3)
    assert result["precision@3"] == pytest.approx(1.0)
    assert result["recall@3"]    == pytest.approx(1.0)
    assert result["ndcg@3"]      == pytest.approx(1.0)

def test_evaluate_batch_empty_recs():
    result = evaluate_batch([[]], [set()], k=5)
    assert result["precision@5"] == 0.0
