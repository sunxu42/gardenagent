from typing import Optional, Dict, Any
from loguru import logger
import importlib


agent_to_class = {
    "garden_robot": "brain_langchain.scenario_one.ScenarioOneApp",
}
def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class AgentFactory:

    @classmethod
    def create_agent(cls, config: Dict[str, Any]=None) -> Any:
        agent_type: str = config.get("agent_type")
        class_type = agent_to_class.get(agent_type)
        if not class_type:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        agent_class = load_class(class_type)
        return agent_class(config)
    
    @classmethod
    async def async_create_app(cls, config: Dict[str, Any]=None) -> Any:
        agent_type: str = config.get("agent_type")
        class_type = agent_to_class.get(agent_type)
        if not class_type:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        agent_class = load_class(class_type)
        return await agent_class.create(config)