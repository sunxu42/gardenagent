import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config(BaseModel):
    skills_dir: str = "yard/skills"
    workspace_dir: str = "yard/workspace"

    subagents_yaml: str = "yard/configs/subagents.yaml"
    mcp_servers_yaml: str = "yard/configs/mcp_servers.yaml"
    agents_md: str = "yard/internal/AGENTS.md"
    goal_md: str = "yard/internal/GOAL.md"
    user_md: str = "yard/internal/USER.md"

    mem0_api_key: Optional[str] = None

    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model_name: Optional[str] = None

    def add_config(self, config: dict):
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)


def load_config() -> Config:
    config = Config(
        mem0_api_key=os.getenv("MEM0_API_KEY"),
        llm_model_name=os.getenv("LLM_MODEL_NAME"),
    )

    if config.llm_model_name and "glm" in config.llm_model_name:
        config.llm_api_key = os.getenv("GLM_OPENAI_API_KEY")
        config.llm_base_url = os.getenv("GLM_OPENAI_BASE_URL")

    # validate if none, raise error
    if not config.llm_model_name or not config.llm_base_url or not config.llm_api_key:
        raise ValueError("LLM model name, base url, and api key are required")

    return config

