import json
from loguru import logger
try:
    from mcp_client import get_tools
except ImportError:
    from .mcp_client import get_tools

class ToolManager:
    def __init__(self):
        self.tools = None
        self.tool_node = None
        self.tool_map = None

    async def create_tools(self):
        self.tools = await get_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        logger.info(f"tool_names: {self.tool_map.keys()}")

    def _parse_result(self, result):
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试 eval（仅用于安全场景）
                try:
                    return eval(result)
                except:
                    return {"error": f"无法解析结果: {result}"}
        return result

    async def get_grass_height(self) -> dict:
        tool = self.tool_map["get_grass_height"]
        result = await tool.ainvoke({"sensor_id": "grass-001"})
        return self._parse_result(result)

    async def get_humidity(self) -> dict:
        tool = self.tool_map["get_soil_moisture"]
        result = await tool.ainvoke({"sensor_id": "soil-001"})
        parsed = self._parse_result(result)
        # 将 moisture_percent 映射到 humidity
        if isinstance(parsed, dict) and "moisture_percent" in parsed:
            parsed["humidity"] = parsed.pop("moisture_percent")
        return parsed

    async def get_watering_record(self) -> dict:
        tool = self.tool_map["list_irrigation_logs"]
        result = await tool.ainvoke({"limit": 5})
        parsed = self._parse_result(result)
        # 如果返回的是列表，包装成字典
        if isinstance(parsed, list):
            return {"watering_record": parsed}
        return parsed

    async def get_knowledge_base(self) -> dict:
        tool = self.tool_map["get_irrigation_knowledge"]
        result = await tool.ainvoke({})
        parsed = self._parse_result(result)
        # 如果返回的是字典，确保有 knowledge_base 键
        if isinstance(parsed, dict) and "knowledge_base" not in parsed:
            return {"knowledge_base": parsed}
        return parsed
