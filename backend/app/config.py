from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str
    database_url: str = "sqlite:///./batches.db"
    webhook_timeout: int = 5
    webhook_max_retries: int = 3

    class Config:
        env_file = "../.env"


settings = Settings()