from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.messages import AIMessageChunk, HumanMessage
import asyncio

def streaming_llm_node(state: MessagesState):
    messages = state["messages"]
    
    # 模拟streaming LLM（实际使用model.astream）
    chunks = [
        AIMessageChunk(content="这是", id="msg_1"),
        AIMessageChunk(content="第一", id="msg_1", parent_ids=["msg_1"]),
        AIMessageChunk(content="个chunk", id="msg_1", parent_ids=["msg_1"])
    ]
    
    # 返回多个chunk，LangGraph自动合并
    return {"messages": chunks}

graph = StateGraph(MessagesState)
graph.add_edge(START, "stream_llm")
graph.add_node("stream_llm", streaming_llm_node)
app = graph.compile()

async def stream_conversation():
    config = {"configurable": {"thread_id": "stream_1"}}
    
    # 用户输入
    user_msg = HumanMessage(content="请流式回复")
    
    async for event in app.astream(
        {"messages": [user_msg]}, 
        config, 
        stream_mode="values"  # 每个state快照
    ):
        messages = event["messages"]
        last_msg = messages[-1]
        
        if isinstance(last_msg, AIMessageChunk):
            print(f"Chunk: {last_msg.content}", end="", flush=True)
        else:
            print(f"\n完整消息: {last_msg.content}")

# 运行：输出 "这是第一个chunk"（自动合并）
asyncio.run(stream_conversation())