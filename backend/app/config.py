from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str | None = None
    groq_model: str = "gemma2-9b-it"
    database_url: str = "sqlite:///./aivoa.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

