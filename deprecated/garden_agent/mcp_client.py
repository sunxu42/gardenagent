from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
import asyncio


client = MultiServerMCPClient(  
    {
       
        "weather": {
            "transport": "streamable_http",  # HTTP-based remote server
            # Ensure you start your weather server on port 8000
            "url": "http://localhost:8000/mcp",
        }
    }
)

async def get_tools():
    tools = await client.get_tools()  
    return tools


def get_tools_sync():
    """同步获取工具，便于在脚本中直接调用。"""
    return asyncio.run(get_tools())

if __name__ == "__main__":
    tools = asyncio.run(get_tools())
    print(tools)
"""
[StructuredTool(name='greet', args_schema={'properties': {'name': {'type': 'string'}}, 'required': ['name'], 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd484a0>), StructuredTool(name='get_grass_height', description='虚拟草高传感器数据获取接口。', args_schema={'properties': {'sensor_id': {'default': 'grass-001', 'type': 'string'}}, 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd64720>), StructuredTool(name='get_soil_moisture', description='虚拟土壤湿度获取接口。', args_schema={'properties': {'sensor_id': {'default': 'soil-001', 'type': 'string'}}, 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd645e0>), StructuredTool(name='list_irrigation_logs', description='虚拟灌溉记录获取接口。', args_schema={'properties': {'limit': {'default': 5, 'type': 'integer'}}, 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd644a0>), StructuredTool(name='get_irrigation_knowledge', description='虚拟灌溉知识库搭建示例。', args_schema={'properties': {}, 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd65300>), StructuredTool(name='control_mower', description='虚拟割草机控制接口。', args_schema={'properties': {'action': {'type': 'string'}, 'area': {'default': 'front-yard', 'type': 'string'}}, 'required': ['action'], 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x79cd0fd65440>)]

"""