"""YouTube AI Factory v4.1 — Config Loader (.env + pipeline.yaml)"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"


def _load_env():
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        example = CONFIG_DIR / ".env.example"
        if example.exists():
            load_dotenv(example)


def _load_pipeline_yaml() -> dict:
    yaml_file = CONFIG_DIR / "pipeline.yaml"
    if not yaml_file.exists():
        return {}
    with open(yaml_file) as f:
        return yaml.safe_load(f) or {}


# Load once at import
_load_env()
_pipeline = _load_pipeline_yaml()


def get_env(key: str, default=None) -> str:
    return os.getenv(key, default)


def get_pipeline(*keys: str, default=None):
    """Deep get from pipeline config, e.g. get_pipeline('providers', 'kieai', 'batch_size')"""
    node = _pipeline
    for k in keys:
        if isinstance(node, dict):
            node = node.get(k)
        else:
            return default
        if node is None:
            return default
    return node


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}. Set in configs/.env")
    return val
