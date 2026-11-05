# soap-client

Асинхронная обёртка над [`zeep`](https://github.com/mvantellingen/python-zeep) для работы с SOAP-сервисами: управление клиентами, ограничение нагрузки и единая точка инициализации в `lifespan` FastAPI.

<!-- [![PyPI](https://img.shields.io/pypi/v/soap-client.svg)](https://pypi.org/project/soap-client/)
[![Python](https://img.shields.io/pypi/pyversions/soap-client.svg)](https://pypi.org/project/soap-client/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) -->

## Возможности

- **`SoapClientManager`** -- обёртка над `zeep.AsyncClient` с контролем конкурентности (`Semaphore`) и rate limit (`AsyncLimiter`).
- **`SoapRegistry`** -- реестр нескольких SOAP-клиентов с инициализацией в `lifespan` и корректным закрытием соединений.
- **`BaseSoapClientSettings`** -- настройки на Pydantic Settings, читаются из `.env`.
- **`SoapError`** -- единый тип ошибки для всех SOAP-вызовов, наследник `ConnectionError`.

## Установка

Если вы пользуетесь менеджером uv: 

```bash
uv add soap-client
```

или через pip:

```bash
pip install soap-client
```

## Быстрый старт

* Настройки из .env:  

```python
from soap_client.settings import BaseSoapClientSettings, get_model_config


class OneCSettings(BaseSoapClientSettings):
    model_config = get_model_config(env_prefix="ONEC_")
```

```env
# .env
ONEC_WSDL=https://example.com/ws/one.1cws?wsdl
ONEC_LOGIN=user
ONEC_PASSWORD=secret
ONEC_MAX_CONCURRENT=10
ONEC_RATE_LIMIT=5
```

* Реестр клиентов:  

```python
# registry.py
from soap_client.registry import SoapRegistry
from settings import OneCSettings

registry = SoapRegistry({"onec": OneCSettings()})
```

* Использование в lifespan FastAPI:  

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from registry import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.init_all()
    try:
        yield
    finally:
        await registry.aclose_all()


app = FastAPI(lifespan=lifespan)
```

* Вызов SOAP-метода:  

```python
from registry import registry


async def get_counterparty(inn: str) -> dict:
    client = registry.get("onec")
    return await client.load("GetStudent", params={"ID": inn})
```

## Основные компоненты

### SoapClientManager
| Метод / свойство | Назначение |
|------------------|------------|
| init() | Инициализирует zeep.AsyncClient (вызывайте один раз в lifespan). |
| is_initialized | True, если клиент готов к работе. |
| load(action, params=None) | Асинхронно вызывает SOAP-метод по имени. |
| aclose() | Закрывает AsyncTransport. |

### SoapRegistry

| Метод / свойство | Назначение |
|------------------|------------|
| init_all() | инициализирует всех клиентов из конфигурации. |
| get(name) | возвращает (при первом обращении создаёт) менеджера по имени. |
| aclose_all() | закрывает все соединения, исключения логируются, но не пробрасываются. |

### SoapError

```python
from soap_client.exceptions import SoapError

try:
    await client.load("GetCompany", params={"INN": "7700000000"})
except SoapError as e:
    print(e.action, e.detail, e.params)
```

## Требования

**Версия языка:**  
Python 3.11+

**Библиотеки:**  
zeep[async], aiolimiter, pydantic-settings, pydantic
