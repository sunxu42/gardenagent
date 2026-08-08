"""Dynamic class loading for multimodal provider factories."""

from __future__ import annotations

import importlib
from typing import Any, Type


def load_class(class_path: str) -> Type[Any]:
    """Import and return a class from ``module.path.ClassName``."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
