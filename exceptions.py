class RequestException(Exception):
    """Ошибка подключения к эндпоинту."""

    def __init__(self, msg=None):
        """Получение сообщения ошибки."""
        self.message = msg

    def __str__(self):
        """ОТправка сообщения об ошибке."""
        return self.message
