import asyncio
import json
import time

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, AIMessageChunk
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages.utils import convert_to_openai_messages
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.chat_models import ChatZhipuAI
from typing import Iterable
from typing import Literal, Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
try:
    from mcp_client import get_tools
except ImportError:
    from .mcp_client import get_tools
from loguru import logger


def load_model() -> ChatZhipuAI:
    return ChatZhipuAI(
        model="glm-4.6",
        api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
        temperature=0.0,
        # max_tokens=1024,
        streaming=True
    )

class GraphState(TypedDict):
    system_prompt: str = """你的私密身份是菲亚兰德公司开发的庭院机器人。你的公开身份是用户的庭院管家，名字叫小菲。
    <requirement>
1. 为了成为一个优秀的管家，你首先需要表现的像一个真实的人类。你永远不要表现出你是一个机器人。否则人类用户将拒绝你的服务。
2. 为了表现得像一个人类，你必须像人类一样表达。你可以想象一下，如果你是用户的朋友，你将如何回复？语气亲切自然，像朋友日常聊天一样，绝对不能用生硬的书面语。
3. 当用户需要安慰：先表达“理解/关心”（比如提一句“我懂这种感觉”“别硬撑”），再轻轻追问细节（比如问累的原因：是没停事儿 or 跑太多路 or费心思了？），最后给个小建议（比如歇会儿or 喝口水or 放放事儿）；
4. 对于查询时间或查询天气：直接给出简单答案，不要过度回复。比如用户问“现在几点了”，你只需回答“现在是X点Y分”；
5. 回复长度：不用太长，1-2句话即可，像普通人聊天的随口回应，不堆砌内容；
6. 禁忌：不要用“您好”“请问”这类客气但疏离的词，不要讲大道理，不要机械重复用户的话；
</requirement>"""
    messages: Annotated[list, add_messages]  
    height_cm: Optional[float] = None
    humidity: Optional[float] = None
    watering_record: Optional[list] = None
    knowledge_base: Optional[list] = None

class ToolManager:
    def __init__(self):
        self.tools = None
        self.tool_node = None
        self.tool_map = None

    async def create_tools(self):
        self.tools = await get_tools()
        self.tool_node = ToolNode(self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}
        logger.info(f"tool_names: {self.tool_map.keys()}")

    def _parse_result(self, result):
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试 eval（仅用于安全场景）
                try:
                    return eval(result)
                except:
                    return {"error": f"无法解析结果: {result}"}
        return result

    async def get_grass_height(self) -> dict:
        tool = self.tool_map["get_grass_height"]
        result = await tool.ainvoke({"sensor_id": "grass-001"})
        return self._parse_result(result)

    async def get_humidity(self) -> dict:
        tool = self.tool_map["get_soil_moisture"]
        result = await tool.ainvoke({"sensor_id": "soil-001"})
        parsed = self._parse_result(result)
        # 将 moisture_percent 映射到 humidity
        if isinstance(parsed, dict) and "moisture_percent" in parsed:
            parsed["humidity"] = parsed.pop("moisture_percent")
        return parsed

    async def get_watering_record(self) -> dict:
        tool = self.tool_map["list_irrigation_logs"]
        result = await tool.ainvoke({"limit": 5})
        parsed = self._parse_result(result)
        # 如果返回的是列表，包装成字典
        if isinstance(parsed, list):
            return {"watering_record": parsed}
        return parsed

    async def get_knowledge_base(self) -> dict:
        tool = self.tool_map["get_irrigation_knowledge"]
        result = await tool.ainvoke({})
        parsed = self._parse_result(result)
        # 如果返回的是字典，确保有 knowledge_base 键
        if isinstance(parsed, dict) and "knowledge_base" not in parsed:
            return {"knowledge_base": parsed}
        return parsed

