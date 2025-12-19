from fastmcp import FastMCP
from datetime import datetime
import random
"""
1. 获取天气信息（气温，日照，风速等）【已完成】
2. 获取光伏系统累计发电量
3. 获取泳池机器人状态
4. 获取草高
5. 获取割草记录
6. 启动割草机（启动成功后，返回割草机模式）
7. 启动灌溉系统（支持定时）
8. 获取水池温度，水质
9. 获取用户偏好
10. 启动冲浪器接口（支持定时）
"""

mcp = FastMCP("My MCP Server")

# 场景一涉及工具
@mcp.tool
def mock_weather_forecast() -> dict:
    return {
        "date": "2025-12-08",
        "current_temperature": 30,
        "temperature_high": 35,
        "temperature_low": 29,
        "weather": "晴天",
        "humidity": "45%",
        "wind_speed": "8km/h 西南风",
        "sunrise": "06:19",
        "sunset": "17:03",
        "uv_index": "中等",
        "rain_expected": False,
    }

@mcp.tool
def mock_solar_system_energy() -> dict:
    return {
        "today_energy_generated_kwh": 4.4,
        "status": "ok",
        "timestamp": datetime.now().isoformat(), 
    }


# 场景三涉及工具
def mock_pool_status() -> dict:
    """
    返回泳池状态。

    返回值:
        temperature_celsius (float): 当前泳池水温（摄氏度）。
        water_quality (str): 当前泳池水质状态。
        ph_value (float): PH值。
        chlorine_level_mg_per_l (float): 氯含量（毫克/升）。
        status (str): 泳池当前总体状态。
        cleaning_status (str): 清洁状态（正在清洁中/清洁完成）。
        timestamp (str): 时间戳，ISO 8601 格式。
    """
    cleaning_status = "正在清洁中" if random.random() < 0.5 else "清洁完成"
    return {
        "temperature_celsius": 16.5,
        "water_quality": "良好",
        "ph_value": 7.2,
        "chlorine_level_mg_per_l": 1.5,
        "status": "水清澈，无异常",
        "cleaning_status": cleaning_status,
        "timestamp": datetime.now().isoformat(), 
    }
@mcp.tool
def mock_swimming_preference() -> dict:


    swimming_preference_markdown = """
    ### 游泳时用户偏好

- **理想水温**：28°C
- 游泳时打开冲浪器，冲浪器模式为：热身，挑战，舒缓。冲浪器模式偏好为：热身5分钟，挑战20分钟，舒缓10分钟。
"""
    return {
        "swimming_preference_markdown": swimming_preference_markdown,
    }



