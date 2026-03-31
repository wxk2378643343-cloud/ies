from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from backend.config.settings import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(Enum("user", "admin", name="user_role"), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    behaviors = relationship("Behavior", back_populates="user")
    interest_tags = relationship("InterestTag", back_populates="user")
    model_results = relationship("ModelResult", back_populates="user")


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    tags_json = Column(Text, default="[]")  # JSON array of tag strings
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum("published", "draft", "removed", name="content_status"), default="published")
    created_at = Column(DateTime, default=datetime.utcnow)

    behaviors = relationship("Behavior", back_populates="content")


class Behavior(Base):
    __tablename__ = "behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    action = Column(Enum("click", "collect", "read", name="behavior_action"), nullable=False)
    duration_sec = Column(Float, default=0.0)  # time spent reading, in seconds
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="behaviors")
    content = relationship("Content", back_populates="behaviors")


class InterestTag(Base):
    __tablename__ = "interest_tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tag = Column(String(50), nullable=False)
    weight = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="interest_tags")


class ModelResult(Base):
    __tablename__ = "model_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    predicted_tags_json = Column(Text, default="[]")  # JSON array of {tag, score}
    confidence = Column(Float, default=0.0)
    model_version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="model_results")


class ModelTrainLog(Base):
    __tablename__ = "model_train_logs"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, unique=True)
    loss = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    precision_at_k = Column(Float, nullable=True)
    recall_at_k = Column(Float, nullable=True)
    ndcg = Column(Float, nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, default="")


def init_db():
    Base.metadata.create_all(bind=engine)
