from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    env: Literal["dev", "demo", "test"] = "dev"

    llm_mode: Literal["bedrock", "cloud", "local", "mock"] = "mock"
    featherless_api_key: str = ""
    aws_bearer_token_bedrock: str = ""
    aws_region: str = "us-west-2"
    bedrock_model_extract: str = "us.anthropic.claude-haiku-5-5"
    bedrock_model_reason: str = "us.anthropic.claude-sonnet-5-5"
    bedrock_model_deep: str = "us.anthropic.claude-opus-5-5"
    ollama_url: str = "http://127.0.0.1:11434"
    model_extract: str = "deepseek-ai/DeepSeek-V4-Flash"
    model_reason: str = "deepseek-ai/DeepSeek-V4-Flash"
    model_vision: str = "Qwen/Qwen3.8-Flash-Next"
    model_local: str = ""
    llm_max_concurrency: int = 2
    llm_timeout_s: int = 30
    demo_cache: bool = False
    llm_record: bool = False  # true = salvează răspunsurile în data/llm_cache (pt. demo offline)

    hmac_secret: str = ""
    arena_hmac_secret: str = ""
    vault_key: str = ""
    he_enabled: bool = True
    detector_gpu: Literal["on", "off"] = "off"
    tesseract_cmd: str = ""

    bank_ui_token: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:4173"
    cors_origin_regex: str = r"https://.*\.vercel\.app"
    database_url: str = f"sqlite:///{REPO_ROOT / 'backend' / 'orb.db'}"
    vault_database_url: str = f"sqlite:///{REPO_ROOT / 'backend' / 'vault.db'}"

    arena_rate_limit_per_min: int = 5
    arena_max_file_mb: int = 5

    manual_minutes_per_case: float = 20
    review_minutes_per_case: float = 1
    cost_per_hour_ron: float = 60

    @model_validator(mode="after")
    def _require_secrets(self):
        if self.env == "test":
            return self
        for name in ("hmac_secret", "arena_hmac_secret", "vault_key", "bank_ui_token"):
            value = getattr(self, name)
            if not value or value.lstrip().startswith("#"):
                raise ValueError(f"{name.upper()} lipsește sau e invalid în .env (vezi .env.example)")
        return self


settings = Settings()
