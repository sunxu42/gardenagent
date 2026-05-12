import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import yaml

CWD = os.getcwd()
DEFAULT_CONFIG_FILE = os.path.join(CWD, ".config.yaml")
DEFAULT_ENV_FILE = os.path.join(CWD, ".env")
PROVIDER_SETTINGS = {
    "glm": {
        "api_key_env": "GLM_OPENAI_API_KEY",
        "base_url_env": "GLM_OPENAI_BASE_URL",
        "default_api_key": None,
        "default_base_url": None,
    },
    "ollama": {
        "api_key_env": "OLLAMA_OPENAI_API_KEY",
        "base_url_env": "OLLAMA_OPENAI_BASE_URL",
        "default_api_key": None,
        "default_base_url": None,
    },
}
SUPPORT_LLM_PROVIDERS = PROVIDER_SETTINGS.keys()

load_dotenv(DEFAULT_ENV_FILE)

class Config(BaseModel):
    skills_dir: str = "skills"
    workspace_dir: str = "yard/workspace"
    prompts_dir: str = "yard/prompts"

    subagents_yaml: str = "yard/configs/subagents.yaml"
    mcp_servers_yaml: str = "yard/configs/mcp_servers.yaml"

    mem0_api_key: Optional[str] = None
    llm_provider: Optional[str] = Field(default="glm")
    llm_api_key: Optional[str] = Field(default=None)
    llm_base_url: Optional[str] = Field(default=None)
    llm_model_name: Optional[str] = Field(default="glm-4-flash")


def _read_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def load_config(runtime_config: Optional[dict] = None) -> Config:
    if not os.path.isfile(DEFAULT_CONFIG_FILE):
        raw: dict = {}
    else:
        loaded = _read_yaml(DEFAULT_CONFIG_FILE)
        raw = loaded if isinstance(loaded, dict) else {}
    if runtime_config:
        raw.update(runtime_config)
    config = Config(**raw)

    provider = (config.llm_provider or "").lower()
    settings = PROVIDER_SETTINGS.get(provider)
    if settings is None:
        supported = ", ".join(sorted(SUPPORT_LLM_PROVIDERS))
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider!r}. Supported providers: {supported}")

    api_key_env = settings["api_key_env"]
    base_url_env = settings["base_url_env"]

    config.llm_api_key = (
        config.llm_api_key
        or os.getenv(api_key_env)
        or settings["default_api_key"]
    )
    config.llm_base_url = (
        config.llm_base_url
        or os.getenv(base_url_env)
        or settings["default_base_url"]
    )

    if not config.llm_api_key or not config.llm_base_url:
        raise ValueError(
            f"LLM API key and base url are required for provider {provider!r} "
            f"and model {config.llm_model_name!r}"
        )

    # validate if none, raise error
    if not config.llm_model_name or not config.llm_base_url or not config.llm_api_key:
        raise ValueError("LLM model name, base url, and api key are required")

    return config

