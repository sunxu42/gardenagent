from enum import Enum


class LogModule(str, Enum):
    HANDLER = "HANDLER"
    ASR = "ASR"
    AGENT = "AGENT"
    TTS = "TTS"
    EMOTION = "EMOTION"
    TRANSPORT = "TRANSPORT"
    METRICS = "METRICS"
    MEMORY = "MEMORY"
    SYSTEM = "SYSTEM"


_SHORT: dict[LogModule, str] = {
    LogModule.HANDLER: "HND",
    LogModule.ASR: "ASR",
    LogModule.AGENT: "AGT",
    LogModule.TTS: "TTS",
    LogModule.EMOTION: "AFF",
    LogModule.TRANSPORT: "TRN",
    LogModule.METRICS: "MET",
    LogModule.MEMORY: "MEM",
    LogModule.SYSTEM: "SYS",
}

_COLORS: dict[LogModule, str] = {
    LogModule.HANDLER: "#22d3ee",
    LogModule.ASR: "#60a5fa",
    LogModule.AGENT: "#a78bfa",
    LogModule.TTS: "#fb923c",
    LogModule.EMOTION: "#f472b6",
    LogModule.TRANSPORT: "#94a3b8",
    LogModule.METRICS: "#34d399",
    LogModule.MEMORY: "#fbbf24",
    LogModule.SYSTEM: "#e2e8f0",
}


def module_short_name(module: LogModule) -> str:
    return _SHORT[module]


def module_color(module: LogModule) -> str:
    return _COLORS[module]
