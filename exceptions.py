class BotExceptionSendToTelegram(Exception):
    """Исключения для отправки в телеграм."""

    pass


class MinorException(Exception):
    """Исключения не для отправки в телеграм."""

    pass
