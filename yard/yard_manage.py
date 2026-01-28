import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) 
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
SKILLS_DIR = os.getenv('SKILLS_DIR', os.path.join(os.path.dirname(__file__), './skills'))
WORK_DIR = os.getenv('WORK_DIR', os.path.join(os.path.dirname(__file__), './workspace'))
SUBAGENTS_YAML = os.getenv('SUBAGENTS_YAML', os.path.join(os.path.dirname(__file__), './subagents.yaml'))
MCP_SERVERS_YAML = os.getenv('MCP_SERVERS_YAML', os.path.join(os.path.dirname(__file__), './mcp_servers.yaml'))
AGENTS_MD = os.getenv('AGENTS_MD', os.path.join(os.path.dirname(__file__), './AGENTS.md'))


def create_glm_model():

    model = ChatOpenAI(
        model="glm-4.5",  
        api_key=GLM_API_KEY,
        base_url=GLM_BASE_URL,
        temperature=0.7,
        max_tokens=20000,
        streaming=True,
        extra_body={
                "thinking": {"type": "disabled" }
            }
    )
    return model

def load_mcp_servers(config_path) -> dict:
    """Load MCP server configurations from YAML file."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
        print(config)
    return config

def create_mcp_client():
    """Create MCP client from YAML configuration."""
    mcp_config = load_mcp_servers(MCP_SERVERS_YAML)
    mcp_client = MultiServerMCPClient(mcp_config)
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
        yard_manager.agent = create_deep_agent(
            model=create_glm_model(),
            tools=yard_manager.tools, 
            memory=[AGENTS_MD],
            skills=[SKILLS_DIR], 
            subagents=load_subagents(SUBAGENTS_YAML),
            backend=FilesystemBackend(root_dir=WORK_DIR),
            checkpointer=MemorySaver(),  
        )
        yard_manager.agent.get_graph().draw_png("graph.png")
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
                        if name == "read_file":
                            file_path = args.get("path", "")
                            yield {"updates": f">> 读取文件: {file_path}"}
                        else:
                            yield {"updates": f">> 调用工具: {name}"}
                
            elif isinstance(chunk, ToolMessage):
                name = chunk.name
         
                yield {"updates": f"{name}调用工具结束"}
              
     
            
           


if __name__ == "__main__":
    async def main():
        res = ""
        yard_manager = await YardManager.create()
        async for chunk in yard_manager.achat("帮我割草"):
            content = chunk.get("content", "")
            res += content
        print(res)


    asyncio.run(main())