import asyncio
from yard.yard_manage import YardManager


async def main():
    res = ""
    yard_manager = await YardManager.create()
    # print graph
    graph = yard_manager.agent.get_graph(xray=True)
    graph.draw_mermaid_png(output_file_path="yard_manager.png")
    async for chunk in yard_manager.achat("帮我割草"):
        content = chunk.get("content", "")
        res += content
    print(res)


asyncio.run(main())