@mcp.tool
def control_heat_pump(action: str = "start", target_temperature_celsius: float = 28.0) -> dict:
    """
    控制泳池热泵启动或暂停。

    Args:
        action: "start" 启动热泵，"pause" 暂停热泵
        target_temperature_celsius: 目标加热温度，仅在启动时需要

    Returns:
        dict: 执行结果详情
    """
    valid_actions = {"start", "pause"}
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    if action == "start":
        return {
            "status": "success",
            "action": "start_heat_pump",
            "target_temperature_celsius": target_temperature_celsius,
            "message": f"热泵已启动，目标温度设为 {target_temperature_celsius}°C",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # pause
        return {
            "status": "success",
            "action": "pause_heat_pump",
            "message": "热泵已暂停",
            "timestamp": "2025-12-08T10:00:00Z",
        }

@mcp.tool
def control_water_pump(action: str = "start", target_temperature_celsius: float = None, flow_rate_l_min: float = None) -> dict:
    """
    控制泳池水泵启动、暂停或调节。

    Args:
        action: "start" 启动水泵, "pause" 暂停水泵, "adjust" 调节水泵参数
        target_temperature_celsius: 目标调节温度（可选，仅部分场景用）
        flow_rate_l_min: 目标流量（升/分钟，可选，仅调节用）

    Returns:
        dict: 执行结果描述
    """
    valid_actions = {"start", "pause", "adjust"}
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    
    if action == "start":
        msg = "水泵已启动"
        if target_temperature_celsius is not None:
            msg += f"，目标温度：{target_temperature_celsius}°C"
        if flow_rate_l_min is not None:
            msg += f"，流量：{flow_rate_l_min}升/分钟"
        return {
            "status": "success",
            "action": "start_water_pump",
            "target_temperature_celsius": target_temperature_celsius,
            "flow_rate_l_min": flow_rate_l_min,
            "message": msg,
            "timestamp": "2025-12-08T10:00:00Z",
        }
    elif action == "pause":
        return {
            "status": "success",
            "action": "pause_water_pump",
            "message": "水泵已暂停",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # adjust
        if flow_rate_l_min is None:
            return {"status": "error", "message": "调节水泵时必须提供流量(flow_rate_l_min)"}
        msg = f"水泵已调节，流量设为{flow_rate_l_min}升/分钟"
        if target_temperature_celsius is not None:
            msg += f"，目标温度：{target_temperature_celsius}°C"
        return {
            "status": "success",
            "action": "adjust_water_pump",
            "target_temperature_celsius": target_temperature_celsius,
            "flow_rate_l_min": flow_rate_l_min,
            "message": msg,
            "timestamp": "2025-12-08T10:00:00Z",
        }

@mcp.tool
def control_cleaning_robot(action: str = "start", mode: str = "deep", duration_minutes: int = 60) -> dict:
    """
    控制泳池清洁机器人。

    Args:
        action: "start" 启动清洁, "pause" 暂停, "dock" 返回充电座
        mode: "quick" 快速清洁, "deep" 深度清洁, "edge" 仅清洁边缘
        duration_minutes: 清洁持续时间（分钟）

    Returns:
        dict: 执行结果描述
    """
    valid_actions = {"start", "pause", "dock"}
    valid_modes = {"quick", "deep", "edge"}
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    if mode not in valid_modes:
        return {"status": "error", "message": f"无效的清洁模式: {mode}"}
    if not (10 <= duration_minutes <= 180):
        return {"status": "error", "message": "清洁时长需在10-180分钟之间"}

    if action == "start":
        return {
            "status": "success",
            "action": "start_cleaning_robot",
            "mode": mode,
            "duration_minutes": duration_minutes,
            "message": f"清洁机器人已启动，模式为{mode}，预计清洁{duration_minutes}分钟",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    elif action == "pause":
        return {
            "status": "success",
            "action": "pause_cleaning_robot",
            "message": "清洁机器人已暂停",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # dock
        return {
            "status": "success",
            "action": "dock_cleaning_robot",
            "message": "清洁机器人已返回充电座",
            "timestamp": "2025-12-08T10:00:00Z",
        }

@mcp.tool
def control_wave_machine(action: str = "start", duration_minutes: int = 30, mode: str = "热身") -> dict:
    """
    控制泳池冲浪器。

    Args:
        action: "start" 启动冲浪器, "stop" 停止冲浪器, "pause" 暂停冲浪
        duration_minutes: 冲浪持续时间（分钟）, 启动时有效
        mode: "热身" 热身, "舒缓" 舒缓, "挑战" 挑战

    Returns:
        dict: 执行结果
    """
    valid_actions = {"start", "stop", "pause"}
    valid_modes = {"热身", "舒缓", "挑战"}
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    if mode not in valid_modes:
        return {"status": "error", "message": f"无效的冲浪模式: {mode}"}
    if action == "start":
        if not (5 <= duration_minutes <= 90):
            return {"status": "error", "message": "冲浪时长需在5-90分钟之间"}
        return {
            "status": "success",
            "action": "start_wave_machine",
            "duration_minutes": duration_minutes,
            "mode": mode,
            "message": f"冲浪器已启动，模式为{mode}，预计运行{duration_minutes}分钟。",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    elif action == "pause":
        return {
            "status": "success",
            "action": "pause_wave_machine",
            "message": "冲浪器已暂停。",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # stop
        return {
            "status": "success",
            "action": "stop_wave_machine",
            "message": "冲浪器已停止。",
            "timestamp": "2025-12-08T10:00:00Z",
        }


# 场景二涉及工具
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
    """土壤湿度获取接口。"""
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
    """割草机控制接口。"""
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