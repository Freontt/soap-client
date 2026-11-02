"""Файл определяет класс для получения данных из 1С."""

from asyncio import Semaphore
from typing import cast

from aiolimiter import AsyncLimiter
from lxml import etree
from zeep import AsyncClient
from zeep.exceptions import Error
from zeep.transports import AsyncTransport

from soap_client.exceptions import SoapError
from soap_client.settings import BaseSoapClientSettings


class SoapClientManager:
    """Класс-обёртка над клиентом zeep для работы с 1с.

    Attributes:
        config (``SoapClientConfig``): Конфигурация SOAP-клиента.
        timeout (``int``): Максимальное время ожидания ответа.
        client (``zeep.AsyncClient | None``): SOAP-клиент.
    """

    def __init__(self, settings: BaseSoapClientSettings, *, timeout: int = 120) -> None:
        """Инициализатор класса ``SoapClientManager``.

        Args:
            settings (``SoapClientConfig``): Конфигурация SOAP-клиента.
            timeout (``int``, ``optional``): Максимальное время ожидания. Defaults to 120.
        """
        self.settings = settings
        self.timeout = timeout
        self.client: AsyncClient | None = None
        self.__semaphore = Semaphore(settings.max_concurrent)
        self.__limiter = AsyncLimiter(settings.rate_limit, 1)

    def init(self) -> None:
        """Инициализирует единоразово в lifespan FastAPI zeep-клиент и настраивает подключение."""
        if self.is_initialized:
            return
        try:
            transport = AsyncTransport(
                timeout=self.timeout,
                operation_timeout=self.timeout,
            )
            transport.client.auth = (self.settings.login, self.settings.password)

            wsdl = self.settings.wsdl
            self.client = AsyncClient(wsdl=wsdl, transport=transport)
        except Exception as e:
            raise SoapError(action="<init>", detail=str(e)) from e

    @property
    def is_initialized(self) -> bool:
        """Свойство - инициализирован ли SOAP-клиент из zeep.

        Returns:
            bool: Если инициализирован - ``true``, иначе ``false``.
        """
        return self.client is not None

    async def load(self, action: str, params: dict | None = None) -> object | None:
        """Вызывает SOAP-метод по имени.

        Args:
            action (``str``): Имя метода, как объявлено в WSDL.
            params (``dict | None``): Параметры, которые необходимо отправить вместе с действием.

        Returns:
            ``object | None``: Результат, который вернул ``zeep`` клиент.

        Raises:
            ``RuntimeError``: Если клиент не инициализирован.

        See Also:
            - :class:`SoapError`: Класс ошибок SOAP-подключений.
            - :class:`BaseSoapClientSettings`: Базовый класс настроек.
        """
        if self.client is None:
            raise RuntimeError("Клиент не инициализирован.")
        async with self.__limiter, self.__semaphore:
            try:
                method = getattr(self.client.service, action)
                if isinstance(params, str):
                    # Аналог SoapVar($xml, XSD_ANYXML) - сырой XML в тело запроса.
                    return await method(etree.fromstring(params.strip()))
                return await method(**(params or {}))
            except Error:
                return None

    async def aclose(self) -> None:
        """Функция для закрытия клиента."""
        if self.client is not None:
            transport = cast("AsyncTransport", self.client.transport)
            await transport.aclose()
