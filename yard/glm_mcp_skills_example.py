#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# 尝试导入 MCP 适配器（可选）
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

# 从 configs.py 导入 GLM 配置
# 注意：这里直接使用配置值，实际使用时可以从环境变量或配置文件读取
GLM_API_KEY = os.getenv('GLM_OPENAI_API_KEY', '83fa704db4954104afec82926847f913.lyzvmMOoFvyy4VRE')
GLM_BASE_URL = os.getenv('GLM_OPENAI_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')

# MCP 服务器配置
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

console = Console()


class AgentDisplay:
    """管理智能体对话与工具调用的展示效果，并配合 Live 显示转圈状态。"""

    def __init__(self):
        self.printed_count = 0
        self.current_status = "思考中..."
        self.spinner = Spinner("dots", text=self.current_status)

    def update_status(self, status: str):
        self.current_status = status
        self.spinner = Spinner("dots", text=status)

    def print_message(self, msg, show_user: bool = True):
        """根据消息类型，以较友好的方式打印到终端。"""
        # 用户消息
        if isinstance(msg, HumanMessage):
            if not show_user:
                return
            console.print(
                Panel(
                    str(msg.content),
                    title="[bold blue]你[/bold blue]",
                    border_style="blue",
                )
            )
            return

        # 智能体回复
        if isinstance(msg, AIMessage):
            content = msg.content
            # 兼容 content 为 list 的情况
            if isinstance(content, list):
                text_parts = [
                    p.get("text", "")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = "\n".join(text_parts)

            if content and isinstance(content, str) and content.strip():
                console.print(
                    Panel(
                        Markdown(content),
                        title="[bold green]Agent[/bold green]",
                        border_style="green",
                    )
                )

            # 显示工具调用信息（沿用原有逻辑）
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})

                    # 特殊处理 write_todos 工具，显示 Todo 列表
                    if tool_name == "write_todos" and "todos" in tool_args:
                        todos = tool_args["todos"]
                        console.print(
                            "  [dim]>> 调用工具:[/dim] [bold cyan]write_todos[/bold cyan]"
                        )
                        if isinstance(todos, list) and len(todos) > 0:
                            console.print("  [dim]Todo 列表:[/dim]")
                            for i, todo in enumerate(todos, 1):
                                status = todo.get("status", "pending")
                                content = todo.get("content", "")

                                if status == "completed":
                                    icon = "[green]✓[/green]"
                                elif status == "in_progress":
                                    icon = "[yellow]•[/yellow]"
                                else:
                                    icon = "[dim]○[/dim]"

                                console.print(f"    {icon} [{status}] {content}")
                        else:
                            console.print(
                                "  [dim]>> 调用工具:[/dim] [bold cyan]write_todos[/bold cyan] (空列表)"
                            )
                    else:
                        console.print(
                            f"  [dim]>> 调用工具:[/dim] [bold cyan]{tool_name}[/bold cyan]"
                        )

                    # 根据工具调用更新状态
                    self.update_status(f"调用工具: {tool_name}")


def create_glm_model():

    model = ChatOpenAI(
        model="glm-4.7",  
        api_key=GLM_API_KEY,
        base_url=GLM_BASE_URL,
        temperature=0.7,
        max_tokens=20000,
    )
    return model


