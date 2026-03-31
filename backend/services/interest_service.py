"""
兴趣服务：训练触发 + 定时增量更新。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def trigger_training(epochs: int = 20) -> dict:
    """手动或定时触发完整训练，返回评估指标。"""
    from ml.training.trainer import train
    return train(epochs=epochs)


def run_inference_for_user(user_id: int, top_n: int = 10) -> dict:
    """对单个用户运行推理，更新 interest_tags 并返回推荐结果。"""
    from ml.utils.inference import predict_user_interest
    return predict_user_interest(user_id=user_id, top_n=top_n)


def batch_update_all_users():
    """批量更新所有活跃用户的兴趣标签（定时任务调用）。"""
    from sqlalchemy.orm import sessionmaker
    from backend.models.orm_models import engine, User
    from ml.utils.inference import predict_user_interest

    Session = sessionmaker(bind=engine)
    db = Session()
    users = db.query(User.id).filter(User.role == "user").all()
    db.close()

    success, failed = 0, 0
    for (uid,) in users:
        try:
            predict_user_interest(uid, top_n=10)
            success += 1
        except Exception as e:
            failed += 1
            print(f"[interest_service] user {uid} 推理失败: {e}")

    print(f"[interest_service] 批量更新完成: {success} 成功 / {failed} 失败")
    return {"success": success, "failed": failed}
