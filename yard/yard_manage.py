import os
import asyncio
from dotenv import load_dotenv
load_dotenv() 
from langchain_openai import ChatOpenAI

GLM_API_KEY = os.getenv('GLM_OPENAI_API_KEY')
GLM_BASE_URL = os.getenv('GLM_OPENAI_BASE_URL')

def create_glm_model():

    model = ChatOpenAI(
        model="glm-4.7",  
        api_key=GLM_API_KEY,
        base_url=GLM_BASE_URL,
        temperature=0.7,
        max_tokens=20000,
    )
    return model

class YardManager:

    def __init__(self):
        pass
    
    async def create_agent(self):
        pass

    async def run_single_turn(self, user_input: str):
        pass
    

    
    async def achat(self, user_input: str):
        pass