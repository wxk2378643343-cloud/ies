"""
LSTM+Attention 模型单元测试
- 输出形状正确
- Attention 权重归一化（和为 1）
- Padding mask 正常工作（padding 位置权重为 0）
- 兴趣向量维度正确
- 不同 batch_size 均可推理
"""
import pytest
import torch
from ml.models.lstm_attention import LSTMAttention

NUM_CONTENTS   = 50
NUM_CATEGORIES = 8
SEQ_LEN        = 20


@pytest.fixture(scope="module")
def model():
    m = LSTMAttention(num_contents=NUM_CONTENTS, num_categories=NUM_CATEGORIES)
    m.eval()
    return m


def make_batch(batch=4, seq=SEQ_LEN, pad_front=0):
    """构造测试批次，pad_front 指定前缀 padding 数量。"""
    cid = torch.randint(1, NUM_CONTENTS + 1, (batch, seq))
    if pad_front > 0:
        cid[:, :pad_front] = 0
    weights = torch.rand(batch, seq)
    return cid, weights


# ---------- 形状测试 ----------

def test_output_shape(model):
    cid, w = make_batch(4)
    logits, attn = model(cid, w)
    assert logits.shape == (4, NUM_CATEGORIES), "logits 形状错误"
    assert attn.shape == (4, SEQ_LEN), "attention 形状错误"


def test_interest_vector_shape(model):
    cid, w = make_batch(4)
    vec = model.get_interest_vector(cid, w)
    assert vec.shape == (4, 128), "兴趣向量维度应为 hidden_size=128"


def test_batch_size_1(model):
    cid, w = make_batch(1)
    logits, attn = model(cid, w)
    assert logits.shape == (1, NUM_CATEGORIES)


def test_batch_size_32(model):
    cid, w = make_batch(32)
    logits, _ = model(cid, w)
    assert logits.shape == (32, NUM_CATEGORIES)


# ---------- Attention 归一化测试 ----------

def test_attention_sums_to_one(model):
    cid, w = make_batch(8)
    _, attn = model(cid, w)
    sums = attn.sum(dim=-1)
    assert torch.allclose(sums, torch.ones(8), atol=1e-5), \
        f"Attention 权重应归一化，实际和: {sums}"


def test_attention_nonnegative(model):
    cid, w = make_batch(4)
    _, attn = model(cid, w)
    assert (attn >= 0).all(), "Attention 权重不应为负"


# ---------- Padding mask 测试 ----------

def test_padding_mask_zero_weight(model):
    """padding 位置（content_id=0）的 attention 权重应接近 0。"""
    cid, w = make_batch(2, pad_front=10)   # 前 10 位为 padding
    _, attn = model(cid, w)
    pad_attn = attn[:, :10].sum(dim=-1)    # padding 区域权重之和
    # padding 位置被 -inf mask，softmax 后应极小
    assert (pad_attn < 0.01).all(), \
        f"Padding 位置 attention 权重应接近 0，实际: {pad_attn}"


# ---------- Logits 合法性 ----------

def test_logits_finite(model):
    cid, w = make_batch(4)
    logits, _ = model(cid, w)
    assert torch.isfinite(logits).all(), "Logits 中存在 NaN 或 Inf"


def test_softmax_probabilities(model):
    cid, w = make_batch(4)
    logits, _ = model(cid, w)
    probs = torch.softmax(logits, dim=-1)
    assert torch.allclose(probs.sum(dim=-1), torch.ones(4), atol=1e-5)
    assert (probs >= 0).all()


# ---------- 无 action_weights 时也能运行 ----------

def test_no_action_weights(model):
    cid = torch.randint(1, NUM_CONTENTS + 1, (4, SEQ_LEN))
    logits, attn = model(cid)    # 不传 action_weights
    assert logits.shape == (4, NUM_CATEGORIES)
