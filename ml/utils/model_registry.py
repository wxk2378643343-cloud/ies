"""
模型版本管理：保存 / 加载 checkpoint，记录到数据库。
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

CHECKPOINT_DIR = Path(__file__).resolve().parents[2] / "ml" / "checkpoints"
CHECKPOINT_DIR.mkdir(exist_ok=True)

LATEST_LINK = CHECKPOINT_DIR / "latest.json"


def save_model(model, vocab_data: dict, metrics: dict) -> str:
    """保存模型权重 + 词表 + 超参，返回版本号。"""
    version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")
    ckpt_path = CHECKPOINT_DIR / f"{version}.pt"
    meta_path = CHECKPOINT_DIR / f"{version}_meta.json"

    torch.save(model.state_dict(), ckpt_path)

    meta = {
        "version": version,
        "vocab": vocab_data,
        "hparams": {
            "embed_dim": 64,
            "hidden_size": 128,
            "num_layers": 2,
            "dropout": 0.2,
        },
        "metrics": metrics,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    LATEST_LINK.write_text(json.dumps({"version": version}))

    # 写入数据库
    _write_train_log(version, metrics)

    print(f"[registry] 模型已保存: {version}")
    return version


def load_latest_model():
    """加载最新版本模型，返回 (model, meta)。"""
    from ml.models.lstm_attention import LSTMAttention

    if not LATEST_LINK.exists():
        return None, None
    version = json.loads(LATEST_LINK.read_text())["version"]
    return load_model(version)


def load_model(version: str):
    from ml.models.lstm_attention import LSTMAttention

    meta_path = CHECKPOINT_DIR / f"{version}_meta.json"
    ckpt_path = CHECKPOINT_DIR / f"{version}.pt"
    if not meta_path.exists():
        raise FileNotFoundError(f"模型版本不存在: {version}")

    meta = json.loads(meta_path.read_text())
    vocab_data = meta["vocab"]
    hp = meta["hparams"]

    model = LSTMAttention(
        num_contents=vocab_data["num_contents"],
        num_categories=vocab_data["num_categories"],
        embed_dim=hp["embed_dim"],
        hidden_size=hp["hidden_size"],
        num_layers=hp["num_layers"],
        dropout=hp["dropout"],
    )
    model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
    model.eval()
    return model, meta


def list_versions() -> list[dict]:
    versions = []
    for f in sorted(CHECKPOINT_DIR.glob("*_meta.json"), reverse=True):
        meta = json.loads(f.read_text())
        versions.append({
            "version": meta["version"],
            "metrics": meta.get("metrics", {}),
        })
    return versions


def _write_train_log(version: str, metrics: dict):
    try:
        from sqlalchemy.orm import sessionmaker
        from backend.models.orm_models import engine, ModelTrainLog
        Session = sessionmaker(bind=engine)
        db = Session()
        log = ModelTrainLog(
            version=version,
            loss=metrics.get("val_loss"),
            accuracy=metrics.get("val_accuracy"),
            precision_at_k=metrics.get("precision@5"),
            recall_at_k=metrics.get("recall@5"),
            ndcg=metrics.get("ndcg@5"),
            note=json.dumps(metrics, ensure_ascii=False),
        )
        db.add(log)
        db.commit()
        db.close()
    except Exception as e:
        print(f"[registry] 写入数据库失败（不影响模型保存）: {e}")
