import asyncio
import time
import os
from typing import Callable, Dict, Any, Optional
from loguru import logger
from src.log import setup_logger
    
from src.agent_layer.agents.agent_factory import AgentFactory
import uuid


class AgentService:
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        self.is_running = False
        self.query_cache = set()
        self.is_new_session = True
        self.agent = None
        self.queue = asyncio.Queue(maxsize=1000)
        self.result_callback = None
    
    def set_result_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.result_callback = callback

    async def start(self):
        try:
            agent_config = {
                "agent_type": "yard_manager",
            }   
            self.agent = await AgentFactory.async_create_app(agent_config)
            self.is_running = True
            logger.info(f"Agent 服务已启动")
        except Exception as e:
            logger.error(f"启动 Agent 服务失败: {e}")
            raise
    
    async def stop(self):
        self.is_running = False
        # 关闭agent的线程池
        # await self.agent.shutdown()
        logger.info("Agent 服务已停止")


    async def start_session(self):
        self.session_id = uuid.uuid4().hex
        self.is_new_session = False


    async def end_session(self):
        self.query_cache = set()
        self.is_new_session = True


    async def process(self):
        while self.is_running:
            try:
                message = await self.queue.get()
                if message:
                    text = message.get('text', '')
                    is_final = message.get('is_final', False)
                    if self.is_new_session:
                        await self.start_session()                        

                    if is_final:
                        await self.process_final_text(text)
                    else:
                        await self.process_intermediate_text(text)
  
            except asyncio.CancelledError:
                logger.info("Agent 处理循环已取消")
                break
            except Exception as e:
                logger.error(f"接收文本时出错: {e}")
                await asyncio.sleep(0.1)
           
    async def process_intermediate_text(self, text: str):
        
        if text in self.query_cache:
            return
        
                
        self.query_cache.add(text)
        try:
            logger.info(f"处理中间文本: {text}")

            # 创建LLM调用任务，不等待结果
            self.agent.create_llm_call_task(text)
            
        except Exception as e:
            logger.error(f"处理中间文本时出错: {e}")
    
    async def process_final_text(self, text: str):
        logger.info(f"处理最终文本: {text}")
        count = 0
        first_content = True
        async for response in self.agent.achat(text):
            if response:
                # 处理字典类型的响应（包含 updates 或 content）
                if isinstance(response, dict):
                    if "updates" in response:
                        # 发送中间状态更新
                        await self.publish_response(
                            response["updates"], 
                            index=count, 
                            msg_type="updates"
                        )
                    elif "content" in response:
                        # 发送内容更新
                        if first_content:
                            await self.publish_response("SENTENCE_START", index=-1)
                            first_content = False
                        await self.publish_response(
                            response["content"], 
                            index=count, 
                            msg_type="content"
                        )
                        count += 1
                else:
                    # 兼容旧的字符串类型响应
                    if count == 0:
                        await self.publish_response("SENTENCE_START", index=-1)
                    await self.publish_response(response, index=count, msg_type="content")
                    count += 1
        await self.publish_response("SENTENCE_END", index=-1)
        await self.end_session()

    
    async def publish_response(self, response: str, index: int=-1, msg_type: str="content"):
        """
        发布响应消息
        
        Args:
            response: 响应内容
            index: 响应索引
            msg_type: 消息类型，可选值: "content"（内容）, "updates"（中间状态更新）
        """
        message = {
            'text': response,
            'timestamp': time.time(),
            'index': index,
            'source': 'agent',
            'msg_type': msg_type  # 添加消息类型标识
        }
        await self.result_callback(message)




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


if __name__ == "__main__":
    asyncio.run(main())
