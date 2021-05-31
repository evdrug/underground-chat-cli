import argparse
import asyncio
import datetime
import os

import aiofiles
from dotenv import load_dotenv


async def main(host: str, port: int, file_history: str) -> None:
    try:
        reader, _ = await asyncio.open_connection(host, port)
    except ConnectionRefusedError as e:
        print(f'Error connection host {host}:{port}')
        return

    async with aiofiles.open(file_history, mode='a') as f:
        while True:
            data = await reader.readline()
            chat_message = data.decode().strip()
            date_today = datetime.datetime.today().strftime("%d.%m.%y %H:%M")
            time_message = f'[{date_today}] {chat_message}'
            print(time_message)
            await f.write(f'{time_message}\n')
            await f.flush()

if __name__ == "__main__":
    load_dotenv()
    host = os.getenv('CHAT_HOST')
    port = os.getenv('CHAT_PORT_READ')
    file_history = os.getenv('FILE_HISTORY')

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', dest='host', type=str, default=host,
                        help='connection server host')

    parser.add_argument('--port', dest='port', type=int, default=port,
                        help='connection server port')

    parser.add_argument('--history', dest='history', type=str, default=file_history,
                        help='save history chat to file')

    args = parser.parse_args()

    asyncio.run(main(args.host, args.port, file_history))
