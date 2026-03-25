# 定义事件类型，heartbeat输入事件,用户输入事件,agent输出事件

HEARTBEAT_INPUT_EVENT = "heartbeat"
USER_INPUT_EVENT = "user"
AGENT_OUTPUT_EVENT = "agent"


class InputEvent:
    def __init__(self, content: str, event_id: str, event_type: str):
        self.event_id = event_id
        self.content = content
        self.event_type = event_type



class OutputEvent:
    def __init__(self, data: dict, 
    trigger_by: str, 
    event_id: str, 
    phase: str,
    event_type: str="agent",
    ):
        self.event_id = event_id
        self.data = data
        self.event_type = event_type
        self.trigger_by = trigger_by
        self.phase = phase # start, end, middle
