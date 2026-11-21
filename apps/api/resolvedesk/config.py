from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    auth_url: str = "http://localhost:3000"
    app_origin: str = "http://localhost:3000"
    demo_enabled: bool = True
    public_demo_only: bool = False
    cron_secret: SecretStr | None = None
    live_ai_enabled: bool = False
    deepseek_api_key: SecretStr | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    @field_validator("database_url", mode="before")
    @classmethod
    def postgres_driver(cls, value):
        if isinstance(value, str) and value.startswith(("postgres://", "postgresql://")):
            return "postgresql+psycopg://" + value.split("://", 1)[1]
        return value

    @property
    def has_deepseek_key(self) -> bool:
        return bool(self.deepseek_api_key and self.deepseek_api_key.get_secret_value().strip())

    @model_validator(mode="after")
    def public_provider_boundary(self):
        if self.public_demo_only and self.live_ai_enabled:
            raise ValueError("Public demo deployment requires LIVE_AI_ENABLED=false.")
        if self.public_demo_only and (
            not self.cron_secret or len(self.cron_secret.get_secret_value()) < 32
        ):
            raise ValueError(
                "Public demo deployment requires a maintenance secret of at least 32 characters."
            )
        return self


settings = Settings()  # pyright: ignore[reportCallIssue] # BaseSettings reads required values from env.
