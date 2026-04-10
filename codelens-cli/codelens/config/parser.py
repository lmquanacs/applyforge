import os
import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG = {
    "output_file": "project_overview.md",
    "project_hint": None,
    "ignore_patterns": ["target/**", "build/**", ".idea/**", ".git/**", "venv/**", "__pycache__/**"],
    "agents": {
        "coordinator": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5",
            "temperature": 0.2,
        },
        "worker": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5",
            "temperature": 0.1,
            "max_concurrent_workers": 5,
        },
    },
}


def load_config(config_path: str = None, overrides: dict = None) -> dict:
    config = DEFAULT_CONFIG.copy()
    config["agents"] = {
        "coordinator": DEFAULT_CONFIG["agents"]["coordinator"].copy(),
        "worker": DEFAULT_CONFIG["agents"]["worker"].copy(),
    }

    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        _deep_merge(config, file_config)
    elif os.path.exists("codelens.config.yaml"):
        with open("codelens.config.yaml") as f:
            file_config = yaml.safe_load(f) or {}
        _deep_merge(config, file_config)

    if overrides:
        for k, v in overrides.items():
            if v is not None:
                config[k] = v

    return config


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
