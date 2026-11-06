"""File contains implementation of the SoapClientManager."""

import logging
from asyncio import Semaphore
from typing import Any, cast

from aiolimiter import AsyncLimiter
from zeep import AsyncClient
from zeep.exceptions import Error
from zeep.transports import AsyncTransport

from soap_client.exceptions import SoapError
from soap_client.settings import BaseSoapClientSettings

logger = logging.getLogger(__name__)


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
        logger.debug("Manager created for wsdl=%r", settings.wsdl)

    def init(self) -> None:
        """Создаёт zeep-клиент и настраивает подключение.

        Note:
            Необходимо единоразово вызвать (к примеру: в ``lifespan`` FastAPI).
        """
        logger.debug("Initializing client for wsdl=%r", self.settings.wsdl)
        if self.is_initialized:
            logger.warning("Trying to init client when that inited already.")
            return
        try:
            transport = AsyncTransport(
                timeout=self.timeout,
                operation_timeout=self.timeout,
            )
            if self.settings.login and self.settings.password:
                transport.wsdl_client.auth = (self.settings.login, self.settings.password)
                transport.client.auth = (self.settings.login, self.settings.password)
            else:
                logger.debug("No auth credentials provided; skipping Basic auth")
            logger.debug("zeep AsyncTransport created")

            wsdl = self.settings.wsdl
            self.client = AsyncClient(wsdl=wsdl, transport=transport)
            logger.info("zeep client created for wsdl=%r", self.settings.wsdl)
        except Exception as e:
            logger.debug("Incorrect init data", exc_info=True)
            raise SoapError(action="<init>", detail=str(e)) from e

    @property
    def is_initialized(self) -> bool:
        """Свойство - инициализирован ли SOAP-клиент из zeep.

        Returns:
            ``bool``: Если инициализирован - ``true``, иначе ``false``.
        """
        return self.client is not None

    async def load(self, action: str, params: dict[str, Any] | None = None) -> object:
        """Вызывает SOAP-метод по имени.

        Args:
            action (``str``): Имя метода, как объявлено в WSDL.
            params (``dict[str, Any] | None``): Параметры, которые
                необходимо отправить вместе с действием.

        Returns:
            ``object``: Результат, который вернул ``zeep`` клиент.

        Raises:
            ``RuntimeError``: Если клиент не инициализирован.
            ``AttributeError``: Если требуемого динамического атрибута нет.
            ``SoapError``: Если произошла ошибка при работе zeep клиента.

        See Also:
            - :class:`SoapError`: Класс ошибок SOAP-подключений.
            - :class:`BaseSoapClientSettings`: Базовый класс настроек.
        """
        if self.client is None:
            logger.error("Trying to load without inited client.")
            raise RuntimeError("Client didn't init.")
        logger.debug("load(%r) params=%r", action, params)
        try:
            method = getattr(self.client.service, action)
        except AttributeError:
            logger.exception("Unknown action %r", action)
            raise
        async with self.__limiter, self.__semaphore:
            try:
                result = await method(**(params or {}))
            except Error as e:
                logger.debug("load(%r) failed params=%r.", action, params, exc_info=True)
                raise SoapError(action=action, detail=str(e)) from e
            else:
                logger.debug("load(%r) ok.", action)
                return result

    async def aclose(self) -> None:
        """Функция для закрытия клиента."""
        logger.debug("Closing client for wsdl=%r.", self.settings.wsdl)
        if self.client is not None:
            transport = cast("AsyncTransport", self.client.transport)
            await transport.aclose()
            self.client = None
            logger.info("Client closed for wsdl=%r.", self.settings.wsdl)
        else:
            logger.warning("Trying to close client when that didn't init.")
