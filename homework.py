import logging
import os
import sys

import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import BotException

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

BOT = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('Abgesendet!')
    except BotException:
        logging.error('Nicht abgesendet!')
        return 'Nicht abgesendet!'


def get_api_answer(current_timestamp):
    """Запрос к API Яндекса."""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        logging.error(
            f'Шеф, все пропало {response.status_code}...')
        send_message(BOT, f'Шеф, все пропало {response.status_code}...')
        raise BotException('Bad, really bad requests')
    return response.json()


def check_response(response):
    """Возврат работ и проверка на корректность данных."""
    if not isinstance(response['homeworks'], list):
        logging.error('Где же мой лист?!')
        send_message(BOT, 'Прости, но лист я так и не нашел...')
        raise BotException('Keine Liste, keine Probleme')
    return response['homeworks']


def parse_status(homework):
    """Проверка статуса работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных среды."""
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
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                send_message(BOT, parse_status(homeworks[0]))
            logging.info('Es gibt keine Ausgaben')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(BOT, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
    print('ok')
