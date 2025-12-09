import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量（若未手动设置，可通过 .env 文件加载）
# load_dotenv()

# 初始化智普 AI 对话模型
chat_model = ChatZhipuAI(
    model="glm-4.6",  # 模型名称：glm-4 / glm-3-turbo / glm-4v（多模态）
    api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
    temperature=0.7,  # 随机性，0-1 之间
    max_tokens=1024,  # 最大生成token数
)



from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
import asyncio

# Define the tools for the agent to use
@tool
def search(query: str):
    """Call to surf the web."""
    # This is a placeholder, but don't tell the LLM that...
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


tools = [search]
tool_node = ToolNode(tools)
model = chat_model.bind_tools(tools)
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    print('--------------------------------')
    for message in messages:
        print('--->: ',type(message).__name__, message)
    print('--------------------------------')
    last_message = messages[-1]
    # 如果大模型通知调用工具的时候，我们可以路由到对应的工具节点
    if last_message.tool_calls:
        return "tools"
    # 否则，停止执行（回复用户）
    return END

# 定义一个调用大模型的函数
def call_model(state: MessagesState):
    messages = state['messages']
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
        "agent",
    should_continue,
)
workflow.add_edge("tools", 'agent')



checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)


async def main():
    res = []
    async for chunk, _ in app.astream(
        {"messages": [HumanMessage(content="what is the weather in sf")]},
        config={"configurable": {"thread_id": 42}},
        stream_mode="messages",
    ):
        res.append(chunk.content)
    print('res: ',''.join(res))


if __name__ == "__main__":
    asyncio.run(main())