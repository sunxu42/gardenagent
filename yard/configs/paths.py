"""项目根目录下配置文件路径常量。"""

from __future__ import annotations

import os

CWD = os.getcwd()
ENV_FILE = os.path.join(CWD, ".env")
CONFIG_FILE = os.path.join(CWD, ".config.yaml")
