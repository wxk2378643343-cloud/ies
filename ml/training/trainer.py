"""
LSTM+Attention 模型训练脚本。

用法：
  python -m ml.training.trainer [--epochs 20] [--batch_size 64] [--seq_len 20]

也可作为函数调用：
  from ml.training.trainer import train
  result = train()
"""
import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.data.preprocess import build_dataset
from ml.data.dataset import BehaviorDataset
from ml.models.lstm_attention import LSTMAttention
from ml.evaluation.metrics import evaluate_batch, ndcg_at_k, precision_at_k, recall_at_k
from ml.utils.model_registry import save_model


def train(
    epochs: int = 20,
    batch_size: int = 64,
    seq_len: int = 20,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    val_ratio: float = 0.2,
) -> dict:
    print("[trainer] 开始数据预处理...")
    sequences, vocab, cat2idx = build_dataset(seq_len=seq_len)

    if len(sequences) == 0:
        print("[trainer] 样本不足，请先运行 generate_mock_data.py")
        return {}

    dataset = BehaviorDataset(sequences)
    val_size = max(1, int(len(dataset) * val_ratio))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    num_contents = len(vocab)
    num_categories = len(cat2idx)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[trainer] 设备: {device}  训练样本: {train_size}  验证样本: {val_size}")

    model = LSTMAttention(
        num_contents=num_contents,
        num_categories=num_categories,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_loss = float("inf")
    best_state = None
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    for epoch in range(1, epochs + 1):
        # --- Train ---
        model.train()
        total_loss = 0.0
        for cid, weights, labels in train_loader:
            cid, weights, labels = cid.to(device), weights.to(device), labels.to(device)
            optimizer.zero_grad()
            logits, _ = model(cid, weights)
            loss = criterion(logits, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()
        avg_train_loss = total_loss / len(train_loader)

        # --- Validate ---
        model.eval()
        val_loss, correct, total = 0.0, 0, 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for cid, weights, labels in val_loader:
                cid, weights, labels = cid.to(device), weights.to(device), labels.to(device)
                logits, _ = model(cid, weights)
                val_loss += criterion(logits, labels).item()
                preds = logits.argmax(dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
                all_preds.extend(preds.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())

        avg_val_loss = val_loss / len(val_loader)
        val_acc = correct / total if total else 0

        history["train_loss"].append(round(avg_train_loss, 4))
        history["val_loss"].append(round(avg_val_loss, 4))
        history["val_acc"].append(round(val_acc, 4))

        print(f"  Epoch {epoch:02d}/{epochs}  "
              f"train_loss={avg_train_loss:.4f}  "
              f"val_loss={avg_val_loss:.4f}  "
              f"val_acc={val_acc:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        scheduler.step()

    # 加载最佳权重
    model.load_state_dict(best_state)
    model.eval()

    # 计算推荐指标（把类别预测视为 Top-1 推荐）
    idx2cat = {v: k for k, v in cat2idx.items()}
    recommended_list = [[idx2cat[p]] for p in all_preds]
    relevant_list = [{idx2cat[l]} for l in all_labels]

    rank_metrics = evaluate_batch(recommended_list, relevant_list, k=1)
    final_metrics = {
        "val_loss": round(best_val_loss, 4),
        "val_accuracy": round(history["val_acc"][-1], 4),
        **rank_metrics,
        "history": history,
    }

    from ml.data.preprocess import load_vocab
    vocab_data = load_vocab()
    version = save_model(model, vocab_data, final_metrics)
    final_metrics["version"] = version

    print(f"[trainer] 训练完成  版本: {version}  最佳 val_loss: {best_val_loss:.4f}")
    return final_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--seq_len", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size,
          seq_len=args.seq_len, lr=args.lr)
