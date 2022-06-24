import logging
import os
import sys

import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO,
    handlers=[handler],

)


def send_message(bot, message):
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    try:
        params = {'from_date': current_timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        return response.json()
    except requests.exceptions.RequestException:
        logging.error(f'{response.status_code}')



def check_response(response):
    return response['homeworks']


def parse_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logging.info('Es geht!')
        return True
    logging.critical('Achtung! Alles verloren!')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        return False

    while True:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            print(response)
            homeworks = check_response(response)
            send_message(bot, parse_status(homeworks[0]))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        # else:
        #     ...


if __name__ == '__main__':
    main()
    print('ok')
