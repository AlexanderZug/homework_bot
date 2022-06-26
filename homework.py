import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

from exceptions import BotExceptionSendToTelegram, MinorException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def send_message(bot: Bot, message: str):
    """Отправка сообщения в телеграм."""
    logging.info('Отправка сообщения началась.')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('Сообщение отправлено.')
    except TelegramError:
        raise MinorException('Не смог отправить сообщение.')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос к API Яндекса."""
    params = {'from_date': current_timestamp}
    logging.info(f'Начать запрос: {ENDPOINT}, {params}, {HEADERS}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        raise BotExceptionSendToTelegram(error)
    if response.status_code != HTTPStatus.OK:
        raise BotExceptionSendToTelegram(
            f'Bad requests {response.status_code}\n'
            f'Детали ошибка: {params}, {HEADERS}')
    return response.json()


def check_response(response: dict) -> list:
    """Возврат работ и проверка на корректность данных."""
    if not (isinstance(response, dict)
            and (isinstance(response.get('current_date'), int))
            and isinstance(response.get('homeworks'), list)):
        raise BotExceptionSendToTelegram('Некорректный тип данных')
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Проверка статуса работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not (homework_name or homework_status):
        raise BotExceptionSendToTelegram(
            'Отсутствует необходимое кол-во ключей')
    if homework_status not in HOMEWORK_VERDICTS:
        raise BotExceptionSendToTelegram(
            f'Неизвестный статус: {homework_status} ')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка переменных среды."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует необходимое кол-во'
                         'переменных окружения')
        sys.exit('Нет переменных окружения')
    while True:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                send_message(bot, parse_status(homeworks[0]))
            logging.info('Нет новых новостей')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info('Работа бота остановлена')
