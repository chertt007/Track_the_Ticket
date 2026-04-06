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

    # AI / OpenRouter (local dev only — in production the agent runs in price-checker Lambda)
    openrouter_api_key: str = ""
    price_checker_model: str = "google/gemini-2.5-flash"

    # SQS queue URL for price-checker Lambda.
    # When set, POST /check sends a message to SQS instead of running the agent inline.
    # Leave empty in local dev to keep the synchronous (direct) mode.
    price_checker_queue_url: str = ""

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
