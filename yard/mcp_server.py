
from fastmcp import FastMCP
from datetime import datetime
import random
from garden_system.garden_system import garden_system, MowerEvent, IrrigationEvent, WaveMachineEvent, CleaningRobotEvent, HeatPumpEvent, WaterPumpEvent

mcp = FastMCP("My MCP Server")



# 场景一涉及工具
@mcp.tool
def get_weather_forecast() -> dict:
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
def get_solar_system_energy() -> dict:
    return {
        "today_energy_generated_kwh": 4.4,
        "status": "ok",
        "timestamp": datetime.now().isoformat(), 
    }

@mcp.tool
def get_pool_status() -> dict:
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
def get_grass_status(sensor_id: str = "grass-001") -> dict:
    """
    草坪状态获取接口。

    Args:
        sensor_id (str): 草坪状态传感器ID，默认为"grass-001"。

    Returns:
        dict: 包含以下字段——
            - sensor_id (str): 传感器编号
            - height_cm (int): 草坪高度（厘米，0-15）
            - moisture_percent (float): 土壤湿度百分比
            - status (str): 状态说明，"ok"为正常
            - timestamp (str): ISO8601格式的时间戳
    """
    return {
        "sensor_id": sensor_id,
        "height_cm": 10, #random.randint(0, 15),
        "moisture_percent": 28.0,
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }

# 设备日志和管理规则

@mcp.tool
def get_running_events() -> dict:
    """
    返回正在运行的设备事件。
    """
    return {
        "running_events": garden_system.get_active_events(),
    }

@mcp.tool
def get_event_log() -> dict:
    """
    返回庭院事件日志。
    """
    return {
        "event_log": garden_system.get_event_log(),
    }

@mcp.tool
def get_swimming_preference() -> dict:


    swimming_preference_markdown = """
    ### 游泳时用户偏好

- **理想水温**：28°C
- 游泳时打开冲浪器，冲浪器模式为：热身，挑战，舒缓。冲浪器模式偏好为：热身5分钟，挑战20分钟，舒缓10分钟。
"""
    return {
        "swimming_preference_markdown": swimming_preference_markdown,
    }

 

