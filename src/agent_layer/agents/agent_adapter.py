import time
import threading
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from loguru import logger
from fairland_brain.agent_services.agent import Agent
from fairland_brain.agent_services.configs.configs import agent_config as configs
from fairland_brain.agent_services.legacy_dep.core.utils.dialogue import Message
import copy
class ClientState:
    def __init__(self):
        self.client_abort = False


class RobotAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_calls = {}
        self.task_queues = {}  # 用于流式处理的结果队列
        self.task_metadata = {}
        self.session_id = None
        # 创建线程池用于并行处理LLM调用
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm_worker")
        self.lock = threading.Lock()



    def llm_call(self, query, count=1):
        messages, functions, tool_choice = self.prepare_llm_params(query, count)
        messages = messages + [{"role": "user", "content": query}]
        llm_responses = self.llm.response_with_functions(messages=messages, functions=functions, tool_choice=tool_choice)
        for content, tool_calls in llm_responses:
            yield content, tool_calls
        
    
    def chat(self, query, conn=None):
        logger.info(f"大模型收到用户消息: {query}, 系统语言: {self.system_language}")
        self.dialogue.put(Message(role="user", content=query))
        count = 0
        while count < self.max_loop_count:
            count += 1
            logger.info(f"当前轮次: {count}")
            t1 = time.time()
            messages, functions, tool_choice = self.prepare_llm_params(query, count)
            func_name = [f['function']["name"] for f in functions] 
            t2 = time.time()
            logger.info(f"prepare_llm_params耗时: {t2 - t1:.3f}秒")
            if count > 1:
                llm_responses = self.llm.response_with_functions(messages=messages, functions=functions, tool_choice=tool_choice)
            else:
                llm_responses = self.retrieve_final_llm_call_task(query)
            if llm_responses is None:
                logger.info(f"llm_responses is None, 重新调用llm")
                t2 = time.time()
                llm_responses = self.llm.response_with_functions(messages=messages, functions=functions, tool_choice=tool_choice)
            should_continue = yield from self._process_streaming_response(llm_responses, functions, conn, t2)
            
            # 如果不需要继续循环（纯文本响应或工具调用完成），则退出循环
            if not should_continue:
                break
    
    async def achat(self, query, conn=None) -> AsyncGenerator[str, None]:
        """异步版本的 chat 方法
        
        Args:
            query: 用户查询文本
            conn: 连接对象（可选）
            
        Yields:
            str: 流式返回的响应内容
        """
        import asyncio
        
        # 创建异步队列用于在线程和异步代码之间传递数据
        result_queue = asyncio.Queue()
        exception_queue = asyncio.Queue()
        done_event = asyncio.Event()
        
        # 获取当前事件循环（在异步函数中）
        loop = asyncio.get_running_loop()
        
        def run_sync_chat():
            """在线程中运行同步的 chat 生成器"""
            try:
                for response in self.chat(query, conn):
                    # 将结果放入异步队列，使用闭包中的 loop
                    asyncio.run_coroutine_threadsafe(
                        result_queue.put(response), 
                        loop
                    )
            except Exception as e:
                # 将异常放入异常队列
                asyncio.run_coroutine_threadsafe(
                    exception_queue.put(e),
                    loop
                )
            finally:
                # 标记完成
                asyncio.run_coroutine_threadsafe(
                    done_event.set(),
                    loop
                )
        
        # 在线程池中运行同步生成器
        future = loop.run_in_executor(self.thread_pool, run_sync_chat)
        
        # 异步生成器：从队列中获取结果
        while True:
            # 检查是否有异常
            try:
                exception = exception_queue.get_nowait()
                raise exception
            except asyncio.QueueEmpty:
                pass
            
            # 检查是否完成
            if done_event.is_set():
                # 确保所有结果都被消费
                while not result_queue.empty():
                    try:
                        response = result_queue.get_nowait()
                        yield response
                    except asyncio.QueueEmpty:
                        break
                break
            
            # 尝试获取结果
            try:
                # 使用超时避免无限等待
                response = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                yield response
            except asyncio.TimeoutError:
                # 超时后继续循环检查完成状态
                continue
            except asyncio.QueueEmpty:
                continue
        
        # 等待线程任务完成
        await future
        
    def retrieve_final_llm_call_task(self, query):
        if query[-1] in ["。", "！", "？", "，", "?", "!", ","]:
            query = query[:-1]
        if query not in self.active_calls:
            return None
        
        return self._stream_from_queue(query)

    
    def _stream_from_queue(self, query):
        """从队列中流式获取结果"""
        queue_obj = self.task_queues.get(query)
        if not queue_obj:
            return None
        
        def response_generator():
            while True:
                try:
                    # 非阻塞获取结果
                    response = queue_obj.get_nowait()
                    if response['type'] == 'response':
                        yield response['content'], response['tool_calls']
                    elif response['type'] == 'completed':
                        break
                    elif response['type'] == 'error':
                        raise Exception(f"任务出错: {response['error']}")
                except queue.Empty:
                    # 队列为空，等待一下再重试
                    time.sleep(0.01)
                    continue
                except Exception as e:
                    logger.error(f"流式处理出错: {e}")
                    break
        
        return response_generator()
        

    def create_llm_call_task(self, query):
        with self.lock:
            if query in self.active_calls:
                return
            
            # 创建结果队列
            result_queue = queue.Queue()
            self.task_queues[query] = result_queue
            
            # 创建任务元数据
            self.task_metadata[query] = {
                'status': 'running',
                'start_time': time.time(),
                'response_count': 0
            }
            
            # 使用线程池提交同步任务
            future = self.thread_pool.submit(self._process_llm_call, query, result_queue)
            self.active_calls[query] = future
    
    def _process_llm_call(self, query, result_queue):
        """在线程池中执行的LLM调用处理函数，流式处理结果"""
        t1 = time.time()
        try:
            logger.info(f"开始处理LLM调用: {query}")
            response_count = 0
            
            # 流式处理LLM响应
            for content, tool_calls in self.llm_call(query):
                if response_count == 0:
                    t = time.time() - t1
                response_count += 1
                # 将结果放入队列
                result_queue.put({
                    'type': 'response',
                    'content': content,
                    'tool_calls': tool_calls,
                    'timestamp': time.time()
                })
                
                with self.lock:
                    self.task_metadata[query]['response_count'] = response_count
            
            # 标记任务完成
            result_queue.put({'type': 'completed'})
            
            with self.lock:
                self.task_metadata[query]['status'] = 'completed'
            
            logger.info(f"LLM调用完成: {query}, 结果数量: {response_count}, first_token_time: {t:.3f}秒")
            
        except Exception as e:
            logger.error(f"LLM调用出错: {query}, 错误: {e}")
            result_queue.put({'type': 'error', 'error': str(e)})
            
            with self.lock:
                self.task_metadata[query]['status'] = 'error'
    
    def shutdown(self):
        """关闭线程池"""
        logger.info("正在关闭LLM线程池...")
        self.thread_pool.shutdown(wait=True)
        logger.info("LLM线程池已关闭")



