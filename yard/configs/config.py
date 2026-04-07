import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import yaml

CWD = os.getcwd()
DEFAULT_CONFIG_FILE = os.path.join(CWD, ".config.yaml")
DEFAULT_ENV_FILE = os.path.join(CWD, ".env")
PROVIDER_ENV_KEY = {
    "glm": ("GLM_OPENAI_API_KEY", "GLM_OPENAI_BASE_URL"),
}
SUPPORT_LLM_PROVIDERS = PROVIDER_ENV_KEY.keys()

load_dotenv(DEFAULT_ENV_FILE)

class Config(BaseModel):
    skills_dir: str = "skills"
    workspace_dir: str = "yard/workspace"

    subagents_yaml: str = "yard/configs/subagents.yaml"
    mcp_servers_yaml: str = "yard/configs/mcp_servers.yaml"
    agents_md: str = "AGENTS.md"
    goal_md: str = "GOAL.md"
    user_md: str = "USER.md"

    mem0_api_key: Optional[str] = None
    llm_provider: Optional[str] = Field(default="glm")
    llm_api_key: Optional[str] = Field(default=None)
    llm_base_url: Optional[str] = Field(default=None)
    llm_model_name: Optional[str] = Field(default="glm-4-flash")


def _read_yaml(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def load_config(runtime_config: Optional[dict] = None) -> Config:
    if not os.path.isfile(DEFAULT_CONFIG_FILE):
        raw: dict = {}
    else:
        loaded = _read_yaml(DEFAULT_CONFIG_FILE)
        raw = loaded if isinstance(loaded, dict) else {}
    config = Config(**raw)
    api_key, base_url = PROVIDER_ENV_KEY.get(config.llm_provider.lower(), (None, None))
    
    config.llm_api_key = os.getenv(api_key)
    config.llm_base_url = os.getenv(base_url)

    if not config.llm_api_key or not config.llm_base_url:
        raise ValueError(f"LLM API key and base url are required for {config.llm_model_name}")

    # validate if none, raise error
    if not config.llm_model_name or not config.llm_base_url or not config.llm_api_key:
        raise ValueError("LLM model name, base url, and api key are required")

    return config

