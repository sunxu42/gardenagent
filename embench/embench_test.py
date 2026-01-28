import asyncio
from embench import EmbenchClient
from yard.yard_manage import YardManager
client = EmbenchClient()


async def main():
    yard_manager = await YardManager.create()
    # for tool in yard_manager.tools:
    #     print(tool)

    while True:
        instruction = client.instruction()["instruction"]
        print(instruction)
        res = ""
        async for chunk in yard_manager.achat(instruction):
            content = chunk.get("content", "")
            res += content
        print(res)
        break

if __name__ == "__main__":
    asyncio.run(main())
