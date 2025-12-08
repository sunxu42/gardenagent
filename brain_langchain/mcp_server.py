from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool
def get_grass_height(sensor_id: str = "grass-001") -> dict:
    """虚拟草高传感器数据获取接口。"""
    return {
        "sensor_id": sensor_id,
        "height_cm": 7.5,
        "status": "ok",
        "timestamp": "2025-12-08T10:00:00Z",
    }


@mcp.tool
def get_soil_moisture(sensor_id: str = "soil-001") -> dict:
    """虚拟土壤湿度获取接口。"""
    return {
        "sensor_id": sensor_id,
        "moisture_percent": 42.0,
        "status": "ok",
        "timestamp": "2025-12-08T10:00:00Z",
    }


@mcp.tool
def list_irrigation_logs(limit: int = 5) -> list:
    """虚拟灌溉记录获取接口。"""
    return [
        {
            "id": f"log-{i}",
            "started_at": f"2025-12-08T0{i}:00:00Z",
            "duration_min": 15 + i,
            "volume_l": 120 + i * 5,
        }
        for i in range(1, limit + 1)
    ]


@mcp.tool
def get_irrigation_knowledge() -> dict:
    """虚拟灌溉知识库搭建示例。"""
    return {
        "rules": [
            "土壤湿度低于35%时启动灌溉",
            "预计降雨时暂停灌溉",
            "夜间灌溉可减少蒸发损失",
        ],
        "crop_profiles": {
            "lawn": {"target_moisture_percent": 45, "max_daily_minutes": 30},
            "flowers": {"target_moisture_percent": 50, "max_daily_minutes": 25},
        },
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