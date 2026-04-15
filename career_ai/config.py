from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "career-ai"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG = Path(__file__).parent / "default_config.yaml"


class ModelConfig(BaseModel):
    default: str = "gpt-4o"
    fallback: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.1


class TokenConfig(BaseModel):
    max_input_limit: int = 16000
    max_output_limit: int = 2000
    warn_cost_threshold: float = 0.10


class AppConfig(BaseModel):
    log_usage: bool = True
    usage_db_path: str = "~/.config/career-ai/usage.db"
    max_cover_letter_words: int = 120


class Config(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    tokens: TokenConfig = Field(default_factory=TokenConfig)
    app: AppConfig = Field(default_factory=AppConfig)

    @property
    def usage_db(self) -> Path:
        return Path(self.app.usage_db_path).expanduser()


def init_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        shutil.copy(DEFAULT_CONFIG, CONFIG_PATH)
    return CONFIG_PATH


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        return Config()
    with CONFIG_PATH.open() as f:
        data = yaml.safe_load(f) or {}
    return Config.model_validate(data)


def set_config_value(key: str, value: str) -> None:
    init_config()
    with CONFIG_PATH.open() as f:
        data = yaml.safe_load(f) or {}

    section, _, field = key.partition(".")
    if field:
        data.setdefault(section, {})[field] = value
    else:
        data[key] = value

    with CONFIG_PATH.open("w") as f:
        yaml.dump(data, f, default_flow_style=False)
