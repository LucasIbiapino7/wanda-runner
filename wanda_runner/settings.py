from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_timeout_ms_per_case: int = 2000
    max_timeout_ms_total: int = 10000
    log_level: str = "INFO"
    port: int = 8001

    class Config:
        env_file = ".env"

settings = Settings()