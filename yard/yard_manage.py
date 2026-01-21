import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/home/diska/ongoing/gardenAgent/yard/.env") 
import asyncio
import yaml
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AIMessageChunk

GLM_API_KEY = os.getenv('GLM_OPENAI_API_KEY')
GLM_BASE_URL = os.getenv('GLM_OPENAI_BASE_URL')
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8000/mcp')
SKILLS_DIR = os.getenv('SKILLS_DIR', os.path.join(os.path.dirname(__file__), './skills'))
WORK_DIR = os.getenv('WORK_DIR', os.path.join(os.path.dirname(__file__), './workspace'))
SUBAGENTS_YAML = os.getenv('SUBAGENTS_YAML', os.path.join(os.path.dirname(__file__), './subagents.yaml'))

def create_glm_model():

    model = ChatOpenAI(
        model="glm-4.7",  
        api_key=GLM_API_KEY,
        base_url=GLM_BASE_URL,
        temperature=0.7,
        max_tokens=20000,
        streaming=True,
    )
    return model

def create_mcp_client():
    mcp_client = MultiServerMCPClient(
            {
                "weather": {
                    "url": MCP_SERVER_URL,
                    "transport": "http",
                }
            }
        )
    return mcp_client

def load_subagents(config_path) -> list:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    available_tools = {}
    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        if "model" in spec:
            subagent["model"] = spec["model"]
        if "tools" in spec:
            avt = []
            for t in spec["tools"]:
                if t in available_tools:
                    avt.append(available_tools[t])

            subagent["tools"] = avt
        subagents.append(subagent)

    return subagents


class YardManager:

    def __init__(self, config=None):
        self.config = config
        pass
    
    @classmethod
    async def create(cls, config=None):
        yard_manager = cls(config)
        mcp_client = create_mcp_client()
        yard_manager.tools = await mcp_client.get_tools()
        yard_manager.agent = agent = create_deep_agent(
            model=create_glm_model(),
            tools=yard_manager.tools, 
            memory=["./AGENTS.md"],
            skills=[SKILLS_DIR], 
            subagents=load_subagents(SUBAGENTS_YAML),
            backend=FilesystemBackend(root_dir=WORK_DIR),
            checkpointer=MemorySaver(),  
        )
        return yard_manager


    async def achat(self, user_input: str, thread_id = "yard-manager-demo"):
        async for chunk, _ in self.agent.astream(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    yield {"content": chunk.content}
                if chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        name = tool_call.get("name", "unknown")
                        args = tool_call.get("args", {})
                        yield {"updates": f">> 调用工具: {name}"}
                
            elif isinstance(chunk, ToolMessage):
                name = chunk.name 
                # print({"updates": f"{name}调用工具结束"})
                pass
            
     
            
           


if __name__ == "__main__":
    async def main():
        res = ""
        yard_manager = await YardManager.create()
        async for chunk in yard_manager.achat("查一下草的高度"):
            content = chunk.get("content", "")
            res += content
        print(res)


    asyncio.run(main())