# 设备控制

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
        heat_pump_event = HeatPumpEvent(event_data={
            "target_temperature_celsius": target_temperature_celsius,
            "action": "start_heat_pump"
        })
        garden_system.add_event(heat_pump_event.name, heat_pump_event.event_data)
        return {
            "status": "success",
            "action": "start_heat_pump",
            "target_temperature_celsius": target_temperature_celsius,
            "message": f"热泵已启动，目标温度设为 {target_temperature_celsius}°C",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # pause
        garden_system.remove_event(HeatPumpEvent().name)
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
        water_pump_event = WaterPumpEvent(event_data={
            "target_temperature_celsius": target_temperature_celsius,
            "flow_rate_l_min": flow_rate_l_min,
            "action": "start_water_pump"
        })
        garden_system.add_event(water_pump_event.name, water_pump_event.event_data)
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
        garden_system.remove_event(WaterPumpEvent().name)
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
        cleaning_robot_event = CleaningRobotEvent(event_data={
            "mode": mode,
            "duration_minutes": duration_minutes,
            "action": "start_cleaning_robot"
        })
        garden_system.add_event(cleaning_robot_event.name, cleaning_robot_event.event_data)
        return {
            "status": "success",
            "action": "start_cleaning_robot",
            "mode": mode,
            "duration_minutes": duration_minutes,
            "message": f"清洁机器人已启动，模式为{mode}，预计清洁{duration_minutes}分钟",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    elif action == "pause":
        garden_system.remove_event(CleaningRobotEvent().name)
        return {
            "status": "success",
            "action": "pause_cleaning_robot",
            "message": "清洁机器人已暂停",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # dock
        garden_system.remove_event(CleaningRobotEvent().name)
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
        wave_machine_event = WaveMachineEvent(event_data={
            "duration_minutes": duration_minutes,
            "mode": mode,
            "action": "start_wave_machine"
        })
        garden_system.add_event(wave_machine_event.name, wave_machine_event.event_data)
        return {
            "status": "success",
            "action": "start_wave_machine",
            "duration_minutes": duration_minutes,
            "mode": mode,
            "message": f"冲浪器已启动，模式为{mode}，预计运行{duration_minutes}分钟。",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    elif action == "pause":
        garden_system.remove_event(WaveMachineEvent().name)
        return {
            "status": "success",
            "action": "pause_wave_machine",
            "message": "冲浪器已暂停。",
            "timestamp": "2025-12-08T10:00:00Z",
        }
    else:  # stop
        garden_system.remove_event(WaveMachineEvent().name)
        return {
            "status": "success",
            "action": "stop_wave_machine",
            "message": "冲浪器已停止。",
            "timestamp": "2025-12-08T10:00:00Z",
        }

@mcp.tool
def control_mower(action: str, area: str = "front-yard", mode: str = "auto") -> dict:
    """
    控制割草机启动、停止或返回充电座。

    Args:
        action: "start" 启动割草, "stop" 停止割草, "dock" 返回充电座
        area: 割草区域，可选值: "front-yard" 前院, "back-yard" 后院, "all" 全部区域
        mode: 割草模式，可选值: "auto" 自动模式, "manual" 手动模式, "edge" 仅边缘修剪

    Returns:
        dict: 执行结果详情
    """
    valid_actions = {"start", "stop", "dock"}
    valid_areas = {"front-yard", "back-yard", "all"}
    valid_modes = {"auto", "manual", "edge"}
    
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    if area not in valid_areas:
        return {"status": "error", "message": f"无效的区域: {area}"}
    if mode not in valid_modes:
        return {"status": "error", "message": f"无效的割草模式: {mode}"}
    
    if action == "start":
        mower_event = MowerEvent(event_data={
            "area": area,
            "mode": mode,
            "action": "start_mower"
        })
        garden_system.add_event(mower_event.name, mower_event.event_data)
        return {
            "status": "success",
            "action": "start_mower",
            "area": area,
            "mode": mode,
            "message": f"割草机已启动，区域：{area}，模式：{mode}",
            "started_at": datetime.now().isoformat(),
        }
    elif action == "stop":
        garden_system.remove_event(MowerEvent().name)
        return {
            "status": "success",
            "action": "stop_mower",
            "area": area,
            "message": f"割草机已停止",
            "stopped_at": datetime.now().isoformat(),
        }
    else:  # dock
        garden_system.remove_event(MowerEvent().name)
        return {
            "status": "success",
            "action": "dock_mower",
            "message": "割草机已返回充电座",
            "docked_at": datetime.now().isoformat(),
        }

@mcp.tool
def control_irrigation(action: str, area: str = "front-yard", duration_minutes: int = 30, scheduled_time: str = None) -> dict:
    """
    控制灌溉系统启动、停止或设置定时灌溉。

    Args:
        action: "start" 启动灌溉, "stop" 停止灌溉, "schedule" 设置定时灌溉
        area: 灌溉区域，可选值: "front-yard" 前院, "back-yard" 后院, "all" 全部区域
        duration_minutes: 灌溉持续时间（分钟），启动或定时时有效，范围5-180分钟
        scheduled_time: 定时启动时间（ISO 8601格式，如"2025-12-08T20:00:00"），仅在action为"schedule"时需要

    Returns:
        dict: 执行结果详情
    """
    valid_actions = {"start", "stop", "schedule"}
    valid_areas = {"front-yard", "back-yard", "all"}
    
    if action not in valid_actions:
        return {"status": "error", "message": f"无效的操作: {action}"}
    if area not in valid_areas:
        return {"status": "error", "message": f"无效的区域: {area}"}
    if not (5 <= duration_minutes <= 180):
        return {"status": "error", "message": "灌溉时长需在5-180分钟之间"}
    
    if action == "start":
        irrigation_event = IrrigationEvent(event_data={
            "area": area,
            "duration_minutes": duration_minutes,
            "action": "start_irrigation"
        })
        garden_system.add_event(irrigation_event.name, irrigation_event.event_data)
        return {
            "status": "success",
            "action": "start_irrigation",
            "area": area,
            "duration_minutes": duration_minutes,
            "message": f"灌溉系统已启动，区域：{area}，预计运行{duration_minutes}分钟",
            "started_at": datetime.now().isoformat(),
        }
    elif action == "stop":
        garden_system.remove_event(IrrigationEvent().name)
        return {
            "status": "success",
            "action": "stop_irrigation",
            "area": area,
            "message": f"灌溉系统已停止",
            "stopped_at": datetime.now().isoformat(),
        }
    else:  # schedule
        if scheduled_time is None:
            return {"status": "error", "message": "设置定时灌溉时必须提供scheduled_time参数"}
        return {
            "status": "success",
            "action": "schedule_irrigation",
            "area": area,
            "duration_minutes": duration_minutes,
            "scheduled_time": scheduled_time,
            "message": f"定时灌溉已设置，区域：{area}，将在{scheduled_time}启动，预计运行{duration_minutes}分钟",
            "scheduled_at": datetime.now().isoformat(),
        }





if __name__ == "__main__":
    mcp.run(transport="http", port=8000)