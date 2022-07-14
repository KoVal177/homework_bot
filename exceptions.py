class ServerError503(Exception):
    """Исключение для ответа сервера 503."""

    pass


class HttpCodeNot200(Exception):
    """Исключение для ответа сервера кроме нормального кода 200."""

    pass
