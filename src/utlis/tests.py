import asyncio
from src.tools.dungeon_map import generate_dungeon_map
params = {'dungeon_size': 'Medium', 'level': 3, 'motif': 'Fire'}  # Replace with valid parameters

async def main():
    result = await generate_dungeon_map(params)
    print(result)

asyncio.run(main())