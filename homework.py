import logging
import os
import time
import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus
load_dotenv()

PRACTICUM_TOKEN = os.getenv('practicum_token')
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')
RETRY_PERIOD = 10 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
LAST_MESS = ''
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
    if not all(token is not None for token in tokens):
        message = 'Отсутсвует одна или несколько переменных окружения'
        logging.critical(message)
        raise


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    global LAST_MESS
    if LAST_MESS != message:
        LAST_MESS = message
        try:
            bot.send_message(TELEGRAM_CHAT_ID, message)
            logging.debug('Успешная отправка сообщения')
        except telegram.error.TelegramError:
            logging.error('Cбой при отправке сообщения в Telegram')
    else:
        logging.debug('Отсутсвует новый статус проверки')


def get_api_answer(timestamp):
    """Совершение запроса к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        elif response.status_code != HTTPStatus.NOT_FOUND:
            message = f'Эндпоинт {ENDPOINT} недоступен'
            logging.error(message)
            send_message(bot, message)
            return 'Эндпоинт недоступен'
    except Exception:
        message = f'Эндпоинт {ENDPOINT} недоступен'
        logging.error(message)
        send_message(bot, message)
        return 'Эндпоинт недоступен'


def check_response(response):
    """Проверка ответа API на соответствие."""
    if response == 'Эндпоинт недоступен':
        return None
    elif not isinstance(response, dict):
        raise TypeError('Получен неверный формат данных в ответе API')
    elif not isinstance(response.get('homeworks'), list):
        raise TypeError('Получен неверный формат данных в ответе API')
    try:
        homework = response['homeworks']
        if homework != []:
            return homework[0]
        else:
            return None
    except KeyError:
        message = 'Отсутствуют ожидаемые ключи в ответе API'
        logging.error(message)
        send_message(bot, message)


def parse_status(homework):
    """Извлечение статуса из конкретной домашней работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        message = 'Домашняя работа не определена!'
        logging.error(message)
        send_message(bot, message)
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError:
        message = 'Неожиданный статус домашней работы обнаружен в ответе API'
        logging.error(message)
        send_message(bot, message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            timedelta = timestamp - RETRY_PERIOD
            response = get_api_answer(timedelta)
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            timestamp += RETRY_PERIOD
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
