import asyncio
import json
import os
import time

import streamlit as st
import websockets


def get_ws_url() -> str:
    host = os.getenv("WEBSOCKET_HOST", "localhost")
    port = os.getenv("WEBSOCKET_PORT", "8005")
    scheme = "ws"
    return f"{scheme}://{host}:{port}"


async def get_or_create_ws():
    ws = st.session_state.get("ws_conn")
    # 某些实现返回的连接对象没有 closed 属性，这里用 getattr 做兼容
    is_closed = getattr(ws, "closed", True) if ws is not None else True
    if ws is None or is_closed:
        ws = await websockets.connect(get_ws_url())
        st.session_state.ws_conn = ws
    return ws


async def stream_chat(message: str, on_update, on_first_token=None) -> str:
    full_text: str = ""
    first_token_reported = False

    try:
        websocket = await get_or_create_ws()
        send_time = time.time()
        await websocket.send(message)
        while True:
            data = await websocket.recv()
       
            if isinstance(data, bytes):
                try:
                    data = data.decode("utf-8")
                except Exception:
                    continue

            if not isinstance(data, str):
                continue

            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue

            if obj.get("type") != "text_response":
                continue

            piece = obj.get("text", "")
            if not piece or piece =="SENTENCE_START":
                continue
            if piece =="SENTENCE_END":
                break
            full_text += piece
            if on_update is not None:
                on_update(full_text)
            if on_first_token is not None and not first_token_reported:
                elapsed = time.time() - send_time
                on_first_token(elapsed)
                first_token_reported = True

    except Exception as e:
        err = f"[连接 WebSocket 失败] {e}"
        if on_update is not None:
            on_update(err)
        return err
    return full_text 


async def main() -> None:
    st.set_page_config(page_title="GardenAgent Chat", page_icon="💬", layout="centered")

    st.title("GardenAgent Chat")
    st.caption("使用 Streamlit + WebSocket 的简单聊天页面")

    # 初始化全局事件循环和长连接（只在首次加载时创建）
    if "ws_conn" not in st.session_state:
        st.session_state.ws_conn = await get_or_create_ws()


    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 历史消息展示
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # 输入框
    user_input = st.chat_input("输入你的问题，然后回车发送...")

    if user_input:
        # 先把用户消息加入聊天记录
        query_message = {"type": "llm", "role": "user", "content": user_input}
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 在界面上显示流式回答
        with st.chat_message("assistant"):
            placeholder = st.empty()
            status_placeholder = st.empty()
            status_placeholder.info("正在向 WebSocket 服务请求回复，请稍候...")
            

            async def runner() -> str:
                payload = json.dumps(query_message, ensure_ascii=False)

                def on_first_token(elapsed: float) -> None:
                    status_placeholder.success(f"用时 {elapsed:.2f} 秒")

                return await stream_chat(
                    payload,
                    on_update=lambda text: placeholder.markdown(text or " "),
                    on_first_token=on_first_token,
                )
            
            response_text = await runner()
            placeholder.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    asyncio.run(main())

