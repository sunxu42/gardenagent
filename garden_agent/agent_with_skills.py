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
from langchain_core.tools import tool
from pathlib import Path
try:
    from tool_manager import ToolManager
except ImportError:
    from .tool_manager import ToolManager
try:    
    from utils import generate_tool_call_id
except ImportError:
    from .utils import generate_tool_call_id
try:
    from tool_system import scan_skills_headers, load_skill_content
except ImportError:
    from .tool_system import scan_skills_headers, load_skill_content

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

def build_system_prompt(skills_dir: str = None) -> str:
    """
    构建系统提示词，注入 skill headers。
    
    Args:
        skills_dir: skills 目录路径，如果为 None 则使用默认路径
        
    Returns:
        包含 skill headers 的系统提示词
    """
    base_prompt = """
你的身份是用户的管家，名字叫小菲。你可以通过查看技能手册来了解如何管理庭院。
<requirement>
1. 当用户需求和技能相关，总是优先查询技能再来执行任务。
2. 为了成为一个优秀的管家，你首先需要表现的像一个真实的人类。你永远不要表现出你是一个机器人。否则人类用户将拒绝你的服务。
3. 为了表现得像一个人类，你必须像人类一样表达。你可以想象一下，如果你是用户的朋友，你将如何回复？语气亲切自然，像朋友日常聊天一样，绝对不能用生硬的书面语。
4. 回复长度：不用太长，1-2句话即可，像普通人聊天的随口回应，不堆砌内容
5. 当用户需要安慰：先表达“理解/关心”（比如提一句“我懂这种感觉”“别硬撑”），再轻轻追问细节（比如问累的原因：是没停事儿 or 跑太多路 or费心思了？），最后给个小建议（比如歇会儿or 喝口水or 放放事儿）；
6. 对于查询时间或查询天气：直接给出简单答案，不要过度回复。比如用户问“现在几点了”，你只需回答“现在是X点Y分”；
7. 禁忌：不要用“您好”“请问”这类客气但疏离的词，不要讲大道理，不要机械重复用户的话；
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
    
    # 注入 skill headers
    if skills_dir is None:
        # 默认使用当前文件所在目录的 skills 文件夹
        current_dir = Path(__file__).parent
        skills_dir = str(current_dir / "skills")
    
    skill_headers = scan_skills_headers(skills_dir)
    
    if skill_headers:
        skills_section = "\n<available_skills>\n"
        for skill_name, header in skill_headers.items():
            description = header.get("description", "")
            skills_section += f"- {skill_name}: {description}\n"
        skills_section += "</available_skills>\n"
        skills_section += "\n你可以使用 load_skill_content 工具来加载特定技能的详细内容。\n"
        base_prompt += skills_section
    
    return base_prompt

class GraphState(TypedDict):
    system_prompt: str 
    messages: Annotated[list, add_messages]  
    llm_call_count: int




@tool
def load_skill_content_tool(skill_name: str) -> str:
    """
    加载指定技能的详细内容。
    
    Args:
        skill_name: 技能名称（从 available_skills 中选择）
        
    Returns:
        技能的详细内容（Markdown 格式）
    """
    # 获取 skills 目录路径
    current_dir = Path(__file__).parent
    skills_dir = current_dir / "skills"
    
    # 查找对应的 SKILL.md 文件
    skill_files = list(skills_dir.rglob('SKILL.md'))
    for skill_file in skill_files:
        # 尝试加载 header 来匹配 skill_name
        try:
            from tool_system import load_skill_header
        except ImportError:
            from .tool_system import load_skill_header
        
        header = load_skill_header(str(skill_file))
        if header and header.get('name') == skill_name:
            return load_skill_content(str(skill_file))
    
    return f"未找到技能: {skill_name}"

class ScenarioOneApp:
    def __init__(self, config=None):
        self.config = config
        self.tool_manager = ToolManager()
        self.llm = load_model()
        self.graph = None
        self.skills_dir = None  # 用于存储 skills 目录路径

    
    @classmethod
    async def create(cls, config=None):
        app = cls(config)
        await app.tool_manager.create_tools()
        
        # 添加 load_skill_content tool
        app.tools = app.tool_manager.tools + [load_skill_content_tool]
        
        # 构建包含 skill headers 的 system prompt
        current_dir = Path(__file__).parent
        app.skills_dir = str(current_dir / "skills")
        app.system_prompt = build_system_prompt(app.skills_dir)
        
        app.graph = await app.create_graph()
        
        return app

    async def create_graph(self):
        """
        创建简化的 langgraph，直接路由到 llm_call。
        """
        tool_node = ToolNode(self.tools)

        workflow = StateGraph(GraphState)
        workflow.add_node("llm_call", self.llm_call)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("llm_call")
        workflow.add_conditional_edges("llm_call", self.should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "llm_call")
        return workflow.compile(checkpointer=MemorySaver())



    async def llm_call(self, state: GraphState) -> dict:
        state["llm_call_count"] += 1
        logger.debug(f"------------第{state['llm_call_count']}次LLM调用------------")
        
        chat_model = self.llm.bind_tools(self.tools)
        messages = state.get("messages", [])

        if not messages or messages[0].type != "system":
            # 使用构建好的 system prompt（包含 skill headers）
            system_prompt = state.get("system_prompt", self.system_prompt)
            system_message = SystemMessage(content=system_prompt)
            messages = [system_message] + messages
        for message in messages:
            print(convert_to_openai_messages(message))
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
            "system_prompt": self.system_prompt
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