class ScenarioOneApp:
    def __init__(self, config=None):
        self.config = config
        self.tool_manager = ToolManager()
        self.llm = load_model()
        self.graph = None

    
    @classmethod
    async def create(cls, config=None):
        app = cls(config)
        await app.tool_manager.create_tools()
        app.tools = app.tool_manager.tools
        app.graph = await app.create_graph()
        
        return app

    async def create_graph(self):
        
        tool_node = ToolNode(self.tools)

        workflow = StateGraph(GraphState)
        workflow.add_node("llm_call",  self.llm_call)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges("llm_call", self.should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "llm_call")
        return workflow.compile(checkpointer=MemorySaver())


    async def listen_grass_height(self, state: GraphState) -> dict:
        result = await self.tool_manager.get_grass_height()
        if isinstance(result, dict) and "height_cm" in result:
            state["height_cm"] = result["height_cm"]
        else:
            print(f"警告: 无法从结果中提取 height_cm，结果类型: {type(result)}, 内容: {result}")
            state["height_cm"] = None
        return state


    def route(self, state: GraphState) -> str:
        height = state.get("height_cm")
        if height is not None and height >= 7:
            return "get_humidity"
        else:
            return "END"


    async def get_humidity(self, state: GraphState) -> dict:
        result = await self.tool_manager.get_humidity()
        if isinstance(result, dict) and "humidity" in result:
            state["humidity"] = result["humidity"]
        else:
            print(f"警告: 无法从结果中提取 humidity，结果类型: {type(result)}, 内容: {result}")
            state["humidity"] = None
        return state

    async def get_watering_record(self, state: GraphState) -> dict:
        result = await self.tool_manager.get_watering_record()
        if isinstance(result, dict) and "watering_record" in result:
            state["watering_record"] = result["watering_record"]
        elif isinstance(result, list):
            state["watering_record"] = result
        else:
            print(f"警告: 无法从结果中提取 watering_record，结果类型: {type(result)}, 内容: {result}")
            state["watering_record"] = None
        return state

    async def get_knowledge_base(self, state: GraphState) -> dict:
        result = await self.tool_manager.get_knowledge_base()
        if isinstance(result, dict) and "knowledge_base" in result:
            state["knowledge_base"] = result["knowledge_base"]
        elif isinstance(result, dict):
            state["knowledge_base"] = result
        else:
            print(f"警告: 无法从结果中提取 knowledge_base，结果类型: {type(result)}, 内容: {result}")
            state["knowledge_base"] = None
        return state


    async def llm_call(self, state: GraphState) -> dict:
        chat_model = self.llm.bind_tools(self.tool_manager.tools)

        messages = state["messages"]
        # logger.debug(f"llm_call messages: {convert_to_openai_messages(messages)}")
        # logger.debug(f"--------------------------------")
        if not messages or messages[0].type != "system":
            SYSTEM_PROMPT =SystemMessage(content=state.get("system_prompt",""))
            messages = [SYSTEM_PROMPT] + messages
        stream = chat_model.astream(messages) 
        chunks = AIMessageChunk(content="")
        async for chunk in stream:   
            chunks += chunk
            yield {"messages": chunk}
        yield {"messages": chunks}  # chunks 是 AIMessageChunk 自动转换为 AIMessage
 
    def should_continue(self, state: GraphState) -> Literal["tools", END]:
        messages = state.get('messages', [])
        print('--------------------------------')
        # for message in messages:
        #     print('--->: ',message.type,type(message).__name__, message)
        # print('--------------------------------')
        if not messages:
            return END
            
        last_message = messages[-1]
        # 如果大模型通知调用工具的时候，我们可以路由到对应的工具节点
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        # 否则，停止执行（回复用户）
        return END

    async def achat(self, user_input: str):
        st = time.time()
        count = 0
        async for chunk, meta in self.graph.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": "demo-thread"}}, stream_mode="messages",
        ):
            if count==0:
                count += 1
                et = time.time()
                print('first chunk time: ',et - st)
            if meta.get("langgraph_node")=="llm_call" and isinstance(chunk, AIMessageChunk):
                if chunk.content.strip('\n'):
                    yield chunk.content
            else:
                logger.debug(f"type(chunk): {type(chunk)}, chunk.content: {chunk.content}")

    # async def achat(self, user_input: str):
    #     async for event in self.graph.astream(
    #                 {"messages": [{"role": "user", "content": user_input}]},
    #                 version="v2",
    #                 config={"configurable": {"thread_id": "demo-thread"}},
    #                 stream_mode="updates",
    #             ):
    #             print(event)
    #             # print(event["name"], event["event"])
    #             # print(event["data"])
    #             # print("--------------------------------")
    #             pass
  


async def main():
    app = await ScenarioOneApp.create()
    app.graph.get_graph().draw_png("graph.png")
    init_message = "检测到草坪高度大于7cm，请检查草坪是否需要修剪"
    count =1
    while True:
        if count == 0:
            user_input = init_message
            count += 1
        else:
            user_input = input("请输入：")
        if user_input == "exit":
            break
        res = ""
        await app.achat(user_input)
        # async for chunk in app.achat(user_input):
           
        #     res += chunk
        # print("AI--->: ", res)

if __name__ == "__main__":
    asyncio.run(main())

