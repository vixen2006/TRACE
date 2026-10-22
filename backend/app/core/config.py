from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    postgres_url: str = "postgresql+asyncpg://trace_user:trace_pass@localhost:5432/trace_db"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/v1/integrations/github/callback"

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    # App
    secret_key: str = "changeme"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    environment: str = "development"
    encryption_key: str = "changeme_base64_32_bytes"
    token_encryption_key: str = "changeme_base64_32_bytes"
    session_cookie_name: str = "trace_session"
    session_cookie_secure: Optional[bool] = None

    # Agent limits
    agent_max_tool_calls: int = 30
    agent_max_seconds: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
