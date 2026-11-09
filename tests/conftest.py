import pytest
from pytest_httpserver import HTTPServer

from wsdl_fixtures import (
    CALCULATOR_WSDL,
    TIMESTAMP_WSDL,
    calculator_handler,
    timestamp_handler,
)


@pytest.fixture()
def calculator_server(httpserver: HTTPServer) -> HTTPServer:
    endpoint = httpserver.url_for("/")
    wsdl = CALCULATOR_WSDL.replace("ENDPOINT", endpoint)
    httpserver.expect_request("/", method="GET").respond_with_data(
        wsdl, content_type="text/xml"
    )
    httpserver.expect_request("/", method="POST").respond_with_handler(
        calculator_handler
    )
    return httpserver


@pytest.fixture
def timestamp_server() -> HTTPServer:
    """Отдельный сервер на своём порту — не конфликтует с httpserver."""
    server = HTTPServer(threaded=True)
    server.start()
    endpoint = server.url_for("/")
    server.expect_request("/", method="GET").respond_with_data(
        TIMESTAMP_WSDL.replace("ENDPOINT", endpoint), content_type="text/xml"
    )
    server.expect_request("/", method="POST").respond_with_handler(
        timestamp_handler
    )
    yield server
    server.stop()


@pytest.fixture
def calculator_wsdl_url(calculator_server: HTTPServer) -> str:
    return calculator_server.url_for("/?wsdl")


@pytest.fixture
def timestamp_wsdl_url(timestamp_server: HTTPServer) -> str:
    return timestamp_server.url_for("/?wsdl")