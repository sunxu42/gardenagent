"""
统一日志初始化模块
"""
import os
import sys
from loguru import logger
from typing import Optional, List


def setup_logger(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    enable_console: bool = True,
    disable_modules: Optional[List[str]] = None
):
    """
    统一日志初始化函数
    
    Args:
        log_file: 日志文件路径，如果为 None 则不输出到文件
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)，如果为 None 则从环境变量读取
        enable_console: 是否启用控制台输出
        disable_modules: 要禁用的模块名称列表，例如 ['src.agent_layer'] 会禁用整个 agent_layer 包
                        如果为 None，则从环境变量 LOG_DISABLE_MODULES 读取（逗号分隔）
    """
    # 从环境变量读取日志配置
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    rotation = os.getenv('LOG_ROTATION', '1 day')
    retention = os.getenv('LOG_RETENTION', '7 days')
    
    # 移除现有处理器
    logger.remove()
    
    # 禁用指定模块的日志
    if disable_modules is None:
        # 从环境变量读取
        disable_modules_str = os.getenv('LOG_DISABLE_MODULES', '')
        if disable_modules_str:
            disable_modules = [m.strip() for m in disable_modules_str.split(',') if m.strip()]
        else:
            disable_modules = []
    
    if disable_modules:
        for module in disable_modules:
            logger.disable(module)
    
    # 控制台格式（带颜色）
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件格式（不带颜色）
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}"
    )
    
    # 添加控制台输出
    if enable_console:
        logger.add(
            sys.stdout,
            level=log_level,
            format=console_format,
            colorize=True
        )
    
    # 添加文件输出
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format=file_format,
            rotation=rotation,
            retention=retention
        )

