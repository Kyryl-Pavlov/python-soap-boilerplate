import xml.etree.ElementTree as ET
from unittest.mock import patch

import bcrypt as _bcrypt
import pytest
from sqlalchemy.pool import StaticPool

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "urn:flask-soap-boilerplate"


@pytest.fixture(scope="session", autouse=True)
def fast_bcrypt():
    _real_gensalt = _bcrypt.gensalt
    with patch(
        "app.models.user.bcrypt.gensalt",
        side_effect=lambda rounds=12: _real_gensalt(rounds=4),
    ):
        yield


@pytest.fixture(scope="session")
def app(fast_bcrypt):
    from app import create_app
    from app.extensions import db as _db

    flask_app = create_app("testing")
    flask_app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
            "JWT_SECRET_KEY": "test-jwt-secret-key-minimum-32-bytes!!",
            "SECRET_KEY": "test-secret-key-minimum-32-bytes!!!!",
            "REDIS_URL": None,
        }
    )

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_tables(app):
    from app.extensions import db

    yield
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def soap(client):
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
        return client.post(
            "/soap", data=envelope.encode(), content_type="text/xml;charset=UTF-8"
        )

    return _call


def parse_soap(response):
    root = ET.fromstring(response.data)
    body = root.find(f"{{{SOAP_NS}}}Body")
    if body is None or len(body) == 0:
        return None
    return body[0]


def _local(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def get_text(element, tag):
    # Spyne assigns ComplexModel fields their own derived namespace, so match by local name only.
    for el in element.iter():
        if _local(el.tag) == tag:
            return el.text
    return None


def _find_fault(body):
    for child in body:
        if _local(child.tag) == "Fault":
            return child
    return None


def is_fault(response):
    root = ET.fromstring(response.data)
    body = root.find(f"{{{SOAP_NS}}}Body")
    return body is not None and _find_fault(body) is not None


def get_fault_code(response):
    root = ET.fromstring(response.data)
    body = root.find(f"{{{SOAP_NS}}}Body")
    fault = _find_fault(body) if body is not None else None
    if fault is None:
        return None
    code = fault.find("faultcode")
    if code is None or not code.text:
        return None
    # Strip SOAP namespace prefix (e.g. "soap11env:Client.Auth.Missing" → "Client.Auth.Missing")
    return code.text.split(":", 1)[-1] if ":" in code.text else code.text


@pytest.fixture
def registered_user(soap):
    soap("register", "<email>user@example.com</email><password>Pass123!</password>")
    return {"email": "user@example.com", "password": "Pass123!"}


@pytest.fixture
def access_token(soap, registered_user):
    r = soap(
        "login",
        f"<email>{registered_user['email']}</email>"
        f"<password>{registered_user['password']}</password>",
    )
    el = parse_soap(r)
    return get_text(el, "access_token")


@pytest.fixture
def refresh_token(soap, registered_user):
    r = soap(
        "login",
        f"<email>{registered_user['email']}</email>"
        f"<password>{registered_user['password']}</password>",
    )
    el = parse_soap(r)
    return get_text(el, "refresh_token")


@pytest.fixture
def mock_cache(app):
    from unittest.mock import MagicMock

    m = MagicMock()
    app.cache = m
    yield m
    app.cache = None
