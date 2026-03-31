import torch
from torch.utils.data import Dataset


class BehaviorDataset(Dataset):
    """
    每条样本：
      - cid_seq    : LongTensor (seq_len,)  内容 id 索引序列
      - weight_seq : FloatTensor (seq_len,) 行为权重序列
      - label      : int                    目标类别索引
    """

    def __init__(self, sequences: list[tuple]):
        self.data = sequences

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        cid_seq, weight_seq, label = self.data[idx]
        return (
            torch.tensor(cid_seq, dtype=torch.long),
            torch.tensor(weight_seq, dtype=torch.float),
            torch.tensor(label, dtype=torch.long),
        )
