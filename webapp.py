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
        # 发送一条文本消息（JSON 字符串）
        send_time = time.time()
        await websocket.send(message)

        # 循环接收数据流（复用同一个长连接）
        while True:
            try:
                data = await websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception:
                break

            # 仅处理文本消息
            if isinstance(data, bytes):
                try:
                    data = data.decode("utf-8")
                except Exception:
                    continue

            if not isinstance(data, str):
                continue

            # 解析 JSON，提取 text_response
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                # 非 JSON 的消息直接忽略
                continue

            if obj.get("type") != "text_response":
                continue

            piece = obj.get("text", "")
            if not piece or piece in ("SENTENCE_START", "SENTENCE_END"):
                # 只作为标记，不展示
                continue

            full_text += piece
            # 实时回调更新界面
            if on_update is not None:
                on_update(full_text)

            # 首个 token 延迟回调（只触发一次）
            if on_first_token is not None and not first_token_reported:
                elapsed = time.time() - send_time
                on_first_token(elapsed)
                first_token_reported = True

    except Exception as e:
        err = f"[连接 WebSocket 失败] {e}"
        if on_update is not None:
            on_update(err)
        return err

    return full_text if full_text else "[未收到服务端文本响应]"


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
            # 状态提示区和“首个回复延迟”指标，效果类似 Gradio 的进度提示
            status_placeholder = st.empty()
            status_placeholder.info("正在向 WebSocket 服务请求回复，请稍候...")
            latency_placeholder = st.empty()
            placeholder = st.empty()

            async def runner() -> str:
                # 将 query_message 序列化为 JSON 发送给后端
                payload = json.dumps(query_message, ensure_ascii=False)

                def on_first_token(elapsed: float) -> None:
                    # 首个 token 到达时，更新提示和延迟指标
                    status_placeholder.success(f"用时 {elapsed:.2f} 秒")

                return await stream_chat(
                    payload,
                    on_update=lambda text: placeholder.markdown(text or " "),
                    on_first_token=on_first_token,
                )

            # 所有 WebSocket 收发都复用同一个事件循环和长连接
            response_text = await runner()

        # 把助手最终回复加入会话状态
        st.session_state.messages.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    asyncio.run(main())

