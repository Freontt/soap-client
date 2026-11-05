import asyncio

import pytest

from soap_client.settings import BaseSoapClientSettings
from soap_client.registry import SoapRegistry
from copy import copy


class TestRegistryMultiWsdl:
    @pytest.fixture
    def registry(self, calculator_wsdl_url, timestamp_wsdl_url):
        return SoapRegistry(
            {
                "calc": BaseSoapClientSettings(
                    wsdl=calculator_wsdl_url,
                    login="",
                    password="",
                    max_concurrent=2,
                    rate_limit=5
                ),
                "clock": BaseSoapClientSettings(
                    wsdl=timestamp_wsdl_url,
                    login="",
                    password="",
                    max_concurrent=2,
                    rate_limit=5
                ),
            }
        )

    @pytest.mark.asyncio
    async def test_registry_init_all_and_aclose_all(self, registry):
        registry.init_all()
        assert registry._clients.get("calc").is_initialized == True
        assert registry._clients.get("clock").is_initialized == True

        clients = copy(registry._clients)
        await registry.aclose_all()
        assert clients.get("calc").is_initialized == False
        assert clients.get("clock").is_initialized == False

    @pytest.mark.asyncio
    async def test_two_contracts_isolated(self, registry):
        calc = registry.get("calc")
        clock = registry.get("clock")
        assert calc is not None and clock is not None
        assert calc is not clock

        add_result = await calc.load("add", {"a": 2, "b": 3})
        now_result = await clock.load("now", {})

        assert add_result == 5
        assert now_result == "2026-11-03T12:00:00Z"

    @pytest.mark.asyncio
    async def test_operation_not_in_other_contract(self, registry):
        clock = registry.get("clock")
        assert clock is not None
        with pytest.raises(Exception):
            await clock.load("add", {"a": 1, "b": 1})

    @pytest.mark.asyncio
    async def test_registry_get_unknown_returns_none_or_raises(self, registry):
        try:
            missing = registry.get("nope")
        except KeyError:
            return
        assert missing is None

    @pytest.mark.asyncio
    async def test_concurrent_calls_across_contracts(self, registry):
        calc = registry.get("calc")
        clock = registry.get("clock")
        assert calc is not None and clock is not None

        results = await asyncio.gather(
            calc.load("add", {"a": 1, "b": 1}),
            clock.load("now", {}),
            calc.load("add", {"a": 2, "b": 2}),
            clock.load("now", {}),
        )
        assert results == [2, "2026-11-03T12:00:00Z", 4, "2026-11-03T12:00:00Z"]