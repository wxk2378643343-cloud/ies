"""
pytest 公共夹具：
- 测试专用 SQLite 数据库（每次会话重建）
- FastAPI TestClient（依赖注入覆盖）
- 预置管理员 / 普通用户 token
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.orm_models import Base, User
from backend.utils.auth import hash_password, create_access_token
from backend.utils.deps import get_db

TEST_DB_URL = "sqlite:///./tests/ies_test.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """在测试会话开始时建表，结束时清理。"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client(setup_test_db):
    from backend.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def admin_token(setup_test_db):
    db = TestingSession()
    admin = User(
        username="test_admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return create_access_token({"sub": str(admin.id)})


@pytest.fixture(scope="session")
def user_token(setup_test_db):
    db = TestingSession()
    user = User(
        username="test_user",
        email="user@test.com",
        password_hash=hash_password("user123"),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return create_access_token({"sub": str(user.id)})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
