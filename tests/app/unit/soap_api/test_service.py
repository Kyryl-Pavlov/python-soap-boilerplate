import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt as pyjwt
import pytest
from spyne.error import Fault

from app.utils.auth import decode_jwt, verify_access_token

SECRET = "test-secret-key-minimum-32-bytes!!!!"
ALGORITHM = "HS256"
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "urn:flask-soap-boilerplate"


def _flask_app(secret=SECRET):
    app = MagicMock()
    app.config = {"JWT_SECRET_KEY": secret, "JWT_ALGORITHM": ALGORITHM}
    return app


def _make_token(sub="user-1", token_type="access", expired=False, secret=SECRET):
    exp = datetime.now(timezone.utc) + (
        timedelta(seconds=-1) if expired else timedelta(hours=1)
    )
    payload = {"sub": sub, "type": token_type, "exp": exp}
    return pyjwt.encode(payload, secret, algorithm=ALGORITHM)


def _ctx(token=None):
    ctx = MagicMock()
    if token:
        xml = (
            f'<soapenv:Envelope xmlns:soapenv="{SOAP_NS}" xmlns:tns="{TNS}">'
            f"<soapenv:Header>"
            f"<tns:AuthHeader><tns:access_token>{token}</tns:access_token></tns:AuthHeader>"
            f"</soapenv:Header>"
            f"<soapenv:Body/></soapenv:Envelope>"
        )
    else:
        xml = (
            f'<soapenv:Envelope xmlns:soapenv="{SOAP_NS}" xmlns:tns="{TNS}">'
            f"<soapenv:Header/><soapenv:Body/></soapenv:Envelope>"
        )
    ctx.in_document = ET.fromstring(xml)
    return ctx


def testverify_access_token_missing():
    with pytest.raises(Fault) as exc:
        verify_access_token(_flask_app(), _ctx(token=None))
    assert exc.value.faultcode == "Client.Auth.Missing"


def testverify_access_token_expired():
    token = _make_token(expired=True)
    with pytest.raises(Fault) as exc:
        verify_access_token(_flask_app(), _ctx(token=token))
    assert exc.value.faultcode == "Client.Auth.Expired"


def testverify_access_token_invalid_signature():
    token = _make_token(secret="wrong-secret")
    with pytest.raises(Fault) as exc:
        verify_access_token(_flask_app(), _ctx(token=token))
    assert exc.value.faultcode == "Client.Auth.Invalid"


def testverify_access_token_wrong_type():
    token = _make_token(token_type="refresh")
    with pytest.raises(Fault) as exc:
        verify_access_token(_flask_app(), _ctx(token=token))
    assert exc.value.faultcode == "Client.Auth.Invalid"


def testverify_access_token_valid():
    token = _make_token(sub="user-42")
    user_id = verify_access_token(_flask_app(), _ctx(token=token))
    assert user_id == "user-42"


def testdecode_jwt_refresh_type():
    token = _make_token(token_type="refresh")
    user_id = decode_jwt(_flask_app(), token, token_type="refresh")
    assert user_id == "user-1"
