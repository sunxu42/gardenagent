from typing import Iterable
import asyncio

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.chat_models import ChatZhipuAI

from mcp_client import get_tools_sync

# 创建工作流：监听草高传感器->拉取湿度，灌溉记录，知识库->模型决策->生成控制指令->指令鉴权->执行-监听反馈


def load_model() -> ChatZhipuAI:
    """初始化智谱模型实例."""
    return ChatZhipuAI(
        model="glm-4-flash",
        api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
        temperature=0.2,
        max_tokens=1024,
    )


def _route_after_agent(state: MessagesState) -> str:
    """根据模型输出决定下一步走工具还是结束。"""
    last: AIMessage = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def _call_agent(model: ChatZhipuAI, state: MessagesState) -> dict:
    """调用大模型，让其读取传感器/日志信息并给出控制决策。"""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def create_graph():
    """构建草坪监控与割草决策工作流."""
    # 通过 MCP 客户端拿到所有可用工具（草高/湿度/灌溉日志/知识库/割草机控制）
    tools = get_tools_sync()
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


def run_once(
    user_query: str,
    messages: Iterable[HumanMessage] | None = None,
    thread_id: str = "demo-thread",
):
    """单次运行示例（异步工具需要使用异步调用）。"""
    graph = create_graph()
    initial_messages = list(messages) if messages else [HumanMessage(content=user_query)]
    result = asyncio.run(
        graph.ainvoke(
            {"messages": initial_messages},
            config={"configurable": {"thread_id": thread_id}},
        )
    )
    return result["messages"]


if __name__ == "__main__":
    final_messages = run_once("请根据当前传感器数据判断是否需要割草，并给出控制指令。")
    for msg in final_messages:
        role = msg.type
        print(f"[{role}] {msg.content}")