"""File contains implementation of the SoapRegistry."""

import logging
from collections.abc import Mapping

from soap_client.manager import SoapClientManager
from soap_client.settings import BaseSoapClientSettings

logger = logging.getLogger(__name__)


class SoapRegistry:
    """Класс для запуска, настройки, проверки и закрытия SOAP-клиентов.

    See Also:
    - :class:`SoapClientManager`: Менеджер SOAP-клиента.
    - :class:`BaseSoapClientSettings`: Базовый класс настроек.
    """

    def __init__(self, settings: Mapping[str, BaseSoapClientSettings]) -> None:
        """Инициализатор класса ``SoapRegistry``.

        Args:
            settings (``SoapClientSettings``): Настройки для клиентов.
        """
        self._settings = dict(settings)
        self._clients: dict[str, SoapClientManager] = {}
        logger.debug("Registry created for %d clients: %r", len(settings), list(settings))

    def init_all(self) -> None:
        """Инициализация всех клиентов.

        Note:
            Блокирует event loop на время загрузки WSDL. Вызывайте из lifespan.
        """
        logger.debug("Initializing all clients")
        for name in self._settings:
            self.get(name)
        logger.info("All clients initialized")

    def get(self, soap_client_name: str) -> SoapClientManager:
        """Получить или создать SOAP-клиента.

        Args:
            soap_client_name (``str``): Имя SOAP-клиента.

        Returns:
            ``SoapClientManager``: Запрашиваемый менеджер SOAP-клиента.

        Raises:
            ``KeyError``: Возникает если передан незаданный тип клиента.
            ``SoapError``: Если не удалось инициализировать клиента.

        Note:
            При создании выполняет синхронную загрузку WSDL и блокирует
            event loop. Вызывайте из lifespan FastAPI или похожего по роли контекста.
        """
        if soap_client_name not in self._settings:
            logger.error(
                "Unknown client %r; available: %r",
                soap_client_name,
                list(self._settings),
            )
            raise KeyError(
                f"Unknown soap client: {soap_client_name!r}. Available: {list(self._settings)!r}"
            )
        if soap_client_name not in self._clients:
            logger.debug("Creating client %r", soap_client_name)
            config = self._settings[soap_client_name]
            client = SoapClientManager(config)
            client.init()
            self._clients[soap_client_name] = client
        return self._clients[soap_client_name]

    async def aclose_all(self) -> None:
        """Закрыть все соединения."""
        logger.debug("Closing %d clients", len(self._clients))
        for name, client in self._clients.items():
            try:
                await client.aclose()
            except Exception:
                logger.exception("Failed to close client %r", name)
        self._clients.clear()
        logger.info("All clients closed")
