import argparse
import asyncio
import datetime
import os
import json
import aiofiles
from dotenv import load_dotenv


async def register(reader: asyncio.StreamReader , writer: asyncio.StreamWriter) -> dict:
    while True:
        writer.write('\n'.encode())
        await reader.readline()
        writer.write('John\n'.encode())
        register_message_raw = await reader.readline()
        register_message = register_message_raw.decode().strip()
        await reader.readline()
        return json.loads(register_message)

async def autorization(reader: asyncio.StreamReader , writer: asyncio.StreamWriter, token:str) -> None:
    writer.write(f'{token}\n'.encode())
    await reader.readline()


def create_message(writer: asyncio.StreamWriter) -> None:
    def message(message:str = '\n\n'):
        writer.write(f'{message}\n\n'.encode())
    return message

async def tcp_echo_client(host: str, port: int, token:str = None, message:str = '') -> None:
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError as e:
        print(f'Error connection host {host}:{port}')
        return

    message_connect_raw = await reader.readline()
    message_connect = message_connect_raw.decode().strip()
    if 'Enter your personal hash or leave it empty to create new account' in message_connect:
        if not token:
            result = await register(reader, writer)
            print('!!!!', result)
        else:
            await autorization(reader, writer, token)
    push_message = create_message(writer=writer)
    push_message(message)



if __name__ == "__main__":
    load_dotenv()
    host = os.getenv('CHAT_HOST')
    port = os.getenv('CHAT_PORT_WRITE')
    token = os.getenv('CHAT_TOKEN')


    parser = argparse.ArgumentParser(description='Send message chat.')

    parser.add_argument('message', type=str, nargs='+',
                        help='send message')

    args = parser.parse_args()
    print(args)

    asyncio.run(tcp_echo_client(host, port, token, ' '.join(args.message)))
