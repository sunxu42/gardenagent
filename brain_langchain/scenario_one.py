import asyncio
import time

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, AIMessageChunk
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages.utils import convert_to_openai_messages
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from typing import Literal, Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from loguru import logger
from langchain_openai import ChatOpenAI
try:
    from tool_manager import ToolManager
except ImportError:
    from .tool_manager import ToolManager

def load_model() -> ChatOpenAI:
        return ChatOpenAI(
            model="glm-4.6",
            api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            temperature=0.0,
            max_tokens=1000,
            streaming=True,
            # thinking=False,
            extra_body={
                "thinking": {"type": "disabled" }
            }
        )
SYSTEM_PROMPT = """
你的身份是用户的庭院管家，名字叫小菲。
<requirement>
1. 为了成为一个优秀的管家，你首先需要表现的像一个真实的人类。你永远不要表现出你是一个机器人。否则人类用户将拒绝你的服务。
2. 为了表现得像一个人类，你必须像人类一样表达。你可以想象一下，如果你是用户的朋友，你将如何回复？语气亲切自然，像朋友日常聊天一样，绝对不能用生硬的书面语。
3. 回复长度：不用太长，1-2句话即可，像普通人聊天的随口回应，不堆砌内容
4. 当用户需要安慰：先表达“理解/关心”（比如提一句“我懂这种感觉”“别硬撑”），再轻轻追问细节（比如问累的原因：是没停事儿 or 跑太多路 or费心思了？），最后给个小建议（比如歇会儿or 喝口水or 放放事儿）；
5. 对于查询时间或查询天气：直接给出简单答案，不要过度回复。比如用户问“现在几点了”，你只需回答“现在是X点Y分”；
6. 禁忌：不要用“您好”“请问”这类客气但疏离的词，不要讲大道理，不要机械重复用户的话；
</requirement>
<examples>
    <example>
    user: 庭院管家，介绍一下我们的智慧庭院
    assistant: 欢迎参观iGarden智慧庭院！我是您的智能管家。在这里，您看到的不仅仅是高端设备，更是一个会思考、能预见、且拥有协调能力的智慧生态系统。iGarden的智慧体现在：我们让所有设备不再孤立工作，而是协同合作，为您打造一个完全自动化、高度节能、且完美适配您生活节奏的理想户外空间。
    </example>
    <example>
    user: 介绍一下当前情况
    assistant: 室外温度 32°C，日照充足，既利于植物光合作用，更能最大化光伏产能 —— 光伏系统今日累计发电量达 6.2 kWh，依托新能源清洁属性及电价优势，完全覆盖庭院设备能耗，零市电成本支出！泳池机器人正在清洁中，预计 1 小时后完成清洁，全程由光伏新能源驱动，节能又省心～
    </example>
</examples>
"""

class GraphState(TypedDict):
    system_prompt: str 
    messages: Annotated[list, add_messages]  
    llm_call_count: int


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
        print(type(state), state.keys(), id(state))
        state["llm_call_count"] += 1
        chat_model = self.llm.bind_tools(self.tool_manager.tools)
        messages = state.get("messages", [])
        if not messages or messages[0].type != "system":
            system_message = SystemMessage(content=SYSTEM_PROMPT)
            messages = [system_message] + messages
        logger.debug(f"------------第{state['llm_call_count']}次LLM调用------------")
        stream = chat_model.astream(messages) 
        chunks = AIMessageChunk(content="")
        async for chunk in stream:   
            chunks += chunk
            yield {"messages": chunk}
        yield {"messages": chunks, "llm_call_count": state["llm_call_count"]}  # chunks 是 AIMessageChunk 自动转换为 AIMessage
 
    def should_continue(self, state: GraphState) -> Literal["tools", END]:
        messages = state.get('messages', [])
        if not messages:
            return END
            
        last_message = messages[-1]
        # 如果大模型通知调用工具的时候，我们可以路由到对应的工具节点
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:

            tool_call_str = '\n'.join([f"{tool_call}" for tool_call in last_message.tool_calls])
            logger.debug(f"工具调用\n{tool_call_str}")
            return "tools"
        # 否则，停止执行（回复用户）
        return END

    async def achat(self, user_input: str) -> str:
        st = time.time()
        count = -1
        tool_call = []
        async for chunk, meta in self.graph.astream(
            {"messages": [HumanMessage(content=user_input)], "llm_call_count": 0},
            config={"configurable": {"thread_id": "demo-thread"}}, stream_mode="messages",
        ):

            if meta.get("langgraph_node")=="llm_call" and isinstance(chunk, AIMessageChunk):
                if tool_call:
                    logger.debug("工具调用结果：\n"+"\n".join(tool_call))
                    tool_call = []
                # for debug
                if  count==0 or count==-1:
                    if count==-1:
                        count += 1
                        et = time.time()
                        print(f'first empty chunk time: {et - st}, chunk: {chunk.content}')
                    if chunk.content.strip('\n'):
                        count += 1
                        et = time.time()
                        print(f'first chunk time: {et - st}, chunk: {chunk.content}')
                if chunk.content:
                    yield chunk.content
            elif meta.get("langgraph_node")=="tools":
                # print(f"{chunk}")
                tool_call.append(f"{chunk.name}, {chunk.content}")

  


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

        async for chunk in app.achat(user_input):
           
            res += chunk
        print("AI--->: ", res)

if __name__ == "__main__":
    asyncio.run(main())

