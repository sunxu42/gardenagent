import asyncio
import os
import uuid

from typing import Any, Awaitable, Callable, Dict, Optional

from src.log import setup_logger, logger
from src.agent_layer.agents.agent_factory import AgentFactory
from yard.events import InputEvent, USER_INPUT_EVENT

class AgentService:
    def __init__(self, agent_config: dict = {}):
        self.agent_config = agent_config 

        self.agent = None
        self.queue = asyncio.Queue(maxsize=1000)
        self.result_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        
        
        self._read_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None

        self.is_running = False
        self.is_new_session = True

    def set_result_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.result_callback = callback

    def _validate_agent(self) -> None:
        if not hasattr(self.agent, "agent_output_queue"):
            raise RuntimeError("agent_output_queue not found on agent")
        if not hasattr(self.agent, "agent_input_queue"):
            raise RuntimeError("agent_input_queue not found on agent")

    def _out_q(self) -> Any:
        self._validate_agent()
        return self.agent.agent_output_queue

    def _in_q(self) -> Any:
        self._validate_agent()
        return self.agent.agent_input_queue

    async def start(self):
        try:
            self.agent = await AgentFactory.async_create_app(self.agent_config)
            self._validate_agent()
            self.is_running = True
            self._read_task = asyncio.create_task(self.read_event())
            self._process_task = asyncio.create_task(self.put_event())
            logger.info(f"Agent 服务已启动")
        except Exception as e:
            logger.error(f"启动 Agent 服务失败: {e}")
            raise
    
    async def stop(self):
        self.is_running = False
        try:
            self.agent.agent_output_queue.put_nowait(None)
        except Exception:
            pass
        try:
            self.queue.put_nowait({"_stop": True})
        except Exception:
            pass

        for t in (self._process_task, self._read_task):
            if t is None:
                continue
            if not t.done():
                t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

        if self.agent is not None and hasattr(self.agent, "aclose"):
            try:
                await self.agent.aclose()
            except Exception as e:
                logger.warning(f"agent aclose failed: {e}")
        logger.info("Agent 服务已停止")

    async def start_session(self):
        self.is_new_session = False

    async def end_session(self):
        self.is_new_session = True
    
    async def publish_response(self, message: Dict[str, Any]):
        if self.result_callback is None:
            logger.warning("publish_response: result_callback not set")
            return
        await self.result_callback(message)

    async def read_event(self):
        out_q = self._out_q()
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
    
    async def put_event(self):
        
        while self.is_running:
            in_q = self._in_q()
            message = await self.queue.get()
            if not message:
                continue
            if isinstance(message, dict) and message.get("_stop") is True:
                return

            text = message.get("text", "")
            is_final = message.get("is_final", False)

            if not text:
                continue

            if not is_final:
                # 暂时下线中间文本处理
                continue
  

            if self.is_new_session:
                await self.start_session()

            input_event = InputEvent(
                content=text, 
                event_id=uuid.uuid4().hex, 
                event_type=USER_INPUT_EVENT,
            )
            await in_q.put(input_event)
    




if __name__ == "__main__":
    async def main():
        # 配置统一日志
        setup_logger(log_file=os.getenv('AGENT_SERVICE_LOG', 'logs/agent_service.log'), enable_console=True)
        
        robot =  AgentService()
        try:
            # 启动服务
            await robot.start()
            
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        except Exception as e:
            logger.error(f"服务运行出错: {e}")
        finally:
            await robot.stop()
    asyncio.run(main())
