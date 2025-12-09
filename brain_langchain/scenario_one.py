import asyncio
import json
import time

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.chat_models import ChatZhipuAI
from typing import Iterable
from typing import Literal, Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate

from mcp_client import get_tools

class ToolManager:
    def __init__(self):
        self.tools = None
        self.tool_node = None
        self.tool_map = None

    async def create_tools(self):
        self.tools = await get_tools()
        self.tool_node = ToolNode(self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}

    def _parse_result(self, result):
        """解析工具返回结果，支持字符串和字典格式。"""
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



tool_manager = ToolManager()

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]  
    height_cm: Optional[float] = None
    humidity: Optional[float] = None
    watering_record: Optional[list] = None
    knowledge_base: Optional[list] = None



def load_model() -> ChatZhipuAI:
    return ChatZhipuAI(
        model="glm-4.6",
        api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
        temperature=0.2,
        # max_tokens=1024,
    )

async def listen_grass_height(state: GraphState) -> dict:
    result = await tool_manager.get_grass_height()
    if isinstance(result, dict) and "height_cm" in result:
        state["height_cm"] = result["height_cm"]
    else:
        print(f"警告: 无法从结果中提取 height_cm，结果类型: {type(result)}, 内容: {result}")
        state["height_cm"] = None
    return state


def route(state: GraphState) -> str:
    height = state.get("height_cm")
    if height is not None and height >= 7:
        return "get_humidity"
    else:
        return "END"


async def get_humidity(state: GraphState) -> dict:
    result = await tool_manager.get_humidity()
    if isinstance(result, dict) and "humidity" in result:
        state["humidity"] = result["humidity"]
    else:
        print(f"警告: 无法从结果中提取 humidity，结果类型: {type(result)}, 内容: {result}")
        state["humidity"] = None
    return state

async def get_watering_record(state: GraphState) -> dict:
    result = await tool_manager.get_watering_record()
    if isinstance(result, dict) and "watering_record" in result:
        state["watering_record"] = result["watering_record"]
    elif isinstance(result, list):
        state["watering_record"] = result
    else:
        print(f"警告: 无法从结果中提取 watering_record，结果类型: {type(result)}, 内容: {result}")
        state["watering_record"] = None
    return state

async def get_knowledge_base(state: GraphState) -> dict:
    result = await tool_manager.get_knowledge_base()
    if isinstance(result, dict) and "knowledge_base" in result:
        state["knowledge_base"] = result["knowledge_base"]
    elif isinstance(result, dict):
        state["knowledge_base"] = result
    else:
        print(f"警告: 无法从结果中提取 knowledge_base，结果类型: {type(result)}, 内容: {result}")
        state["knowledge_base"] = None
    return state

class GenerateChain:
    def __init__(self):
        tools = tool_manager.tools
        self.model = load_model().bind_tools(tools)
   
        self.prompt = ChatPromptTemplate.from_template("""
        你是一个专业的园丁助手，根据草高、湿度和灌溉记录，决定是否需要割草， 如果需要割草请输出割草指令，否则告诉用户不需要割草。
        草高：{height_cm} cm
        湿度：{humidity} %
        灌溉记录：{watering_record}
        知识库：{knowledge_base}
        """)
        self.chain = self.prompt | self.model

    def invoke(self, state: GraphState) -> dict:

        return self.chain.invoke(state)

    async def astream_full(self, state: GraphState):
        parts = []
        # 这里会逐 token/块产出 AIMessageChunk
        async for chunk in self.chain.astream(state):
            if hasattr(chunk, "content") and chunk.content:
                parts.append(chunk.content)
                # 你可以在这里把 chunk.content 打印 / 推送到前端
                yield chunk.content
        # 组装成最终 AIMessage
        return AIMessage(content="".join(parts))

async def call_agent(state: GraphState) -> dict:
    generate_chain = GenerateChain()
    t1 = time.time()
    response = generate_chain.invoke(state)
    t2 = time.time()
    print('time: ',t2 - t1)
    # 累积消息而不是覆盖，避免丢失 tool_calls 所需的上下文
    state["messages"] = add_messages(state.get("messages", []), [response])
    return state



def should_continue(state: GraphState) -> Literal["tools", END]:
    messages = state.get('messages', [])
    print('--------------------------------')
    for message in messages:
        print('--->: ',type(message).__name__, message)
    print('--------------------------------')
    if not messages:
        return END
        
    last_message = messages[-1]
    # 如果大模型通知调用工具的时候，我们可以路由到对应的工具节点
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # 否则，停止执行（回复用户）
    return END


async def create_graph():

    # 创建工作流：监听草高传感器->拉取湿度，灌溉记录，知识库->模型决策->生成控制指令->指令鉴权->执行-监听反馈
    # 通过 MCP 客户端拿到所有可用工具（草高/湿度/灌溉日志/知识库/割草机控制）

    workflow = StateGraph(GraphState)
    await tool_manager.create_tools()
    tool_node = ToolNode(tool_manager.tools)
    workflow.add_node("listen_grass_height", listen_grass_height)
    workflow.add_node("get_humidity", get_humidity)
    workflow.add_node("get_watering_record", get_watering_record)
    workflow.add_node("get_knowledge_base", get_knowledge_base)
    workflow.add_node("call_agent", call_agent)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "listen_grass_height")
    workflow.add_conditional_edges("listen_grass_height", route, {"get_humidity": "get_humidity", "END": END})
    workflow.add_edge("get_humidity", "get_watering_record")
    workflow.add_edge("get_watering_record", "get_knowledge_base")
    workflow.add_edge("get_knowledge_base", "call_agent")
    workflow.add_conditional_edges("call_agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "call_agent")

    return workflow.compile(checkpointer=MemorySaver())




async def main():
    graph = await create_graph()
    graph.get_graph().draw_png("graph.png")
    
    while True:
        user_input = input("请输入：")
        if user_input == "exit":
            break
        res = []
        async for chunk, _ in graph.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": "demo-thread"}}, stream_mode="messages",
        ):
     
            res.append(chunk.content)
        print('res: ',''.join(res))

if __name__ == "__main__":
    asyncio.run(main())