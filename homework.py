import dotenv
import logging
import os
import requests
import telegram
import time

dotenv.load_dotenv()


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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s')
)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляем сообщение через бота."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение в телеграм успешно отправлено')
        logger.info(f'Текст: {message}')
    except Exception:
        logger.error('Не получилось отправить сообщение в телеграм')


def get_api_answer(current_timestamp):
    """Запрос к серверу об изменениях статусов проверки домашних работ."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == 503:
        error_message = 'Сервер с данными недоступен. Ошибка 503.'
        logger.error(error_message)
        raise Exception(error_message)
    elif response.status_code != 200:
        error_message = ('Проблема с получением данных. '
                         + f'Код {response.status_code}.')
        logger.error(error_message)
        raise Exception(error_message)
    return response.json()


def check_response(response):
    """Проверяем корректность полученных данных."""
    homeworks = None
    try:
        homeworks = response['homeworks']
    except KeyError:
        error_message = 'Ключ homeworks в ответе сервера не обнаружен.'
        logger.error(error_message)
    if not isinstance(homeworks, list):
        error_message = 'Данные по статусу работ некорректны.'
        logger.error(error_message)
        raise TypeError
    return homeworks


def parse_status(homework):
    """Парсим статус проверки домашней работы."""
    homework_status = None
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        error_message = 'В данных сервера отсутствует необходимый ключ.'
        logger.error(error_message)
        raise KeyError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяемя наличие всех необходимых токенов для работы."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if not token:
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Не хватает переменных окружения')
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
            else:
                logger.debug('Новых статусов домашних работ не обнаружено')
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.error(error_message)
            send_message(bot, error_message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
