from typing import Any

from server.multimodal.common.importlib_registry import load_class


BACKEND_REGISTRY = {
    "robot": "server.multimodal.session.backends.robot_agent.RobotAgent",
    "garden_robot": "garden_agent.scenario_one.ScenarioOneApp",
    "agent_manager": "agent.manager.AgentManager",
    "yard_manager": "agent.manager.AgentManager",
}


class SessionBackendFactory:
    @classmethod
    def create_backend(cls, config: dict[str, Any] | None = None) -> Any:
        agent_type: str = config.get("agent_type")
        class_type = BACKEND_REGISTRY.get(agent_type)
        if not class_type:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        backend_class = load_class(class_type)
        return backend_class(config)

    @classmethod
    async def async_create_backend(cls, config: dict[str, Any] | None = None) -> Any:
        agent_type: str = config.get("agent_type")
        class_type = BACKEND_REGISTRY.get(agent_type)
        if not class_type:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        backend_class = load_class(class_type)
        return await backend_class.create(config)