async def create_mcp_tools():
    """从 MCP 服务器获取工具"""
    if not MCP_AVAILABLE:
        console.print("[yellow]⚠[/yellow] langchain-mcp-adapters 未安装，跳过 MCP 工具")
        console.print("[dim]安装命令: pip install langchain-mcp-adapters[/dim]")
        return []
    
    try:
        # 创建 MCP 客户端
        # 对于 HTTP 传输的 MCP 服务器，需要根据实际 API 格式配置
        # 这里提供一个通用的配置方式
        mcp_client = MultiServerMCPClient(
            {
                "weather": {
                    "url": MCP_SERVER_URL,
                    "transport": "http",
                }
            }
        )
        
        # 获取工具
        mcp_tools = await mcp_client.get_tools()
        console.print(f"[green]✓[/green] 成功从 MCP 服务器获取 {len(mcp_tools)} 个工具")
        
        # 显示工具名称
        if mcp_tools:
            tool_names = [getattr(tool, 'name', str(tool)) for tool in mcp_tools[:5]]
            console.print(f"[dim]工具示例: {', '.join(tool_names)}[/dim]")
            if len(mcp_tools) > 5:
                console.print(f"[dim]... 还有 {len(mcp_tools) - 5} 个工具[/dim]")
        
        return mcp_tools
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] MCP 服务器连接失败: {e}")
        console.print(f"[dim]服务器地址: {MCP_SERVER_URL}[/dim]")
        console.print("[dim]继续运行，但不使用 MCP 工具[/dim]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return []


def create_skills_directory():
    """创建示例 skills 目录结构"""
    example_dir = Path(__file__).parent
    skills_dir = example_dir / "skills"
    skills_dir.mkdir(exist_ok=True)
    
    # 创建一个简单的 blog-post skill
    blog_skill_dir = skills_dir / "blog-post"
    blog_skill_dir.mkdir(exist_ok=True)
    
    skill_file = blog_skill_dir / "SKILL.md"
    
    return str(skills_dir)


async def create_agent_with_mcp_and_skills():
    """创建带有 MCP 工具和 Skills 的智能体"""
    # 1. 创建 GLM 模型
    console.print("[cyan]配置 GLM 模型...[/cyan]")
    model = create_glm_model()
    console.print(f"[green]✓[/green] GLM 模型已配置 (Base URL: {GLM_BASE_URL})")
    
    # 2. 获取 MCP 工具
    console.print(f"[cyan]连接 MCP 服务器 ({MCP_SERVER_URL})...[/cyan]")
    mcp_tools = await create_mcp_tools()
    
    # # 3. 创建 skills 目录
    console.print("[cyan]设置 Skills...[/cyan]")
    skills_dir = create_skills_directory()
    console.print(f"[green]✓[/green] Skills 目录: {skills_dir}")
    
    # 4. 创建工作目录
    work_dir = Path(__file__).parent / "workspace"
    work_dir.mkdir(exist_ok=True)
    
    # 5. 创建 checkpointer 用于保持对话历史
    checkpointer = MemorySaver()
    
    # 6. 创建智能体
    console.print("[cyan]创建 Deep Agent...[/cyan]")
    agent = create_deep_agent(
        model=model,
        tools=mcp_tools,  # MCP 工具
        skills=[skills_dir],  # Skills 目录
        backend=FilesystemBackend(root_dir=work_dir),
        checkpointer=checkpointer,  # 用于保持对话历史
        system_prompt="""你的身份是用户的管家，名字叫小菲。
<requirement>
判断用户需求和技能是否相关，如果相关，总是优先查询技能再来执行任务。
</requirement>
<examples>
    <example>
    user: 庭院管家，介绍一下我们的智慧庭院
    assistant: 欢迎参观iGarden智慧庭院！我是您的智能管家。在这里，您看到的不仅仅是高端设备，更是一个会思考、能预见、且拥有协调能力的智慧生态系统。iGarden的智慧体现在：我们让所有设备不再孤立工作，而是协同合作，为您打造一个完全自动化、高度节能、且完美适配您生活节奏的理想户外空间。
    </example>
</examples>""",
    )
    console.print("[green]✓[/green] Deep Agent 创建成功！\n")
    
    return agent, work_dir


async def run_agent_single_turn(agent, user_input: str, thread_id: str, show_user_input: bool = True):
    """运行智能体单轮对话并使用 Live+Spinner 显示流式结果。
    
    Args:
        agent: 智能体实例
        user_input: 用户输入
        thread_id: 对话线程 ID（用于保持对话历史）
        show_user_input: 是否单独显示用户输入（避免重复展示）
    """
    display = AgentDisplay()
    printed_count = 0

    # 如果需要，先直接展示用户输入（与 AgentDisplay 中的用户展示解耦）
    if show_user_input:
        console.print(
            Panel(
                user_input,
                title="[bold blue]你[/bold blue]",
                border_style="blue",
            )
        )

    # 使用 Live 显示 spinner，在等待模型响应和工具调用时展示动态效果
    with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
        async for chunk in agent.astream(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="values",
        ):
            if "messages" in chunk:
                messages = chunk["messages"]
                if len(messages) > printed_count:
                    # 暂停 spinner，打印新消息
                    live.stop()
                    for msg in messages[printed_count:]:
                        # 如果用户输入已经单独展示过，就不再重复展示 HumanMessage
                        if isinstance(msg, HumanMessage) and show_user_input:
                            continue
                        display.print_message(msg, show_user=not show_user_input)
                    printed_count = len(messages)
                    # 重新启动 spinner，并使用最新状态
                    live.start()
                    live.update(display.spinner)


async def run_multi_turn_conversation(agent, work_dir: Path):
    """运行多轮对话"""
    thread_id = "glm-mcp-demo"
    
    console.print(Panel(
        f"[bold cyan]工作目录:[/bold cyan] {work_dir}\n"
        f"[bold cyan]对话 ID:[/bold cyan] {thread_id}\n"
        f"[dim]输入 'exit' 或 'quit' 退出对话[/dim]",
        title="多轮对话模式",
        border_style="blue"
    ))
    console.print()
    
    # 如果有命令行参数，作为第一轮对话
    if len(sys.argv) > 1:
        first_input = " ".join(sys.argv[1:])
        console.print(f"[dim]执行初始任务: {first_input}[/dim]\n")
        await run_agent_single_turn(agent, first_input, thread_id, show_user_input=False)
        console.print()
    
    # 进入交互循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n[bold cyan]你:[/bold cyan] ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                console.print("\n[yellow]退出对话[/yellow]")
                break
            
            if not user_input:
                console.print("[yellow]请输入内容[/yellow]")
                continue
            
            # 运行智能体
            console.print()  # 空行分隔
            await run_agent_single_turn(agent, user_input, thread_id)
            console.print()  # 空行分隔
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]已中断，输入 'exit' 退出[/yellow]")
        except EOFError:
            console.print("\n\n[yellow]退出对话[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]错误:[/red] {e}")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


async def main():
    """主函数"""
    try:
        # 创建智能体
        agent, work_dir = await create_agent_with_mcp_and_skills()
        agent.get_graph().draw_png("graph.png")
        # 运行多轮对话
        await run_multi_turn_conversation(agent, work_dir)
        
        console.print()
        console.print("[bold green]✓ 对话结束[/bold green]")
        console.print(f"[dim]生成的文件位于: {work_dir}[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]已中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]错误:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
