"""SOAP client library."""

import logging

from soap_client.exceptions import SoapError
from soap_client.manager import SoapClientManager
from soap_client.registry import SoapRegistry
from soap_client.settings import BaseSoapClientSettings

__all__ = ["BaseSoapClientSettings", "SoapClientManager", "SoapError", "SoapRegistry"]
__version__ = "0.1.0"


logging.getLogger("soap_client").addHandler(logging.NullHandler())
