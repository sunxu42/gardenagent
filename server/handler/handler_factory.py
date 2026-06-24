import importlib

from shared.config.server import UnifiedConfig
from server.transport.base import TransportBase

handler_to_class = {
    "text_in_text_out": "server.handler.text_in_text_out_handler.Handler",
    "default": "server.handler.default.Handler",
}

def load_class(
    handler_type: str,
    transport: TransportBase,
    client_id: str,
    server_config: UnifiedConfig,
):
    class_type = handler_to_class.get(handler_type)
    if not class_type:
        raise ValueError(f"Unsupported handler type: {class_type}")
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    handler_class = getattr(module, class_name)
    return handler_class(server_config, transport, client_id)


