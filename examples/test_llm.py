# -*- encoding: utf-8 -*-
'''
@File    :   openai.py
@Time    :   2025/07/11 09:40:06
@Author  :   lpl
@Desc    :   None
'''


import time
from typing import Dict, List
import openai
import re

def remove_thinking_tags(text: str) -> str:
    return re.sub(r"^<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()

# 尽可能少的引用其他模块
class OpenAILLM:
    def __init__(self, config: Dict):
        self.config = config

        self.model_name = config.get("model_name")
        self.api_key = config.get("openai_api_key")
        self.base_url = config.get("openai_base_url")

        # params
        self.temperature=config.get("temperature", 0.3)
        self.max_tokens=config.get("max_tokens", 1000)
        self.top_p=config.get("top_p", 0.3)
        self.client = openai.Client(api_key=self.api_key, 
                                    base_url=self.base_url
                                    )
        self.tool_choice = config.get("tool_choice", "auto")

    def generate(self, messages: List, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=kwargs.get("stream", False),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
        )

        # print(__name__, f"Response from OpenAI: {response.model_dump_json()}")
        response_content = response.choices[0].message.content
        if "<think>" in response_content:
            return remove_thinking_tags(response_content)
        else:
            return response_content
    
    
 
    def response_with_functions(self, messages: List, functions=None, **kwargs):
        stream = self.client.chat.completions.create(
                model=self.model_name, 
                messages=messages, 
                stream=True, 
                tools=functions,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                tool_choice=kwargs.get("tool_choice", self.tool_choice ),
                extra_body={
                    "thinking": {"type": "disabled" }
                }
                )
        
        for chunk in stream:
            yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls
    
    def response_with_functions_and_stream(self, messages: List, functions=None, **kwargs):
        """
        返回生成器和 stream 对象，用于支持提前关闭连接
        返回: (generator, stream_object)
        """
        stream = self.client.chat.completions.create(
                model=self.model_name, 
                messages=messages, 
                stream=True, 
                tools=functions,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                tool_choice=kwargs.get("tool_choice", self.tool_choice ),
                extra_body={
                    "thinking": {"type": "disabled" }
                }
                )
        
        def generator():
            for chunk in stream:
                    yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls

        
        return generator(), stream


from langchain_openai import ChatOpenAI
def load_model() -> ChatOpenAI:
        return ChatOpenAI(
            model="glm-4.6",
            api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            temperature=0.0,
            max_tokens=1000,
            streaming=True,
            # thinking=False,
            extra_body={
                "thinking": {"type": "disabled" }
            }
        )

if __name__ == "__main__":
    config = {
        "model_name": "glm-4.6",
        "openai_api_key": "83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
        "openai_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "temperature": 0.0,
        "max_tokens": 1000,
        "top_p": 0.3,
    }
    llm = OpenAILLM(config)
    
    responses = llm.response_with_functions([{"role": "user", "content": "你是谁"}])
    count = 0
    st = time.time()
    for response in responses:
        et = time.time()
        print(f"count: {count}, time: {et - st}, response: {response}")
        count += 1
    time.sleep(3)
    print("--------------------------------")
    llm = load_model()
    responses = llm.stream([{"role": "user", "content": "你是谁"}],
     max_tokens=1000, 
     temperature=0.0, 
     top_p=0.3, 
     tool_choice="auto", 
    #  extra_body={
    #                 "thinking": {"type": "disabled" }
    #             })
    )
    count = 0
    st = time.time()
    for response in responses:
        et = time.time()
        print(f"count: {count}, time: {et - st}, response: {response}")
        count += 1
