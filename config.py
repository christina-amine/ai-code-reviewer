from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: Literal["claude", "gemini", "openai"] = "claude"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"

    # Session
    session_secret: str = "your-secret-key-change-this"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
