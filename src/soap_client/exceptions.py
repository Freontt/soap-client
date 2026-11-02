"""Файл хранит классы-исключения."""

class SoapError(ConnectionError):
    """Ошибка при обращении к SOAP-методу.

    Используется в исключениях связанных с ``SoapClientManager``.
    """

    def __init__(self, action: str, detail: str, params: dict | None = None) -> None:
        """Инициализатор класса ``SoapError``.

        Args:
            action (``str``): Действие, которое было вызвано клиентом.
            detail (``str``): Дополнительные подробности об операции.
            params (``dict | None``, ``optional``): Дополнительные параметры,
                указанные для action. Defaults to None.
        """
        super().__init__(f"SOAP-метод {action!r} завершился ошибкой: {detail}")
        self.action = action
        self.detail = detail
        self.params = params
