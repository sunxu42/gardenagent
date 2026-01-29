import os
import sys
sys.path.append("/home/diska/ongoing/gardenAgent/")
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
        if instruction == "TaskCompleted":
            break
        print(instruction)
        res = ""
        async for chunk in yard_manager.achat(instruction):
            if "content" in chunk:
                content = chunk.get("content", "")
                res += content
            elif "updates" in chunk:
               print(chunk)
        print(res)
        break

if __name__ == "__main__":
    asyncio.run(main())
