import importlib
from typing import Dict, Any, Optional

handler_to_class = {
    "text_in_text_out": "src.handler_layer.text_in_text_out_handler.Handler",
    "default": "src.handler_layer.handler.Handler",
}

def load_class(class_type):
    class_type = handler_to_class.get(class_type)
    if not class_type:
        raise ValueError(f"Unsupported handler type: {class_type}") 
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


