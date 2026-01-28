import requests
from typing import Any, Dict, Optional
from fastmcp import FastMCP


class EmbenchClient:

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: float = 30.0):

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def instruction(self) -> Dict[str, Any]:
        """
        Send an instruction to the server.
        
        Args:
            instruction: The instruction text to send
            **kwargs: Additional parameters to include as query parameters
        
        Returns:
            Response from the /instruction endpoint
        """
        url = f"{self.base_url}/instruction"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def tools(
        self,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Get available tools from the server.
        
        Args:
            **kwargs: Additional parameters to include as query parameters
        
        Returns:
            Response from the /tools endpoint containing available tools
        """
        url = f"{self.base_url}/tools"
        response = requests.get(url, params=kwargs, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:

        url = f"{self.base_url}/execute_tool"
        payload = {
            "tool_name": tool_name,
            "arguments": tool_args,
            **kwargs
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def observation(
        self,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/observation"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        image_base64 = response.json().get("image_base64")

        final_image = f"data:image/png;base64,{image_base64}"
        return final_image





# Example usage
if __name__ == "__main__":
    # Example 1: Using the client class
    client = EmbenchClient()
    
    # Get available tools
    tools = client.tools()
    print("Available tools:", tools)
    
    # Send an instruction
    result = client.instruction()
    print("Instruction result:", result)
    
    # Execute a tool action
    tool_result = client.execute_tool(
        "pick",
        {"target": "ball"}
    )
    print("Tool result:", tool_result)
    
    # Send an observation
    obs_result = client.observation()
    # print("Observation result:", obs_result)
    
    
    # Example 2: Using convenience functions
    # tools = get_tools()
    # print("Tools:", tools)


# from zhipuai import ZhipuAI

# client = ZhipuAI(api_key="83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE")  # 请填写您自己的 API Key

# response = client.chat.completions.create(
#   model="glm-4.6v",
#   messages=[ 
#     {"role": "user", "content": [
#       {
#         "type": "image_url",
#         "image_url": {
#           "url": obs_result
#         },
#       },
#       {"type": "text","text": "图片中有什么"},
#     ]}
#   ],
#   thinking={
#     "type": "disabled",
#   },
#   temperature=0.0
# )

# # 获取完整回复
# print(response.choices[0].message)