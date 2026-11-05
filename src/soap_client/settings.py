"""File contains implementation of the BaseSoapClientSettings and helpful function."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSoapClientSettings(BaseSettings):
    """Базовые настройки SOAP-клиента для взаимодействия с 1с.

    Attributes:
        wsdl (``str``): WSDL - контракт интерфейса по взаимодействию с 1С.
        login (``str``): Логин, по которому происходит вход.
        password (``str``): Пароль, по которому происходит вход.
        max_concurrent (``int``): Максимально число одновременных вызовов.
        rate_limit (``int``): Максимальное число запросов в секунду.

    Note:
        - Используется для создания пользовательских типов конфигураций.
        - Вызовите ``get_model_config`` для создания Pydantic настроек.
        Без этого подкласс унаследует дефолтный конфиг Pydantic, и настройки
        не будут читаться из ``.env``.
    """

    # Main settings of connection by wsdl
    wsdl: str = Field(min_length=1)
    login: str
    password: str
    # Settings of the connection load
    max_concurrent: int = Field(gt=0)
    rate_limit: int = Field(gt=0)


def get_model_config(
    env_prefix: str, env_file: str | Path = ".env", env_file_encoding: str = "UTF-8"
) -> SettingsConfigDict:
    """Вспомогательная функция для генерации model_config.

    Args:
        env_prefix (``str``): Префикс в ``.env`` файле,
            который будет использован для настроек.
        env_file (``str | Path``, ``optional``): Путь до ``.env`` файла. Defaults to ".env".
        env_file_encoding (``str``, ``optional``):
            Кодировка ``.env`` файла. Defaults to "UTF-8".

    Returns:
        SettingsConfigDict: model_config для настроек.
    """
    return SettingsConfigDict(
        env_file=env_file,
        env_file_encoding=env_file_encoding,
        env_prefix=env_prefix,
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )
