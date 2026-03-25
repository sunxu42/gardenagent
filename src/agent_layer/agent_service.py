import asyncio
import inspect
import os
import uuid

from typing import Any, Awaitable, Callable, Dict, Optional

from src.log import setup_logger, logger
from src.agent_layer.agents.agent_factory import AgentFactory


class AgentService:
    def __init__(self, agent_config: dict = {}):
        self.agent_config = agent_config 

        self.agent = None
        self.queue = asyncio.Queue(maxsize=1000)
        self.result_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        
        
        self._read_task: Optional[asyncio.Task] = None

        self.session_id: Optional[str] = None
        self.is_running = False
        self.query_cache = set()
        self.is_new_session = True

    def set_result_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.result_callback = callback

    async def start(self):
        try:
            agent_config = dict(self.agent_config) if self.agent_config else {}
            agent_config.setdefault("agent_type", "yard_manager")
            self.agent = await AgentFactory.async_create_app(agent_config)
            self.is_running = True
            logger.info(f"Agent 服务已启动")
        except Exception as e:
            logger.error(f"启动 Agent 服务失败: {e}")
            raise
    
    async def stop(self):
        self.is_running = False

        # Best-effort: unblock read_event/process loops.
        try:
            if self.agent is not None:
                out_q = getattr(self.agent, "agent_output_queue", None)
                if out_q is not None:
                    out_q.put_nowait(None)
        except Exception:
            # Unblock is best-effort; don't fail stop.
            pass

        try:
            self.queue.put_nowait({"_stop": True})
        except Exception:
            pass

        # Cancel local drain task if it's still alive.
        if self._read_task is not None and not self._read_task.done():
            self._read_task.cancel()

        # 关闭agent的线程池
        # await self.agent.shutdown()
        if self.agent is not None and hasattr(self.agent, "aclose"):
            try:
                await self.agent.aclose()
            except Exception as e:
                logger.warning(f"agent aclose failed: {e}")
        logger.info("Agent 服务已停止")

    async def start_session(self):
        self.session_id = uuid.uuid4().hex
        self.is_new_session = False

    async def end_session(self):
        self.query_cache = set()
        self.is_new_session = True
    
    async def publish_response(self, message: Dict[str, Any]):
        if self.result_callback is None:
            logger.warning("publish_response: result_callback not set")
            return
        await self.result_callback(message)


    async def read_event(self):
        out_q = getattr(self.agent, "agent_output_queue", None)
        if out_q is None:
            logger.warning("read_event: agent_output_queue not found on agent")
            return

        # Track sentence state per event_id (safer if outputs interleave).
        started: set[str] = set()

        try:
            while self.is_running:
                evt = await out_q.get()
                if evt is None:
                    return
                try:
                    trigger_by = getattr(evt, "trigger_by", None)
                    # Backward/robustness: fall back to attribute or dict.
                    event_id = getattr(evt, "event_id", None) or getattr(evt, "id", None) or "unknown"
                    phase = getattr(evt, "phase", None) or "middle"
                    data = getattr(evt, "data", None)

                    # By default: do not forward heartbeat to front-end.
                    if (
                        trigger_by == "heartbeat"
                        and isinstance(data, dict)
                        and data.get("content", "").strip() == "HEARTBEAT_OK"
                    ):
                        continue

                    if phase == "start":
                        if event_id not in started:
                            await self.publish_response({"msg_type": "SENTENCE_START"})
                            started.add(event_id)
                        continue

                    if phase == "end":
                        # Only end if we have started for this event_id.
                        if event_id in started:
                            await self.publish_response({"msg_type": "SENTENCE_END"})
                            started.discard(event_id)
                            try:
                                # Avoid resetting session when multiple events interleave.
                                if not started:
                                    await self.end_session()
                            except Exception:
                                pass
                        continue

                    # middle: stream chunks
                    if event_id not in started:
                        # If the producer forgot to emit "start", we recover by auto-start.
                        await self.publish_response({"msg_type": "SENTENCE_START"})
                        started.add(event_id)

                    if isinstance(data, dict):
                        if "content" in data:
                            await self.publish_response(
                                {
                                    "msg_type": "response",
                                    "response": {"role": "assistant", "content": data.get("content", "")},
                                }
                            )
                        elif "updates" in data:
                            await self.publish_response(
                                {
                                    "msg_type": "response",
                                    "response": {"role": "updates", "updates": data.get("updates", "")},
                                }
                            )
                        else:
                            # Unknown dict payload: stringify as assistant content.
                            await self.publish_response(
                                {
                                    "msg_type": "response",
                                    "response": {"role": "assistant", "content": str(data)},
                                }
                            )
                    else:
                        await self.publish_response(
                            {
                                "msg_type": "response",
                                "response": {"role": "assistant", "content": str(data)},
                            }
                        )

                finally:
                    if hasattr(out_q, "task_done"):
                        out_q.task_done()

        except asyncio.CancelledError:
            logger.info("read_event: cancelled")
        except Exception as e:
            logger.error(f"read_event: loop failed: {e}")

    async def put_event(self, event: Any):
        in_q = getattr(self.agent, "agent_input_queue", None)
        if in_q is None:
            logger.warning("put_event: agent_input_queue not found on agent")
            return
        try:
            # Support both dict-style events and already-built InputEvent objects.
            from yard.events import InputEvent, USER_INPUT_EVENT

            if isinstance(event, InputEvent):
                await in_q.put(event)
                return
            # Dict event from handler
            text = event.get("content") or event.get("text") or ""
            if not text:
                return

            event_id = event.get("event_id") or uuid.uuid4().hex
            event_type = event.get("event_type") or USER_INPUT_EVENT
            input_event = InputEvent(content=text, event_id=event_id, event_type=event_type)
            await in_q.put(input_event)
        except Exception as e:
            logger.error(f"put_event failed: {e}")
    
    async def process(self):
        # Start draining agent outputs to front-end.
        self._read_task = asyncio.create_task(self.read_event(), name="agent_read_event")
        try:
            while self.is_running:
                message = await self.queue.get()
                if not message:
                    continue
                if isinstance(message, dict) and message.get("_stop") is True:
                    return

                text = message.get("text", "")
                is_final = message.get("is_final", False)
                source = message.get("source", "user")

                if not text:
                    continue

                if not is_final:
                    # Intermediate ASR text: fire-and-forget.
                    if text in self.query_cache:
                        continue
                    self.query_cache.add(text)
                    try:
                        if hasattr(self.agent, "create_llm_call_task"):
                            self.agent.create_llm_call_task(text)
                    except Exception as e:
                        logger.error(f"处理中间文本时出错: {e}")
                    continue

                # Final user turn: enqueue into yard input queue.
                if self.is_new_session:
                    await self.start_session()

                # Map both user and asr finals to yard "user" event_type.
                await self.put_event(
                    {
                        "content": text,
                        "event_type": "user",
                        "source": source,
                    }
                )
        except asyncio.CancelledError:
            logger.info("AgentService.process cancelled")
        finally:
            # Stop draining outputs.
            if self._read_task is not None:
                self._read_task.cancel()
            try:
                if self._read_task is not None:
                    await self._read_task
            except asyncio.CancelledError:
                pass
    




if __name__ == "__main__":
    async def main():
        # 配置统一日志
        setup_logger(log_file=os.getenv('AGENT_SERVICE_LOG', 'logs/agent_service.log'), enable_console=True)
        
        robot =  AgentService()
        try:
            # 启动服务
            await robot.start()
            
                # 开始监听和处理    
            await robot.process()
            
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        except Exception as e:
            logger.error(f"服务运行出错: {e}")
        finally:
            await robot.stop()
    asyncio.run(main())
