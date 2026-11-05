"""SOAP client library."""

import logging

from soap_client.manager import BaseSoapClientSettings, SoapClientManager, SoapError
from soap_client.registry import SoapRegistry

__all__ = ["BaseSoapClientSettings", "SoapClientManager", "SoapError", "SoapRegistry"]
__version__ = "0.1.0"


logging.getLogger("soap_client").addHandler(logging.NullHandler())
