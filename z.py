from dataclasses import dataclass
from pydantic import BaseModel

class HandlerConfig(BaseModel):
    input_modality: list[str] = ["text", "audio"]
a = HandlerConfig()
b = HandlerConfig()
a.input_modality.append("image")
print(b.input_modality)  # 也会多出 "image"