import asyncio

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.chat_models import ChatZhipuAI
from typing import Iterable

from mcp_client import get_tools



def load_model() -> ChatZhipuAI:
    return ChatZhipuAI(
        model="glm-4-flash",
        api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
        temperature=0.2,
        max_tokens=1024,
    )



def _route_after_agent(state: MessagesState) -> str:
    last: AIMessage = state["messages"][-1]
    print(last)
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def _call_agent(model: ChatZhipuAI, state: MessagesState) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response]}


# def entry_rou

def get_humidity(state: MessagesState) -> dict:
    pass

def get_watering_record(state: MessagesState) -> dict:
    pass

def get_knowledge_base(state: MessagesState) -> dict:
    pass

def generate_control_command(state: MessagesState) -> dict:
    pass

def verify_control_command(state: MessagesState) -> dict:
    pass
def execute_control_command(state: MessagesState) -> dict:
    pass

def listen_feedback(state: MessagesState) -> dict:
    pass


def listen_grass_height(state: MessagesState) -> dict:

    pass


async def create_graph():

    # 创建工作流：监听草高传感器->拉取湿度，灌溉记录，知识库->模型决策->生成控制指令->指令鉴权->执行-监听反馈
    # 通过 MCP 客户端拿到所有可用工具（草高/湿度/灌溉日志/知识库/割草机控制）
    tools = await get_tools()
    
    tool_node = ToolNode(tools)

    # 将工具能力绑定到模型，便于模型自行调用
    model = load_model().bind_tools(tools)

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", lambda state: _call_agent(model, state))
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", _route_after_agent, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    # 使用内存检查点，方便追踪历史对话
    return workflow.compile(checkpointer=MemorySaver())




async def main():
    graph = await create_graph()
    graph.get_graph().draw_png("graph.png")
    while True:
        user_input = input("请输入：")
        if user_input == "exit":
            break

        async for response in graph.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": "demo-thread"}},
        ):
            print(response)


if __name__ == "__main__":
    asyncio.run(main())