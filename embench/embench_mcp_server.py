
from typing import Any, Dict, Optional
from fastmcp import FastMCP
from embench_http import EmbenchClient
import uvicorn

mcp = FastMCP("Embench MCP Server")

client = EmbenchClient()

tools = {
    'navigate': ['left drawer', 'middle drawer', 'right drawer', 'bottom drawer', 'fridge', 'chair', 'black table', 'brown table', 'TV stand', 'sink', 'right counter', 'left counter', 'sofa', 'fridge', 'left drawer', 'right drawer'], 
    'pick': ['ball', 'clamp', 'hammer', 'screwdriver', 'padlock', 'scissors', 'block', 'drill', 'spatula', 'knife', 'spoon', 'plate', 'sponge', 'cleanser', 'plum', 'pear', 'peach', 'apple', 'lemon', 'can', 'box', 'banana', 'strawberry', 'lego', 'rubriks cube', 'book', 'bowl', 'cup', 'mug', 'orange', 'lid', 'toy airplane', 'wrench'], 
    'place': ['chair', 'black table', 'brown table', 'TV stand', 'sink', 'right counter', 'left counter', 'sofa', 'fridge', 'left drawer', 'right drawer'], 
    'open': ['fridge', 'left drawer', 'middle drawer', 'right drawer', 'bottom drawer'], 
    'close': ['fridge', 'left drawer', 'middle drawer', 'right drawer', 'bottom drawer']}


@mcp.tool
def navigate(destination: str):
    """
    导航到指定位置。
    Use this tool for:
    - 移动机器人到某个场景/位置以便后续操作（pick/open/place 等）
    - 在执行任务前切换视角/位置
    
    Args:
        destination: 目标位置名称。Must be one of: ['left drawer', 'middle drawer', 'right drawer', 'bottom drawer', 'fridge', 'chair', 'black table', 'brown table', 'TV stand', 'sink', 'right counter', 'left counter', 'sofa', 'fridge', 'left drawer', 'right drawer']
    
    Returns:
        dict: 导航执行结果
    """
    return client.execute_tool("navigate", {"target": destination})

@mcp.tool
def pick(target: str):
    """
    抓取指定物体。
    Use this tool for:
    - 从环境中拿起某个物体以便后续操作
    - 在执行任务前获取物体
    
    Args:
        target: 要抓取的物体名称。Must be one of: ball, clamp, hammer, screwdriver, padlock, scissors, block, drill, spatula, knife, spoon, plate, sponge, cleanser, plum, pear, peach, apple, lemon, can, box, banana, strawberry, lego, rubriks cube, book, bowl, cup, mug, orange, lid, toy airplane, wrench
    
    Returns:
        dict: 抓取执行结果
    """
    return client.execute_tool("pick", {"target": target})

@mcp.tool
def place(destination: str):
    """
    将物体放置到指定位置。
    Use this tool for:
    - 将当前持有的物体放到某个位置
    - 完成物体移动任务
    
    Args:
        destination: 目标放置位置。Must be one of: chair, black table, brown table, TV stand, sink, right counter, left counter, sofa, fridge, left drawer, right drawer
    
    Returns:
        dict: 放置执行结果
    """
    return client.execute_tool("place", {"target": destination})

@mcp.tool
def open(target: str):
    """
    打开指定容器或抽屉。
    Use this tool for:
    - 打开抽屉、冰箱等容器以便访问内部物体
    - 在执行 pick 操作前打开容器
    
    Args:
        target: 要打开的容器名称。Must be one of: fridge, left drawer, middle drawer, right drawer, bottom drawer
    
    Returns:
        dict: 打开操作执行结果
    """
    return client.execute_tool("open", {"target": target})

@mcp.tool
def close(target: str):
    """
    关闭指定容器或抽屉。
    Use this tool for:
    - 关闭已打开的抽屉、冰箱等容器
    - 完成任务后恢复环境状态
    
    Args:
        target: 要关闭的容器名称。Must be one of: fridge, left drawer, middle drawer, right drawer, bottom drawer
    
    Returns:
        dict: 关闭操作执行结果
    """
    return client.execute_tool("close", {"target": target})

@mcp.tool
def get_observation():
    """
    获取机器人当前观测（摄像头画面）。
    Use this tool for:
    - 在采取动作前确认环境状态与物体位置
    - 在动作执行后验证结果（例如是否成功拿起/放置）
    
    Returns:
        str: 图片数据（data URL 格式）
    """
    observation = client.observation()
    return observation


if __name__ == "__main__":
    # 使用 uvicorn 手动启动 HTTP 服务，并将日志级别设置为 WARNING，避免打印 INFO 日志
    http_app = mcp.http_app()
    uvicorn.run(http_app, host="127.0.0.1", port=8001, log_level="warning")