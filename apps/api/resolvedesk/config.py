from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    auth_url: str = "http://localhost:3000"
    app_origin: str = "http://localhost:3000"
    demo_enabled: bool = True
    live_ai_enabled: bool = False
    deepseek_api_key: SecretStr | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def has_deepseek_key(self) -> bool:
        return bool(self.deepseek_api_key and self.deepseek_api_key.get_secret_value().strip())


settings = Settings()  # pyright: ignore[reportCallIssue] # BaseSettings reads required values from env.
