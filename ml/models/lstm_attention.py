"""
LSTM + Self-Attention 用户兴趣演化模型

架构：
  输入序列 (content_id, action_weight)
      │
  Embedding 层  (num_contents+1, embed_dim)
      │  × action_weight（加权近期高价值行为）
      │
  LSTM 层       (embed_dim -> hidden_size, num_layers)
      │
  Self-Attention（对 LSTM 各时间步加权，突出重要行为）
      │
  兴趣向量 context  (hidden_size,)
      │
  全连接分类器  -> 类别 logits  (num_categories,)
"""
import torch
import torch.nn as nn


class LSTMAttention(nn.Module):
    def __init__(
        self,
        num_contents: int,
        num_categories: int,
        embed_dim: int = 64,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.embedding = nn.Embedding(
            num_contents + 1, embed_dim, padding_idx=0
        )
        self.lstm = nn.LSTM(
            embed_dim, hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.attention = nn.Linear(hidden_size, 1)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_categories)

    def _attend(self, lstm_out: torch.Tensor, mask: torch.Tensor = None):
        """
        lstm_out : (batch, seq_len, hidden)
        mask     : (batch, seq_len)  True 表示 padding 位置
        returns  : context (batch, hidden), attn_weights (batch, seq_len)
        """
        scores = self.attention(lstm_out).squeeze(-1)  # (batch, seq_len)
        if mask is not None:
            scores = scores.masked_fill(mask, float("-inf"))
        attn_weights = torch.softmax(scores, dim=-1)   # (batch, seq_len)
        context = (lstm_out * attn_weights.unsqueeze(-1)).sum(dim=1)  # (batch, hidden)
        return context, attn_weights

    def forward(
        self,
        cid_seq: torch.Tensor,       # (batch, seq_len)
        action_weights: torch.Tensor = None,  # (batch, seq_len)
    ):
        emb = self.embedding(cid_seq)          # (batch, seq_len, embed_dim)
        if action_weights is not None:
            # 归一化权重后加权 embedding，突出高价值行为（收藏 > 阅读 > 点击）
            w = (action_weights / action_weights.max(dim=1, keepdim=True).values.clamp(min=1))
            emb = emb * w.unsqueeze(-1)

        lstm_out, _ = self.lstm(emb)           # (batch, seq_len, hidden)
        lstm_out = self.dropout(lstm_out)

        # padding mask：content_id == 0 的位置为 padding
        mask = (cid_seq == 0)
        context, attn_weights = self._attend(lstm_out, mask)

        logits = self.classifier(context)      # (batch, num_categories)
        return logits, attn_weights

    def get_interest_vector(
        self,
        cid_seq: torch.Tensor,
        action_weights: torch.Tensor = None,
    ) -> torch.Tensor:
        """返回兴趣向量（不含分类头），用于推荐相似度计算。"""
        with torch.no_grad():
            emb = self.embedding(cid_seq)
            if action_weights is not None:
                w = (action_weights / action_weights.max(dim=1, keepdim=True).values.clamp(min=1))
                emb = emb * w.unsqueeze(-1)
            lstm_out, _ = self.lstm(emb)
            mask = (cid_seq == 0)
            context, _ = self._attend(lstm_out, mask)
        return context  # (batch, hidden_size)
