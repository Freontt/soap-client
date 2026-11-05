import pytest

from soap_client.settings import BaseSoapClientSettings
from soap_client.registry import SoapRegistry, SoapClientManager
from soap_client.exceptions import SoapError


@pytest.fixture
def calculator_manager(calculator_wsdl_url):
    settings = BaseSoapClientSettings(
        wsdl=calculator_wsdl_url,
        login="",
        password="",
        max_concurrent=3,
        rate_limit=10,
    )
    registry = SoapRegistry({"calc": settings})
    manager = registry.get("calc")
    assert manager is not None
    return manager


class TestCorrectUses:
    @pytest.mark.asyncio
    async def test_add_returns_sum(self, calculator_manager):
        result = await calculator_manager.load("add", {"a": 1, "b": 2})
        assert result == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [(0, 0, 0), (-5, 5, 0), (100, 23, 123), (10**6, 1, 10**6 + 1)],
    )
    async def test_add_various(self, calculator_manager, a, b, expected):
        result = await calculator_manager.load("add", {"a": a, "b": b})
        assert result == expected

    @pytest.mark.asyncio
    async def test_echo_returns_string(self, calculator_manager):
        result = await calculator_manager.load("echo", {"text": "hello"})
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_aclose_manager(self, calculator_wsdl_url):
        settings = BaseSoapClientSettings(
            wsdl=calculator_wsdl_url,
            login="",
            password="",
            max_concurrent=3,
            rate_limit=10,
        )
        manager = SoapClientManager(settings)
        manager.init()
        await manager.aclose()
        assert manager.is_initialized == False
        


class TestIncorrectUses:
    @pytest.mark.asyncio
    async def test_load_unknown_action_raises(self, calculator_manager):
        with pytest.raises(Exception):
            await calculator_manager.load("nonexistent", {})

    @pytest.mark.asyncio
    async def test_load_none_params_uses_empty_dict(self, calculator_manager):
        with pytest.raises(Exception):
            await calculator_manager.load("add", None)

    @pytest.mark.asyncio
    async def test_init_inited_manager(self, calculator_manager):
        calculator_manager.init()

    @pytest.mark.asyncio
    async def test_init_with_incorrect_wsdl_manager(self):
        settings = BaseSoapClientSettings(
            wsdl="???",
            login="",
            password="",
            max_concurrent=3,
            rate_limit=10
        )
        with pytest.raises(SoapError):
            custom_manager = SoapClientManager(settings).init()

    @pytest.mark.asyncio
    async def test_using_manager_without_init(self, calculator_wsdl_url):
        settings = BaseSoapClientSettings(
            wsdl=calculator_wsdl_url,
            login="",
            password="",
            max_concurrent=3,
            rate_limit=10,
        )
        with pytest.raises(RuntimeError, match="Клиент не инициализирован."):
            manager = SoapClientManager(settings)
            result = await manager.load("add", {"a": 1, "b": 2})
