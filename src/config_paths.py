"""服务端配置路径（避免 src.settings 与 yard.configs 循环依赖）。"""

from yard.configs.paths import CONFIG_FILE

__all__ = ["CONFIG_FILE"]
