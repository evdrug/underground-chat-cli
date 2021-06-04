import argparse
import asyncio
import json
import logging
import os
import socket
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
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        return False
    return True


def read_write_message(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Callable:
    async def wrapper(write_data: str) -> str:
        logger.debug(f'writer:  {write_data}')
        writer.write(f'{write_data}\n'.encode())
        fetch_message_raw = await reader.readline()
        fetch_message = fetch_message_raw.decode().strip()
        logger.debug(f"reader: {fetch_message}")
        return fetch_message

    return wrapper


def submit_message(writer: asyncio.StreamWriter) -> Callable:
    def wrapper(text_message: str = '\n\n') -> None:
        writer.write(f'{text_message}\n\n'.encode())
        logger.debug(f'send_message:  {text_message}')

    return wrapper


async def main(host: str = '', port: int = None, token: str = None, message: str = '', username: str = None) -> None:
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except (ConnectionRefusedError, socket.gaierror) as e:
        print(f'Error connection host {host}:{port}')
        return
    except TimeoutError as e:
        print(f'Connection host {host}:{port} timeout')
        return

    send_data = read_write_message(reader, writer)
    await reader.readline()

    if username:
        result_registration_user = await registration(send_data, username)
        print('Registration new user -', result_registration_user)
        return None

    auth_result = await authorization(send_data, token)

    if not auth_result:
        return None

    push_message = submit_message(writer=writer)
    push_message(message)


if __name__ == "__main__":
    load_dotenv()
    chat_host = os.getenv('CHAT_HOST')
    chat_port = os.getenv('CHAT_PORT_WRITE')
    chat_token = os.getenv('CHAT_TOKEN')

    log_format = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=log_format)

    parser = argparse.ArgumentParser(description='Send message chat.')

    parser.add_argument('message', type=str, nargs='*', help='send message')
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
    try:
        asyncio.run(main(host=args.host, port=args.port,
                     token=args.token, message=message, username=args.username))
    except KeyboardInterrupt:
        pass