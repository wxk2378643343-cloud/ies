"""
生成模拟数据，用于开发调试和模型冷启动。
运行方式：在项目根目录执行
    python -m database.seeds.generate_mock_data
"""
import json
import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import sessionmaker
from backend.models.orm_models import engine, init_db, User, Content, Behavior, InterestTag, ModelTrainLog
from backend.utils.auth import hash_password

SessionLocal = sessionmaker(bind=engine)

CATEGORIES = ["科技", "体育", "娱乐", "财经", "教育", "健康", "游戏", "旅游"]
ACTIONS = ["click", "read", "collect"]

SAMPLE_TITLES = {
    "科技": ["Python 3.12 新特性", "大模型推理加速技术", "边缘计算最新进展", "量子计算突破"],
    "体育": ["世界杯预选赛综述", "NBA季后赛分析", "马拉松训练计划", "游泳技巧提升"],
    "娱乐": ["年度票房榜单", "热门剧集推荐", "音乐节回顾", "明星采访精选"],
    "财经": ["A股市场分析", "美联储利率决议", "比特币行情解读", "房地产政策解读"],
    "教育": ["考研数学备考指南", "英语四六级技巧", "编程入门路径", "大学选专业建议"],
    "健康": ["睡眠质量提升方法", "饮食营养搭配", "健身初学者指南", "心理健康维护"],
    "游戏": ["热门手游排行", "PC端新游速递", "电竞赛事直播", "独立游戏推荐"],
    "旅游": ["国内十大景区", "东南亚自由行攻略", "欧洲签证指南", "民宿预订技巧"],
}


def seed():
    init_db()
    db = SessionLocal()

    # 创建管理员
    admin = User(
        username="admin",
        email="admin@ies.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)

    # 创建普通用户
    users = []
    for i in range(1, 11):
        u = User(
            username=f"user{i:02d}",
            email=f"user{i:02d}@ies.com",
            password_hash=hash_password("password123"),
        )
        db.add(u)
        users.append(u)

    db.commit()

    # 创建内容
    contents = []
    for cat, titles in SAMPLE_TITLES.items():
        for title in titles:
            c = Content(
                title=title,
                body=f"这是关于{title}的详细内容，涵盖最新的行业动态与深度分析。" * 5,
                category=cat,
                tags_json=json.dumps([cat, title[:4]], ensure_ascii=False),
                author_id=admin.id,
            )
            db.add(c)
            contents.append(c)

    db.commit()

    # 生成行为日志（每个用户 30-60 条）
    now = datetime.utcnow()
    for user in users:
        # 给每个用户分配 1-3 个偏好分类（模拟兴趣偏向）
        preferred = random.sample(CATEGORIES, k=random.randint(1, 3))
        preferred_contents = [c for c in contents if c.category in preferred]
        other_contents = [c for c in contents if c.category not in preferred]

        pool = preferred_contents * 3 + other_contents  # 偏好内容权重更高
        n_behaviors = random.randint(30, 60)

        for j in range(n_behaviors):
            content = random.choice(pool)
            action = random.choices(ACTIONS, weights=[5, 3, 2])[0]
            b = Behavior(
                user_id=user.id,
                content_id=content.id,
                action=action,
                duration_sec=random.uniform(5, 300) if action == "read" else 0,
                timestamp=now - timedelta(days=random.randint(0, 30),
                                          hours=random.randint(0, 23)),
            )
            db.add(b)

        # 初始化兴趣标签
        for cat in preferred:
            tag = InterestTag(
                user_id=user.id,
                tag=cat,
                weight=round(random.uniform(0.5, 1.0), 3),
            )
            db.add(tag)

    # 生成模拟训练历史（5个版本，模拟模型逐步收敛）
    mock_logs = [
        {"days_ago": 30, "loss": 2.1032, "acc": 0.3241, "p": 0.3105, "r": 0.4820, "ndcg": 0.3560},
        {"days_ago": 22, "loss": 1.8764, "acc": 0.3890, "p": 0.3714, "r": 0.5301, "ndcg": 0.4012},
        {"days_ago": 15, "loss": 1.5421, "acc": 0.4532, "p": 0.4230, "r": 0.5890, "ndcg": 0.4621},
        {"days_ago": 7,  "loss": 1.2108, "acc": 0.5214, "p": 0.5012, "r": 0.6470, "ndcg": 0.5380},
        {"days_ago": 1,  "loss": 0.9876, "acc": 0.5983, "p": 0.5731, "r": 0.7021, "ndcg": 0.6024},
    ]
    for i, m in enumerate(mock_logs):
        t = now - timedelta(days=m["days_ago"])
        version = t.strftime("v%Y%m%d_%H%M%S")
        log = ModelTrainLog(
            version=version,
            loss=m["loss"],
            accuracy=m["acc"],
            precision_at_k=m["p"],
            recall_at_k=m["r"],
            ndcg=m["ndcg"],
            trained_at=t,
            note=json.dumps({"epochs": 20, "train_samples": 350 + i * 10}, ensure_ascii=False),
        )
        db.add(log)
    db.commit()

    db.close()
    print(f"种子数据生成完成：1 管理员 + {len(users)} 用户 + {len(contents)} 内容 + 5 条训练记录")


if __name__ == "__main__":
    seed()
