from pydantic import BaseModel


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file_level: str = "DEBUG"
    dir: str = "logs"
    file: str = "garden.jsonl"
    rotation: str = "1 day"
    retention: str = "7 days"
    console: bool = True
    websocket: bool = True
    file_enabled: bool = True
    ui_buffer_size: int = 500
