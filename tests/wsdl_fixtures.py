"""WSDL-контракты и динамические хендлеры для мок-серверов."""
from lxml import etree
from werkzeug.wrappers import Response
from time import sleep

# ---------- calculator contract ----------
CALCULATOR_NS = "http://example.com/calculator"
CALCULATOR_NSMAP = {"c": CALCULATOR_NS}

CALCULATOR_WSDL = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://example.com/calculator"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://example.com/calculator">
  <types>
    <xsd:schema targetNamespace="http://example.com/calculator"
                elementFormDefault="qualified">
      <xsd:element name="add">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:int"/>
            <xsd:element name="b" type="xsd:int"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="addResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="addResult" type="xsd:int"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="echo">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="text" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="echoResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="echoResult" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </types>
  <message name="addInput"><part name="parameters" element="tns:add"/></message>
  <message name="addOutput"><part name="parameters" element="tns:addResponse"/></message>
  <message name="echoInput"><part name="parameters" element="tns:echo"/></message>
  <message name="echoOutput"><part name="parameters" element="tns:echoResponse"/></message>
  <portType name="CalculatorPort">
    <operation name="add">
      <input message="tns:addInput"/><output message="tns:addOutput"/>
    </operation>
    <operation name="echo">
      <input message="tns:echoInput"/><output message="tns:echoOutput"/>
    </operation>
  </portType>
  <binding name="CalculatorBinding" type="tns:CalculatorPort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="add">
      <soap:operation soapAction="add"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="echo">
      <soap:operation soapAction="echo"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
  </binding>
  <service name="CalculatorService">
    <port name="CalculatorPort" binding="tns:CalculatorBinding">
      <soap:address location="ENDPOINT"/>
    </port>
  </service>
</definitions>
"""

# ---------- timestamp (clock) contract ----------
TIMESTAMP_NS = "http://example.com/timestamp"
TIMESTAMP_NSMAP = {"t": TIMESTAMP_NS}

TIMESTAMP_WSDL = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://example.com/timestamp"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://example.com/timestamp">
  <types>
    <xsd:schema targetNamespace="http://example.com/timestamp"
                elementFormDefault="qualified">
      <xsd:element name="now">
        <xsd:complexType><xsd:sequence/></xsd:complexType>
      </xsd:element>
      <xsd:element name="nowResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="nowResult" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </types>
  <message name="nowInput"><part name="parameters" element="tns:now"/></message>
  <message name="nowOutput"><part name="parameters" element="tns:nowResponse"/></message>
  <portType name="TimestampPort">
    <operation name="now">
      <input message="tns:nowInput"/><output message="tns:nowOutput"/>
    </operation>
  </portType>
  <binding name="TimestampBinding" type="tns:TimestampPort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="now">
      <soap:operation soapAction="now"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
  </binding>
  <service name="TimestampService">
    <port name="TimestampPort" binding="tns:TimestampBinding">
      <soap:address location="ENDPOINT"/>
    </port>
  </service>
</definitions>
"""

FIXED_NOW = "2026-11-03T12:00:00Z"


def soap_envelope(body: str) -> str:
    return f"""<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>{body}</soap:Body>
</soap:Envelope>"""


def calculator_handler(request):
    root = etree.fromstring(request.get_data())

    add_el = root.find(".//c:add", CALCULATOR_NSMAP)
    if add_el is not None:
        a = int(add_el.findtext("c:a", namespaces=CALCULATOR_NSMAP))
        b = int(add_el.findtext("c:b", namespaces=CALCULATOR_NSMAP))
        body = (
            f'<ns0:addResponse xmlns:ns0="{CALCULATOR_NS}">'
            f"<ns0:addResult>{a + b}</ns0:addResult>"
            f"</ns0:addResponse>"
        )
    else:
        echo_el = root.find(".//c:echo", CALCULATOR_NSMAP)
        text = echo_el.findtext("c:text", namespaces=CALCULATOR_NSMAP) if echo_el is not None else ""
        body = (
            f'<ns0:echoResponse xmlns:ns0="{CALCULATOR_NS}">'
            f"<ns0:echoResult>{text}</ns0:echoResult>"
            f"</ns0:echoResponse>"
        )
    sleep(0.1)
    return Response(
        soap_envelope(body),
        status=200,
        content_type="text/xml; charset=utf-8",
    )


def timestamp_handler(request):
    body = (
        f'<ns0:nowResponse xmlns:ns0="{TIMESTAMP_NS}">'
        f"<ns0:nowResult>{FIXED_NOW}</ns0:nowResult>"
        f"</ns0:nowResponse>"
    )
    sleep(0.1)
    return Response(
        soap_envelope(body),
        status=200,
        content_type="text/xml; charset=utf-8",
    )