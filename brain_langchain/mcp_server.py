from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")


@mcp.tool
def mock_weather_forecast() -> dict:
    return {
        "sunrise": "06:20",
        "rain_expected": False,
        "note": "近24小时无显著降雨",
    }


@mcp.tool
def mock_grass_height(sensor_id: str = "grass-001") -> dict:
    return {
        "sensor_id": sensor_id,
        "height_cm": 7.0,
        "status": "ok",
        "timestamp": "2025-12-08T10:00:00Z",
    }


@mcp.tool
def mock_soil_moisture(sensor_id: str = "soil-001") -> dict:
    """虚拟土壤湿度获取接口。"""
    return {
        "sensor_id": sensor_id,
        "moisture_percent": 28.0,
        "status": "ok",
        "timestamp": "2025-12-08T10:00:00Z",
    }


@mcp.tool
def mock_irrigation_logs() -> dict:

    return {
        "result": "24小时前浇过水，水量120升",
    }

@mcp.tool
def mock_irrigation_knowledge() -> dict:
    return {
        "rules": [
            "土壤湿度低于35%时启动灌溉",
            "预计降雨时暂停灌溉",
            "夜间灌溉可减少蒸发损失",
            "割草后24小时内避免浇水以减少病菌风险",
            "草坪高度大于6cm时需要修剪",
        ],
    }


@mcp.tool
def control_mower(action: str, area: str = "front-yard") -> dict:
    """虚拟割草机控制接口。"""
    if action not in {"start", "stop", "dock"}:
        return {"status": "error", "message": "Invalid action"}
    return {
        "status": "accepted",
        "action": action,
        "area": area,
        "started_at": "2025-12-08T10:05:00Z",
    }


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)