import asyncio
import time
import re
from unittest import result
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, AIMessageChunk, RemoveMessage
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
try:    
    from utils import generate_tool_call_id
except ImportError:
    from .utils import generate_tool_call_id

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
你的身份是用户的管家，名字叫小菲。
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
        self.pool_prepare_count = 0
        self.grass_prepare_count = 0

    
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
        workflow.set_conditional_entry_point(
            self.entry_route,
            {
                "pool_prepare": "pool_prepare",
                "grass_prepare": "grass_prepare",
                "irrigation_prepare": "irrigation_prepare",
                "llm_call": "llm_call",
            }
        )   
        workflow.add_node("pool_prepare", self.pool_prepare)
        workflow.add_node("grass_prepare", self.grass_prepare)
        workflow.add_node("irrigation_prepare", self.irrigation_prepare)
        workflow.add_node("llm_call",  self.llm_call)
        workflow.add_node("tools", tool_node)

        workflow.add_edge("pool_prepare", "llm_call")
        workflow.add_edge("grass_prepare", "llm_call")
        workflow.add_edge("irrigation_prepare", "llm_call")
        # workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges("llm_call", self.should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "llm_call")
        return workflow.compile(checkpointer=MemorySaver())


    async def entry_route(self, state: GraphState) -> str:
        messages = state.get("messages", [])
        last_message = messages[-1]

        if re.search(r'泳池|水池|游泳', last_message.content):
            logger.debug("------------路由到泳池概览------------")
            return "pool_prepare"
        elif re.search(r'草坪|花园|草地|割草|修剪', last_message.content):
            logger.debug("------------路由到草坪概览------------")
            self.grass_prepare_count == 0
            return "grass_prepare"
        elif re.search(r'灌溉|浇水|灌溉系统|浇水系统', last_message.content):
            logger.debug("------------路由到灌溉准备------------")
            return "irrigation_prepare"
        else:
            logger.debug("------------路由到LLM调用------------")
        return "llm_call"
    
    async def irrigation_prepare(self, state: GraphState) -> str:

        system_prompt = f"""
        请根据以下规则管理灌溉：
        1. 在做出任何决定前，需优先检查当前天气、土壤湿度、 割草机运行状态、灌溉系统运行状态。
        2. 如果检测到土壤湿度太高，则告诉用户土壤湿度太高，不能进行灌溉。
        3. 如果检测到割草机正在运行，则告诉用户割草机正在运行，不能进行灌溉。
        4. 如果检测到灌溉系统正在运行，则告诉用户灌溉系统正在运行，不能进行灌溉。
        5. 如果检测到天气预报有降雨，则告诉用户天气预报有降雨，不能进行灌溉。
        6. 割草后24小时内不能进行灌溉, 防止病菌滋生。
        7. 计划安排结束后，简洁的告诉用户你已经安排好了，并简洁的告诉用户你安排的计划。
        """
        return {"system_prompt": system_prompt}
    async def pool_prepare(self, state: GraphState) -> str:
        if self.pool_prepare_count == 1:
            return state
        self.pool_prepare_count += 1

        # user_input = state.get("messages", [])[-1].content
        # last_id = state["messages"][-1].id
        # tool_calls = [
        #     {'name': 'mock_pool_robot_status', 'args': {}, 'id': generate_tool_call_id(), 'type': 'tool_call'},
        #     {'name': 'mock_weather_forecast', 'args': {}, 'id': generate_tool_call_id(), 'type': 'tool_call'},
        #     {'name': 'mock_swimming_preference', 'args': {}, 'id': generate_tool_call_id(), 'type': 'tool_call'}
        # ]
        # tool_messages=[]
        # for tool_call in tool_calls:
        #     tool = self.tool_manager.tool_map[tool_call["name"]]
        #     result = await tool.ainvoke(tool_call["args"])
        #     tool_messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
        system_prompt = f"""
        假如你是泳池管家，请根据以下规则管理泳池：

        1. 在做出任何决定前，需优先检查当前天气、泳池状态（包括清洁程度、水温、水质）和主人的游泳偏好。
        2. 如果检测到泳池水质不佳，务必首先安排清洁机器人对泳池进行彻底清洁。
        3. 若水温低于主人的偏好温度，可以考虑启动热泵进行加热; 若水温高于主人的偏好温度，可以考虑启动水泵进行降温。
        4. 如果泳池已经干净并且水温适宜，可根据主人的偏好提前开启冲浪器等辅助设备。
        5. 不建议在恶劣天气（如下雨、强风）时建议主人游泳，应主动提示并建议等待天气改善。
        6. 每一步操作和建议都需基于综合设备状态与主人的实际需求。
        7. 计划安排结束后，简洁的告诉用户你已经安排好了，并简洁的告诉用户你安排的计划。

        请根据上述规则为我安排最佳的泳池使用状态并说明理由。
        </equipments>
        泳池相关设备：水泵，热泵，泳池清洁机器人，冲浪器。
        </equipments>
       

        """
        # ai_message =  AIMessage(
        #                     content="\n作为您的泳池管家，我需要先检查当前状况来为您安排最佳的游泳环境。让我先查看天气、泳池状态和您的游泳偏好。\n",  # 可选的额外文本内容
        #                     tool_calls=[
        #                         {
        #                             "name": "mock_weather_forecast",      # 工具名称
        #                             "args": {},  # 工具参数
        #                             "id": generate_tool_call_id(),        # 唯一工具调用ID
        #                             "type": "tool"              # 类型标识
        #                         }
        #                     ]
        #                 )
        tool_names = ["mock_weather_forecast", "mock_pool_status", "mock_swimming_preference","control_heat_pump", "control_water_pump", "control_cleaning_robot", "control_wave_machine"]  
        tools = [tool  for tool in self.tool_manager.tools if tool.name in tool_names]

        return {"system_prompt": system_prompt, "tools": tools }

    async def grass_prepare(self, state: GraphState) -> str:
        system_prompt = f"""
        假如你是草坪管家，请根据以下规则管理草坪：

        1. 在做出任何决定前，需优先检查当前天气、草坪状态（包括草高、土壤湿度、灌溉记录）和主人的草坪偏好。
        2. 如果检测到草坪草高过高，务必首先启动割草机对草坪进行修剪。
        3. 若土壤湿度低于主人的偏好湿度，可以考虑启动灌溉系统进行灌溉; 若土壤湿度高于主人的偏好湿度，可以考虑启动排水系统进行排水。
        4. 如果草坪已经修剪并且土壤湿度适宜，可根据主人的偏好提前开启冲浪器等辅助设备。
        5. 不建议在恶劣天气（如下雨、强风）时建议主人修剪草坪，应主动提示并建议等待天气改善。
        6. 每一步操作和建议都需基于综合设备状态与主人的实际需求。
        7. 计划安排结束后，简洁的告诉用户你已经安排好了，并简洁的告诉用户你安排的计划。
        8. 草高小于7cm时，不需要修剪。
        9. 土壤湿度太大时不能割草。

        请根据上述规则为我安排最佳的草坪使用状态并说明理由。
        </equipments>
        草坪相关设备：割草机，灌溉系统，排水系统，冲浪器。
        </equipments>
        """
        tool_names = ["mock_grass_height", "mock_soil_moisture", "mock_irrigation_logs", "mock_irrigation_knowledge", "control_mower"]  
        tools = [tool  for tool in self.tool_manager.tools if tool.name in tool_names]
        return {"system_prompt": system_prompt, "tools": tools }

    async def llm_call(self, state: GraphState) -> dict:
        state["llm_call_count"] += 1
        logger.debug(f"------------第{state['llm_call_count']}次LLM调用------------")
        
        chat_model = self.llm.bind_tools(state.get("tools", self.tool_manager.tools))
        messages = state.get("messages", [])

        if not messages or messages[0].type != "system":
            system_message = SystemMessage(content=state.get("system_prompt", SYSTEM_PROMPT))
            messages = [system_message] + messages
        for message in messages:
            print(convert_to_openai_messages(message))
        # stream = chat_model.astream(messages) 
        # chunks = AIMessageChunk(content="")
        # async for chunk in stream:   
        #     chunks += chunk
        #     yield {"messages": chunk}
        # logger.debug(f"------------第{state['llm_call_count']}次LLM调用结果------------\n{chunks}")
        # yield {"messages": chunks, "llm_call_count": state["llm_call_count"]}  # chunks 是 AIMessageChunk 自动转换为 AIMessage
        response = await chat_model.ainvoke(messages)
        return {"messages": response}
 
    def should_continue(self, state: GraphState) -> Literal["tools", END]:
        messages = state.get('messages', [])
        if not messages:
            return END
            
        last_message = messages[-1]
        # 如果大模型通知调用工具的时候，我们可以路由到对应的工具节点
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            tool_call_str = '\n'.join([f"{tool_call}" for tool_call in last_message.tool_calls])
            logger.debug(f"工具调用：\n{tool_call_str}")
            return "tools"
        # 否则，停止执行（回复用户）
        return END

    async def achat(self, user_input: str):
        st = time.time()
        count = -1
        tool_call = []
        state = {
            "messages": [HumanMessage(content=user_input)], 
            "llm_call_count": 0,
            "system_prompt": SYSTEM_PROMPT
            }
        async for chunk, meta in self.graph.astream(state, config={"configurable": {"thread_id": "demo-thread"}}, stream_mode="messages"):
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

    # async def achat(self, user_input: str):
    #     st = time.time()
    #     count = -1
    #     tool_call = []
    #     state = {
    #         "messages": [HumanMessage(content=user_input)], 
    #         "llm_call_count": 0,
    #         "system_prompt": SYSTEM_PROMPT
    #         }
    #     async for info in self.graph.astream(state, config={"configurable": {"thread_id": "demo-thread"}}, 
    #     stream_mode=["updates","messages"],
    #     ):
    #         if info[0] == "updates":
    #             # update_content = info[1]
    #             # if update_content.get("llm_call"):
    #             #     yield {"updates": "正在访问llm模型..."}
    #             # elif update_content.get("tools"):
    #             #     tool_name = update_content.get("tools")[0].get("name")
    #             #     # print(f"tool_name: {tool_name}")
    #             #     yield {"updates": f"正在访问工具：{tool_name}..."}
    #             print(f"updates: {info[1]}")
                
    #         elif info[0] == "messages":
    #             messages = info[1]
    #             chunk = messages[0]
    #             meta = messages[1]
    #             if meta.get("langgraph_node")=="llm_call" and isinstance(chunk, AIMessageChunk):
    #                 if tool_call:
    #                     logger.debug("工具调用结果：\n"+"\n".join(tool_call))
    #                     tool_call = []
    #                 # for debug
    #                 if  count==0 or count==-1:
    #                     if count==-1:
    #                         count += 1
    #                         et = time.time()
    #                         print(f'first empty chunk time: {et - st}, chunk: {chunk.content}')
    #                     if chunk.content.strip('\n'):
    #                         count += 1
    #                         et = time.time()
    #                         print(f'first chunk time: {et - st}, chunk: {chunk.content}')
    #                 if chunk.content:
    #                     yield chunk.content
    #             elif meta.get("langgraph_node")=="tools":
    #                 # print(f"{chunk}")
    #                 tool_call.append(f"{chunk.name}, {chunk.content}")
                            
    
       

    async def achat(self, user_input: str):
        state = {
            "messages": [HumanMessage(content=user_input)], 
            "llm_call_count": 0,
            "system_prompt": SYSTEM_PROMPT
            }
        st = time.time()
        count = 0
        async for event in self.graph.astream_events(state, version="v2",config={"configurable": {"thread_id": "demo-thread"}}):
            
            
            tags = event.get("tags", [])
            event_name = event.get("name", "")
            event_event = event.get("event", "")
            data = event.get("data", {})
            # print(f"event_name: {event_name}, event_event: {event_event}, tags: {tags}")
            if event_name == "ChatOpenAI" and event_event == "on_chat_model_stream":
                content = data['chunk'].content         
                if count == 0 and content.strip('\n'):
                    et = time.time()
                    print(f"first token time: {round(et - st, 3)}s, content: {content}")
                    count += 1
                yield {"content": content}
            elif event_event == "on_tool_start":
                yield {"updates": f"正在访问工具 {event_name}"}

            elif event_name == "ChatOpenUAI" and event_event == "on_chat_model_start":
                yield {"updates": "正在访问llm模型..."}
            elif event_name == "ChatOpenUAI" and event_event == "on_chat_model_end":
                yield {"updates": "结束访问llm模型..."}
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
        # await app.achat(user_input)
        async for chunk in app.achat(user_input):
           content = chunk.get("content", "")
           res += content
        print("AI--->: ", res)

if __name__ == "__main__":
    asyncio.run(main())

