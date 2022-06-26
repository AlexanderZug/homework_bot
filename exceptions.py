class BotExceptionSendToTelegram(Exception):
    """Исключения для отправки в телеграм."""

    pass


class MinorException(Exception):
    """Штатные исключения не для отправки в телеграм."""

    pass
