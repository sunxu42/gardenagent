"""
Agent Factory - 用于创建和管理 Agent 实例
"""
from typing import Optional, Dict, Any
from loguru import logger
from .agent_adapter import RobotAgent, ClientState


class AgentFactory:
    """Agent 工厂类，负责创建和管理 Agent 实例"""
    
    @staticmethod
    def create_agent(
        agent_type: str = "robot",
        origin_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        client_state: Optional[ClientState] = None,
        **kwargs
    ) -> RobotAgent:
        """
        创建 Agent 实例
        
        Args:
            agent_type: Agent 类型，默认为 "robot"
            origin_config: 原始配置字典
            session_id: 会话ID，默认为 "text_listener_session"
            client_state: 客户端状态，如果为 None 则创建新的 ClientState
            **kwargs: 其他传递给 Agent 的参数
            
        Returns:
            RobotAgent: 创建的 Agent 实例
            
        Raises:
            ValueError: 如果 agent_type 不支持
        """
        if origin_config is None:
            origin_config = {}
        
        if session_id is None:
            session_id = "text_listener_session"
        
        if client_state is None:
            client_state = ClientState()
        
        if agent_type == "robot":
            logger.info(f"创建 RobotAgent 实例，session_id: {session_id}")
            agent = RobotAgent(
                origin_config=origin_config,
                session_id=session_id,
                client_state=client_state,
                **kwargs
            )
            return agent
        else:
            raise ValueError(f"不支持的 agent_type: {agent_type}")
    
    @staticmethod
    def create_default_agent() -> RobotAgent:
        """
        创建默认配置的 Agent 实例
        
        Returns:
            RobotAgent: 默认配置的 Agent 实例
        """
        return AgentFactory.create_agent()

