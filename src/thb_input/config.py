from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="THB_",
        extra="ignore",
    )

    app_name: str = "THB"
    env: str = "development"
    log_level: str = "INFO"
    llm_api_key: str | None = None
    strip_model: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout: float = Field(default=30.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    strip_temperature: float = Field(default=0.0, ge=0, le=2)
    strip_max_tokens: int = Field(default=4096, ge=1)
    strip_output_mode: Literal["json_schema", "json_object"] = "json_schema"
    llm_api_style: Literal["chat_completions", "responses"] = "chat_completions"
    strip_validation_retries: int = Field(default=1, ge=0, le=2)
    extract_model: str | None = None
    extract_temperature: float = Field(default=0.0, ge=0, le=2)
    extract_max_tokens: int = Field(default=8192, ge=1)
    extract_output_mode: Literal["json_schema", "json_object"] = "json_schema"
    extract_validation_retries: int = Field(default=2, ge=0, le=2)
    extract_timeout: float = Field(default=120.0, gt=0)
    strategize_model: str | None = None
    strategize_temperature: float = Field(default=0.0, ge=0, le=2)
    strategize_max_tokens: int = Field(default=8192, ge=1)
    strategize_output_mode: Literal["json_schema", "json_object"] = "json_schema"
    strategize_validation_retries: int = Field(default=2, ge=0, le=2)
    strategize_timeout: float = Field(default=120.0, gt=0)
    respond_model: str | None = None
    respond_temperature: float = Field(default=0.2, ge=0, le=2)
    respond_max_tokens: int = Field(default=2048, ge=1)
    respond_output_mode: Literal["json_schema", "json_object"] = "json_schema"
    respond_validation_retries: int = Field(default=2, ge=0, le=2)
    respond_timeout: float = Field(default=120.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
