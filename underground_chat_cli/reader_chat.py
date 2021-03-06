import argparse
import asyncio
import datetime
import os
import socket
from asyncio import StreamReader, StreamWriter
from contextlib import suppress

import aiofiles
from dotenv import load_dotenv


async def connect_chat(host: str = None, port: int = None, max_time_reconnect: int = 30) -> (
StreamReader, StreamWriter):
    count_refuse_connect = 0
    while True:
        await asyncio.sleep(count_refuse_connect)
        print(f'Connection host {host}:{port}')
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 5)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
            reader, writer = await asyncio.open_connection(sock=sock)
        except (ConnectionRefusedError, ConnectionError, socket.gaierror) as e:
            print(f'Error connection host {host}:{port}')
        except (socket.timeout, TimeoutError) as e:
            print(f'Error connection host {host}:{port} - Timeout Error')
        else:
            break

        if count_refuse_connect <= max_time_reconnect:
            count_refuse_connect += 1
        print(f'Connection attempt again after {count_refuse_connect} s')
    return reader, writer


async def write_history_to_file_and_stdout(file_history: str = None, reader: StreamReader = None) -> None:
    async with aiofiles.open(file_history, mode='a') as f:
        while True:
            data = await reader.readline()
            chat_message = data.decode().strip()
            date_today = datetime.datetime.today().strftime("%d.%m.%y %H:%M")
            message = f'[{date_today}] {chat_message}\n'
            print(message, end='')
            await f.writelines(message)
            await f.flush()


async def run_reading_chat(host: str = None, port: int = None, file_history: str = None,
                           max_time_reconnect: int = None) -> None:
    while True:
        reader, writer = await connect_chat(host, port, max_time_reconnect)
        try:
            await write_history_to_file_and_stdout(file_history, reader)
        except TimeoutError:
            print(f'Error connection host {host}:{port} - Timeout Error')
            writer.close()
            with suppress(TimeoutError):
                await writer.wait_closed()


def main():
    load_dotenv()
    chat_host = os.getenv('CHAT_HOST')
    chat_port = os.getenv('CHAT_PORT_READ')
    chat_file_history = os.getenv('FILE_HISTORY')
    max_time_reconnect = int(os.getenv('MAX_TIME_RECONNECT', 30))

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', dest='host', type=str, default=chat_host,
                        help='connection server host')

    parser.add_argument('--port', dest='port', type=int, default=chat_port,
                        help='connection server port')

    parser.add_argument('--history', dest='history', type=str, default=chat_file_history,
                        help='save history chat to file')

    args = parser.parse_args()

    with suppress(KeyboardInterrupt):
        asyncio.run(run_reading_chat(args.host, args.port, args.history, max_time_reconnect))


if __name__ == "__main__":
    main()
