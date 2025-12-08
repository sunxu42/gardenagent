import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量（若未手动设置，可通过 .env 文件加载）
# load_dotenv()

# 初始化智普 AI 对话模型
chat_model = ChatZhipuAI(
    model="glm-4",  # 模型名称：glm-4 / glm-3-turbo / glm-4v（多模态）
    api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE",
    temperature=0.7,  # 随机性，0-1 之间
    max_tokens=1024,  # 最大生成token数
)

# 构造对话消息
messages = [
    SystemMessage(content="你是一个专业的助手，回答简洁准确"),
    HumanMessage(content="介绍一下 LangChain 框架的核心功能")
]

# 调用模型（同步）
response = chat_model.invoke(messages)
print("模型响应：", response.content)

