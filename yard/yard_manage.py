import asyncio
import yaml

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AIMessageChunk

from yard.mem0_middleware import Mem0Middleware
from yard.graph import create_deep_agent
from yard.configs.config import load_config



def create_glm_model(config):

    model = ChatOpenAI(
        model=config.llm_model_name,  
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        temperature=0.7,
        max_tokens=20000,
        streaming=True,
        extra_body={
                "thinking": {"type": "disabled" }
            }
    )
    return model



async def load_mcp_tools(config):
    with open(config.mcp_servers_yaml) as f:
        mcp_servers_config = yaml.safe_load(f)
    mcp_client = MultiServerMCPClient(mcp_servers_config)
    all_tools = []
    for name in mcp_client.connections.keys():
        try:
            tools = await mcp_client.get_tools(server_name=name)
        except Exception as e:
            print(f"[warn] MCP server '{name}' is unavailable and will be skipped")
            continue
        all_tools.extend(tools)
    return all_tools

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
        print(config)
        self.config = self._merge_config(config)

    def _merge_config(self, config):
        base_config = load_config()
        if config:
            # 将传入的 dict 配置合并到基础配置对象上（只覆盖已存在字段）
            base_config.add_config(config)
        return base_config

    @classmethod
    async def create(cls, config=None):
        yard_manager = cls(config)
        yard_manager.tools = await load_mcp_tools(yard_manager.config)
        yard_manager.agent = create_deep_agent(
            model=create_glm_model(yard_manager.config),
            tools=yard_manager.tools,
            # memory=[yard_manager.config.agents_md],
            skills=[yard_manager.config.skills_dir],
            # subagents=load_subagents(yard_manager.config.subagents_yaml),
            backend=FilesystemBackend(root_dir=yard_manager.config.workspace_dir),
            checkpointer=MemorySaver(),  
            middleware=[Mem0Middleware(api_key=yard_manager.config.mem0_api_key)],
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
        # print graph
        # graph = yard_manager.agent.get_graph(xray=True)
        # graph.draw_mermaid_png(output_file="yard_manager.png")
        async for chunk in yard_manager.achat("帮我割草"):
            content = chunk.get("content", "")
            res += content
        print(res)


    asyncio.run(main())