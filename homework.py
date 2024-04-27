import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import RequestException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('practicum_token')
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')
RETRY_PERIOD = 10 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    filename='homework.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG)


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = [PRACTICUM_TOKEN,
              TELEGRAM_TOKEN,
              TELEGRAM_CHAT_ID
              ]
    return all(token is not None for token in tokens)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    logging.debug('Отправка сообщения в Telegram...')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Успешная отправка сообщения')
    except telegram.error.TelegramError:
        logging.error('Сбой при отправке сообщения в Telegram')


def get_api_answer(timestamp):
    """Совершение запроса к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    logging.debug(f'Попытка совершения запроса к {ENDPOINT}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException:
        message = f'Эндпоинт {ENDPOINT} недоступен'
        raise RequestException(message)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    message = f'Получен статус:{response.status_code}'
    raise requests.RequestException(message)


def check_response(response):
    """Проверка ответа API на соответствие."""
    if not isinstance(response, dict):
        raise TypeError('Получен неверный формат данных в ответе API')
    if 'homeworks' not in response:
        raise KeyError('В полученном ответе отсутсвует "homeworks"')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Получен неверный формат данных в ответе API')
    if 'current_date' not in response:
        raise KeyError('В полученном ответе отсутсвует "current_date"')
    return response['homeworks']


def parse_status(homework):
    """Извлечение статуса из домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В полученном ответе отсутсвует "homework_name"')
    if 'status' not in homework:
        raise KeyError('В полученном ответе отсутсвует "status"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Неожиданный статус домашней',
                       'работы обнаружен в ответе API')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    last_mess = ''
    if not check_tokens():
        message = 'Отсутсвует одна или несколько переменных окружения'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            timedelta = timestamp - RETRY_PERIOD
            response = get_api_answer(timedelta)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != last_mess:
                    send_message(bot, message)
                    last_mess = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != last_mess:
                send_message(bot, message)
                last_mess = message
        finally:
            timestamp += RETRY_PERIOD
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
