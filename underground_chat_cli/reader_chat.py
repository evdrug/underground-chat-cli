import argparse
import asyncio
import datetime
import os
import socket
from asyncio import StreamReader, StreamWriter
from contextlib import suppress

import aiofiles
from dotenv import load_dotenv


async def connection_chat(host: str = None, port: int = None, ) -> (StreamReader, StreamWriter):
    count_refuse_connect = 0
    max_time_reconnect = int(os.getenv('MAX_TIME_RECONNECT', 30))
    while True:
        await asyncio.sleep(count_refuse_connect)
        try:
            sock = socket.create_connection((host, port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 5)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
            reader, writer = await asyncio.open_connection(sock=sock)
        except (ConnectionRefusedError, ConnectionError, socket.gaierror) as e:
            print(f'Error connection host {host}:{port}')
        except TimeoutError as e:
            print(f'Connection host {host}:{port} timeout')
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


async def run_reading_chat(host: str = None, port: int = None, file_history: str = None) -> None:
    try:
        while True:
            reader, writer = await connection_chat(host, port)
            with suppress(TimeoutError):
                await write_history_to_file_and_stdout(file_history, reader)
    finally:
        writer.close()
        await writer.wait_closed()


def main():
    load_dotenv()
    chat_host = os.getenv('CHAT_HOST')
    chat_port = os.getenv('CHAT_PORT_READ')
    chat_file_history = os.getenv('FILE_HISTORY')

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', dest='host', type=str, default=chat_host,
                        help='connection server host')

    parser.add_argument('--port', dest='port', type=int, default=chat_port,
                        help='connection server port')

    parser.add_argument('--history', dest='history', type=str, default=chat_file_history,
                        help='save history chat to file')

    args = parser.parse_args()

    with suppress(KeyboardInterrupt):
        asyncio.run(run_reading_chat(args.host, args.port, args.history))


if __name__ == "__main__":
    main()
