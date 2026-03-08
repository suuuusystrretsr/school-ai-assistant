from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='SCHOOL AI ASSISTANT API', alias='APP_NAME')
    env: str = Field(default='development', alias='ENV')
    api_prefix: str = Field(default='/api/v1', alias='API_PREFIX')
    api_url: str = Field(default='http://localhost:8000/api/v1', alias='API_URL')
    site_url: str = Field(default='https://schoolaiassistant.local', alias='SITE_URL')

    # SQLite default for fastest free-tier deployment. Postgres is optional later.
    database_url: str = Field(default='sqlite:///./school_ai_assistant.db', alias='DATABASE_URL')

    jwt_secret: str = Field(default='change-me-in-production', alias='JWT_SECRET')
    jwt_algorithm: str = Field(default='HS256', alias='JWT_ALGORITHM')
    jwt_expires_minutes: int = Field(default=10080, alias='JWT_EXPIRES_MINUTES')

    # Comma-separated origins. Use '*' for quick MVP CORS.
    cors_origins: str = Field(default='*', alias='CORS_ORIGINS')

    ai_provider: str = Field(default='mock', alias='AI_PROVIDER')
    ai_model: str = Field(default='mock-edu-v1', alias='AI_MODEL')
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    hf_api_key: str | None = Field(default=None, alias='HF_API_KEY')
    hf_model_id: str = Field(default='Qwen/Qwen2.5-7B-Instruct', alias='HF_MODEL_ID')
    hf_timeout_seconds: int = Field(default=35, alias='HF_TIMEOUT_SECONDS')
    hf_max_new_tokens: int = Field(default=500, alias='HF_MAX_NEW_TOKENS')

    @property
    def runtime_database_url(self) -> str:
        # Render free web services can be strict about writable paths.
        # If using the relative SQLite path in production, redirect to /tmp.
        if self.env == 'production' and self.database_url.startswith('sqlite:///./'):
            return 'sqlite:////tmp/school_ai_assistant.db'
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

