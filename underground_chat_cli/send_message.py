import argparse
import asyncio
import json
import os
from types import coroutine

from dotenv import load_dotenv
import logging

logger = logging.getLogger('send_message')


async def registration(send_data: coroutine, nickname: str) -> dict:
    await send_data('')
    result = await send_data(nickname)
    await send_data('')
    return json.loads(result)


async def autorization(send_data: coroutine, token: str) -> bool:
    result = await send_data(token)
    if result == 'null':
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        return False
    return True


def sender(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    async def message(write_data: str) -> str:
        logger.debug(f'writer:  {write_data}')
        writer.write(f'{write_data}\n'.encode())
        fetch_message_raw = await reader.readline()
        fetch_message = fetch_message_raw.decode().strip()
        logger.debug(f"reader: {fetch_message}")
        return fetch_message
    return message


def create_message(writer: asyncio.StreamWriter) -> None:
    def message(message: str = '\n\n') -> None:
        writer.write(f'{message}\n\n'.encode())
        logger.debug(f'send_message:  {message}')
    return message


async def main(host: str = '', port: int = None, token: str = None, message: str = '', username: str = None) -> None:
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError as e:
        print(f'Error connection host {host}:{port}')
        return None
    send_data = sender(reader, writer)
    await reader.readline()

    if username:
        result_registration_user = await registration(send_data, username)
        print('Registration new user -', result_registration_user)
        return None

    auth_result = await autorization(send_data, token)

    if not auth_result:
        return None
    
    push_message = create_message(writer=writer)
    push_message(message)



if __name__ == "__main__":
    load_dotenv()
    host = os.getenv('CHAT_HOST')
    port = os.getenv('CHAT_PORT_WRITE')
    token = os.getenv('CHAT_TOKEN')

    log_format = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=log_format)

    parser = argparse.ArgumentParser(description='Send message chat.')

    parser.add_argument('message', type=str, nargs='*', help='send message')
    parser.add_argument('-d', '--debug', dest='loglevel', action='store_const', default=logging.INFO,
                        const=logging.DEBUG, help='Enable debug')
    parser.add_argument('-r', '--registration',
                        dest='registration', help='Username for rigistration')

    args = parser.parse_args()
    logger.setLevel(args.loglevel)
    if not args.message and not args.registration:
        parser.error('the following arguments are required: message or optional arguments -r(--registration)')
    message = ' '.join(args.message)
    asyncio.run(main(host=host, port=port, token=token, message=message, username=args.registration))
