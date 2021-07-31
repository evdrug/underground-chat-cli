import argparse
import asyncio
import json
import logging
import os
import socket
from contextlib import suppress
from functools import partial
from typing import Optional, Callable

from dotenv import load_dotenv

logger = logging.getLogger('send_message')


async def registration(send_data: Callable, nickname: str) -> dict:
    await send_data('')
    result = await send_data(nickname)
    await send_data('')
    return json.loads(result)


async def authorization(send_data: Callable, token_chat: Optional[str]) -> bool:
    result = await send_data(token_chat)
    if result == 'null':
        return False
    return True


async def read_write_message(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, write_data: str) -> str:
    logger.debug(f'writer:  {write_data}')
    writer.write(f'{write_data}\n'.encode())
    await writer.drain()
    message_raw = await reader.readline()
    message = message_raw.decode().strip()
    logger.debug(f"reader: {message}")
    return message


async def submit_message(writer: asyncio.StreamWriter, text_message: str = '\n\n') -> None:
    writer.write(f'{text_message}\n\n'.encode())
    await writer.drain()
    logger.debug(f'send_message:  {text_message}')


async def run_sender(host: str = '', port: int = None, token: str = None, message: str = '',
                     username: str = None) -> None:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 20)
    except (ConnectionRefusedError, socket.gaierror) as e:
        print(f'Error connection host {host}:{port}')
        return
    except asyncio.exceptions.TimeoutError as e:
        print(f'Connection host {host}:{port} timeout')
        return

    try:
        send_data = partial(read_write_message, reader, writer)
        await reader.readline()

        if username:
            new_registered_user = await registration(send_data, username)
            print('Registration new user -', new_registered_user)
            return None

        is_correct_token = await authorization(send_data, token)

        if not is_correct_token:
            print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
            return None

        push_message = partial(submit_message, writer)
        await push_message(message)
    finally:
        writer.close()
        await writer.wait_closed()


def main():
    load_dotenv()
    chat_host = os.getenv('CHAT_HOST')
    chat_port = os.getenv('CHAT_PORT_WRITE')
    chat_token = os.getenv('CHAT_TOKEN')

    log_format = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=log_format)

    parser = argparse.ArgumentParser(description='The sender of the message to the chat')

    parser.add_argument('message', type=str, nargs='*', help='text message')
    parser.add_argument('--host', dest='host', type=str, default=chat_host,
                        help='connection server host')

    parser.add_argument('--port', dest='port', type=int, default=chat_port,
                        help='connection server port')
    parser.add_argument('-t', '--token', dest='token', type=str, default=chat_token,
                        help='connection server port')
    parser.add_argument('-d', '--debug', dest='loglevel', action='store_const', default=logging.INFO,
                        const=logging.DEBUG, help='Enable debug')
    parser.add_argument('-r', '--registration',
                        dest='username', help='Username for rigistration')

    args = parser.parse_args()
    logger.setLevel(args.loglevel)
    if not args.message and not args.username:
        parser.error(
            'the following arguments are required: message or optional arguments -r(--registration)')

    message = ' '.join(args.message)
    with suppress(KeyboardInterrupt):
        asyncio.run(run_sender(host=args.host, port=args.port,
                               token=args.token, message=message, username=args.username))


if __name__ == "__main__":
    main()
