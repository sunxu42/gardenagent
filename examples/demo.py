import asyncio

from agent.manager import AgentManager


async def main():
    agent_manager = await AgentManager.create()

    graph = agent_manager.agent.get_graph(xray=True)
    graph.draw_mermaid_png(output_file_path="agent_manager.png")
    async for chunk in agent_manager.achat("帮我割草"):
        print(chunk)


if __name__ == "__main__":
    asyncio.run(main())
