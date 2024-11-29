import asyncio


async def func1():
    for i in range(15):
        print(i)
        await asyncio.sleep(1)


async def func2():
    for _ in range(15):
        print("func2")
        await asyncio.sleep(1)

async def main():
    await func1()
    await func2()

asyncio.run(main())
