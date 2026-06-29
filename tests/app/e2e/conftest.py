import os
import xml.etree.ElementTree as ET

import pytest
import requests as _requests

SOAP_URL = os.getenv("E2E_SOAP_URL", "http://localhost/soap")
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "urn:flask-soap-boilerplate"


@pytest.fixture(scope="session")
def soap_url():
    return SOAP_URL


@pytest.fixture(scope="session")
def http():
    session = _requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def soap(http, soap_url):
    def _call(method, body_xml="", access_token=None):
        if access_token:
            header_xml = (
                f'<tns:AuthHeader xmlns:tns="{TNS}">'
                f"<tns:access_token>{access_token}</tns:access_token>"
                f"</tns:AuthHeader>"
            )
        else:
            header_xml = ""
        envelope = (
            f'<?xml version="1.0"?>'
            f'<soapenv:Envelope xmlns:soapenv="{SOAP_NS}" xmlns:tns="{TNS}">'
            f"<soapenv:Header>{header_xml}</soapenv:Header>"
            f"<soapenv:Body><tns:{method}>{body_xml}</tns:{method}></soapenv:Body>"
            f"</soapenv:Envelope>"
        )
        return http.post(
            soap_url,
            data=envelope.encode(),
            headers={"Content-Type": "text/xml;charset=UTF-8"},
        )

    return _call


def parse_body(response):
    root = ET.fromstring(response.text)
    body = root.find(f"{{{SOAP_NS}}}Body")
    if body is None or len(body) == 0:
        return None
    return body[0]


def get_text(element, tag):
    for el in element.iter():
        local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if local == tag:
            return el.text
    return None


def is_fault(response):
    root = ET.fromstring(response.text)
    body = root.find(f"{{{SOAP_NS}}}Body")
    if body is None:
        return False
    for child in body:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "Fault":
            return True
    return False


@pytest.fixture(scope="session")
def access_token(soap):
    soap(
        "register", "<email>e2e@ci-test.internal</email><password>E2eTest1!</password>"
    )
    r = soap(
        "login", "<email>e2e@ci-test.internal</email><password>E2eTest1!</password>"
    )
    el = parse_body(r)
    return get_text(el, "access_token")
