from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger

@dataclass
class MowerEvent:
    name: str = "mower_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()

@dataclass
class IrrigationEvent:
    name: str = "irrigation_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()

@dataclass
class WaveMachineEvent:
    name: str = "wave_machine_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()

@dataclass
class CleaningRobotEvent:
    name: str = "cleaning_robot_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()

@dataclass
class HeatPumpEvent:
    name: str = "heat_pump_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()

@dataclass
class WaterPumpEvent:
    name: str = "water_pump_running"
    event_data: dict = field(default_factory=dict)
    event_timestamp: datetime = datetime.now()


class GardenSystem:
    def __init__(self):
        self.active_events = []
        self.event_log = [] # 事件日志

    def add_event(self, event_name: str, event_data: dict):
        # 添加事件到活动事件列表
        
        self.active_events.append({
            "event_name": event_name,
            "event_data": event_data,
            "event_timestamp": datetime.now(),
        })
        logger.info(f"添加事件: {event_name}")

    def add_event_log(self, event_name: str, event_data: dict):
        self.event_log.append({
            "event_name": event_name,
            "event_data": event_data,
            "event_timestamp": datetime.now(),
        })
    def remove_expired_event(self):
        # 如果超过10分钟，则删除事件
        if len(self.active_events) > 0:
            for event in self.active_events:
                if event["event_timestamp"] < datetime.now() - timedelta(minutes=10):
                    self.active_events.remove(event)
                    self.add_event_log(event["event_name"], event["event_data"])
    
    def remove_event(self, event_name: str):
        for event in self.active_events:
            if event["event_name"] == event_name:
                self.active_events.remove(event)
                self.add_event_log(event["event_name"], event["event_data"])
                break

    def get_active_events(self) -> list:
        self.remove_expired_event()
        # Convert datetime objects to ISO format strings for JSON serialization
        return [
            {
                **event,
                "event_timestamp": event["event_timestamp"].isoformat() if isinstance(event["event_timestamp"], datetime) else event["event_timestamp"]
            }
            for event in self.active_events
        ]
    
    def get_event_log(self) -> list:
        return self.event_log





garden_system = GardenSystem()