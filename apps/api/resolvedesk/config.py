from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    auth_url: str = "http://localhost:3000"
    app_origin: str = "http://localhost:3000"
    demo_enabled: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # pyright: ignore[reportCallIssue] # BaseSettings reads required values from env.
