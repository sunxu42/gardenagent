import secrets
import uuid
def generate_tool_call_id(use_uuid: bool = False) -> str:
    """
    生成工具调用 ID，格式：call_ + 24位十六进制字符串
    例如：call_5364c0b37e6344b4a2853ace
    
    Args:
        use_uuid: 如果为 True，使用 uuid.uuid4() 生成（更标准但需要转换）
                  如果为 False，使用 secrets.token_hex() 生成（更直接，推荐）
    
    推荐使用 secrets，因为：
    1. 直接生成所需格式，无需转换
    2. 加密安全（适合生产环境）
    3. 代码更简洁
    """
    if use_uuid:
        # 使用 UUID：标准格式，但需要转换
        # uuid4().hex 生成 32 位十六进制，取前 24 位
        hex_string = uuid.uuid4().hex[:24]
    else:
        # 使用 secrets：直接生成 24 位十六进制（推荐）
        # 生成 12 字节的随机十六进制字符串（24个字符）
        hex_string = secrets.token_hex(12)
    
    return f"call_{hex_string}"
