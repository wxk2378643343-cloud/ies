from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "IES - 兴趣演化预测系统"
    database_url: str = "sqlite:///./database/ies.db"
    secret_key: str = "change-this-in-production-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    class Config:
        env_file = ".env"


settings = Settings()
