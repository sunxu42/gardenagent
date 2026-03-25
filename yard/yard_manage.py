import asyncio
import yaml

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AIMessageChunk

from yard.events import InputEvent, OutputEvent
from yard.mem0_middleware import Mem0Middleware
from yard.graph import create_deep_agent
from yard.configs.config import load_config
from yard.context_middleware import ContextMiddleware
from yard.init_workspace import init_workspace
from yard.heartbeat import run_heartbeat_enqueue_loop

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
        workspace_dir = init_workspace(yard_manager.config.workspace_dir)
        yard_manager.tools = await load_mcp_tools(yard_manager.config)
        backend = FilesystemBackend(
            root_dir=yard_manager.config.workspace_dir, 
            virtual_mode=True
            )
        yard_manager.agent = create_deep_agent(
            model=create_glm_model(yard_manager.config),
            tools=yard_manager.tools,
            # memory=[yard_manager.config.agents_md],
            skills=[yard_manager.config.skills_dir],
            # subagents=load_subagents(yard_manager.config.subagents_yaml),
            backend=backend,
            checkpointer=MemorySaver(),  
            middleware=[ContextMiddleware(backend=backend, source_path=yard_manager.config.workspace_dir)],
        )

        # Agent internal queues (input -> worker -> output)
        yard_manager.agent_input_queue = asyncio.Queue(maxsize=1000)
        yard_manager.agent_output_queue = asyncio.Queue(maxsize=1000)
        yard_manager._agent_input_processing = False

        # start background tasks
        yard_manager._worker_stop = asyncio.Event()
        yard_manager._worker_task = asyncio.create_task(
            yard_manager._agent_input_worker(),
            name="input_worker",
        )
        yard_manager._heartbeat_stop = asyncio.Event()
        yard_manager._heartbeat_task = asyncio.create_task(
            run_heartbeat_enqueue_loop(
                agent=yard_manager,
                stop_event=yard_manager._heartbeat_stop,
            ),
            name="heartbeat_enqueue",
        )
        return yard_manager

    async def aclose(self) -> None:
        """Stop background worker and heartbeat task."""
        worker_stop = getattr(self, "_worker_stop", None)
        hb_stop = getattr(self, "_heartbeat_stop", None)
        if worker_stop is not None:
            worker_stop.set()
        if hb_stop is not None:
            hb_stop.set()

        worker_task = getattr(self, "_worker_task", None)
        hb_task = getattr(self, "_heartbeat_task", None)
        if worker_task is not None and not worker_task.done():
            worker_task.cancel()
        if hb_task is not None and not hb_task.done():
            hb_task.cancel()

        # Best-effort await
        for task in (worker_task, hb_task):
            if task is None:
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass


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
              
     
            
    async def astream(self, event: InputEvent):
        event_id = event.event_id
        trigger_by = event.event_type

        # Turn start boundary
        self.agent_output_queue.put_nowait(
            OutputEvent(data={}, trigger_by=trigger_by, event_id=event_id, phase="start")
        )

        # Stream middle chunks
        async for chunk in self.achat(event.content):
            print(f"astream: {chunk}")
            self.agent_output_queue.put_nowait(
                OutputEvent(data=chunk, trigger_by=trigger_by, event_id=event_id, phase="middle")
            )

        # Turn end boundary
        self.agent_output_queue.put_nowait(
            OutputEvent(data={}, trigger_by=trigger_by, event_id=event_id, phase="end")
        )



    async def _agent_input_worker(self) -> None:
        while not self._worker_stop.is_set():
            if self._agent_input_processing:
                await asyncio.sleep(0.1)
                continue
            try:
                item = await self.agent_input_queue.get()
                self._agent_input_processing = True
                try:
                    await self.astream(item)
                finally:
                    self._agent_input_processing = False
                    self.agent_input_queue.task_done()
            except asyncio.CancelledError:
                return           

if __name__ == "__main__":
    async def main():
        res = ""
        yard_manager = await YardManager.create()
        # print graph
        graph = yard_manager.agent.get_graph(xray=True)
        graph.draw_mermaid_png(output_file_path="yard_manager.png")
        # async for chunk in yard_manager.achat("帮我割草"):
        #     content = chunk.get("content", "")
        #     res += content
        # print(res)


    asyncio.run(main())