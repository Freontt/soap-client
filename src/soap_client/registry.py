"""Файл определяет класс по созданию SoapClientManager."""

from collections.abc import Mapping

from soap_client.manager import SoapClientManager
from soap_client.settings import BaseSoapClientSettings


class SoapRegistry:
    """Класс для запуска, настройки, проверки и закрытия SOAP-клиентов."""

    def __init__(self, settings: Mapping[str, BaseSoapClientSettings]) -> None:
        """Инициализатор класса ``SoapRegistry``.

        Args:
            settings (``SoapClientSettings``): Настройки для клиентов.
        """
        self._settings = settings
        self._clients: dict[str, SoapClientManager] = {}

    def init_all(self) -> None:
        """Инициализация всех клиентов."""
        for name in self._settings:
            self.get(name)

    def get(self, soap_client_name: str) -> SoapClientManager:
        """Получить или создать SOAP-клиента.

        Args:
            soap_client_name (``str``): Имя SOAP-клиента.

        Returns:
            ``SoapClientManager``: Запрашиваемый менеджер SOAP-клиента.

        Raises:
            ``ValueError``: Возникает если передан незаданный тип клиента.
        """
        if soap_client_name not in self._settings:
            raise ValueError("Неизвестный тип клиента.")
        if soap_client_name not in self._clients:
            config = self._settings[soap_client_name]
            client = SoapClientManager(config)
            client.init()
            self._clients[soap_client_name] = client
        return self._clients[soap_client_name]

    async def aclose_all(self) -> None:
        """Закрыть все соединения."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
