import importlib
from src.config import load_config
from src.transport_layer.base import TransportBase

handler_to_class = {
    "text_in_text_out": "src.handler_layer.text_in_text_out_handler.Handler",
    "default": "src.handler_layer.handler.Handler",
}

def load_class(handler_type: str, transport: TransportBase, client_id: str):
    class_type = handler_to_class.get(handler_type)
    if not class_type:
        raise ValueError(f"Unsupported handler type: {class_type}") 
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    handler_class = getattr(module, class_name)
    return handler_class(load_config(), transport, client_id)


