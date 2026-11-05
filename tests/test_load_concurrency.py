import asyncio
import time

import pytest

from soap_client.settings import BaseSoapClientSettings
from soap_client.registry import SoapRegistry


def _make_manager(wsdl_url, max_concurrent: int, rate_limit: int):
    settings = BaseSoapClientSettings(
        wsdl=wsdl_url,
        login="",
        password="",
        max_concurrent=max_concurrent,
        rate_limit=rate_limit
    )
    registry = SoapRegistry({"test": settings})
    manager = registry.get("test")
    assert manager is not None
    return manager


class TestRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_serializes_requests(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url, max_concurrent=10, rate_limit=5)

        start = time.perf_counter()
        results = await asyncio.gather(
            *(manager.load("add", {"a": i, "b": i}) for i in range(10))
        )
        elapsed = time.perf_counter() - start

        assert results == [i + i for i in range(10)]
        assert elapsed >= 0.9, f"rate_limit не сработал: {elapsed:.2f}s"


class TestSemaphore:
    @pytest.mark.asyncio
    async def test_max_concurrent_limits_parallelism(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url, max_concurrent=2, rate_limit=1000)

        active = 0
        max_seen = 0
        original_call = manager.client.service.add # type: ignore

        async def spy(*args, **kwargs):
            nonlocal active, max_seen
            active += 1
            max_seen = max(max_seen, active)
            try:
                await asyncio.sleep(0.05)
                return await original_call(*args, **kwargs)
            finally:
                active -= 1

        manager.client.service.add = spy  # type: ignore[method-assign]

        results = await asyncio.gather(
            *(manager.load("add", {"a": i, "b": 1}) for i in range(10))
        )

        assert results == [i + 1 for i in range(10)]
        assert max_seen <= 2, f"semaphore не ограничил: {max_seen}"

    @pytest.mark.asyncio
    async def test_high_load_100_requests(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url, max_concurrent=5, rate_limit=100)
        results = await asyncio.gather(
            *(manager.load("add", {"a": i, "b": 0}) for i in range(100))
        )
        assert results == list(range(100))


class TestMixedLoad:
    @pytest.mark.asyncio
    async def test_rate_limit_and_semaphore_together(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url, max_concurrent=3, rate_limit=10)

        start = time.perf_counter()
        results = await asyncio.gather(
            *(manager.load("add", {"a": i, "b": i}) for i in range(30))
        )
        elapsed = time.perf_counter() - start

        assert results == [i * 2 for i in range(30)]
        assert 1.6 <= elapsed <= 5.0