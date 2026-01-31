# src/secql_api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    supabase_url: str = ""
    supabase_key: str = ""
    sec_user_agent: str = "SecQL API contact@secql.dev"

    # For local testing only
    secql_test_api_key: str = ""


settings = Settings()
