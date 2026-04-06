from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    db_host: str
    db_port: int = 5432
    db_name: str = "tracktheticket"
    db_username: str
    db_password: str

    # AWS
    aws_region: str = "us-east-1"
    screenshots_bucket: str

    # Auth
    cognito_user_pool_id: str
    cognito_region: str = "us-east-1"

    # AI / OpenRouter
    openrouter_api_key: str = ""
    price_checker_model: str = "google/gemini-2.5-flash"

    # App
    environment: str = "prod"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
