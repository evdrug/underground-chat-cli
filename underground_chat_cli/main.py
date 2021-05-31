import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv('CHAT_HOST')
PORT = os.getenv('CHAT_PORT')

async def tcp_echo_client():
    reader, writer = await asyncio.open_connection(
        HOST, PORT )
    while True:
        data = await reader.readline()
        print(data.decode(), end='')


if __name__ == "__main__":
    asyncio.run(tcp_echo_client())