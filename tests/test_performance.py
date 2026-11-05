import asyncio
import statistics
import time

import pytest

from soap_client.settings import BaseSoapClientSettings
from soap_client.registry import SoapRegistry


pytestmark = pytest.mark.performance


def _make_manager(wsdl_url):
    settings = BaseSoapClientSettings(
        wsdl=wsdl_url,
        login="",
        password="",
        max_concurrent=10, 
        rate_limit=1000
    )
    registry = SoapRegistry({"perf": settings})
    manager = registry.get("perf")
    assert manager is not None
    return manager


class TestPerformance:
    @pytest.mark.asyncio
    async def test_single_request_latency(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url)
        start = time.perf_counter()
        await manager.load("add", {"a": 1, "b": 1})
        latency = time.perf_counter() - start
        assert latency < 1.0, f"слишком медленно: {latency:.3f}s"

    @pytest.mark.asyncio
    async def test_throughput_sequential(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url)
        n = 50
        timings: list[float] = []
        for i in range(n):
            t0 = time.perf_counter()
            await manager.load("add", {"a": i, "b": 1})
            timings.append(time.perf_counter() - t0)

        avg = statistics.mean(timings)
        p95 = statistics.quantiles(timings, n=20)[-1]
        print(f"\nsequential: avg={avg*1000:.1f}ms p95={p95*1000:.1f}ms")

        assert avg < 0.5
        assert p95 < 1.0

    @pytest.mark.asyncio
    async def test_throughput_parallel(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url)
        n = 50
        start = time.perf_counter()
        results = await asyncio.gather(
            *(manager.load("add", {"a": i, "b": 1}) for i in range(n))
        )
        elapsed = time.perf_counter() - start
        rps = n / elapsed
        print(f"\nparallel: {n} req in {elapsed:.3f}s = {rps:.1f} rps")

        assert results == [i + 1 for i in range(n)]
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self, calculator_wsdl_url):
        manager = _make_manager(calculator_wsdl_url)
        n = 20

        t0 = time.perf_counter()
        for i in range(n):
            await manager.load("add", {"a": i, "b": 0})
        sequential = time.perf_counter() - t0

        t0 = time.perf_counter()
        await asyncio.gather(*(manager.load("add", {"a": i, "b": 0}) for i in range(n)))
        parallel = time.perf_counter() - t0

        print(f"\nseq={sequential:.3f}s par={parallel:.3f}s speedup={sequential/parallel:.2f}x")
        assert parallel < sequential