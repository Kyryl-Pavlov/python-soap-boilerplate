from unittest.mock import MagicMock

from tests.app.integration.conftest import (
    get_fault_code,
    get_text,
    is_fault,
    parse_soap,
)


def test_cache_ping_unavailable(soap):
    r = soap("cache_ping")
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "available") == "false"


def test_cache_ping_available(soap, app):
    mock = MagicMock()
    mock.ping.return_value = True
    app.cache = mock
    try:
        r = soap("cache_ping")
        assert r.status_code == 200
        el = parse_soap(r)
        assert get_text(el, "available") == "true"
    finally:
        app.cache = None


def test_cache_test_success(soap, access_token, app):
    mock = MagicMock()
    mock.get.return_value = "hello"
    mock.ttl.return_value = 59
    app.cache = mock
    try:
        r = soap(
            "cache_test",
            "<key>test-key</key><value>hello</value>",
            access_token=access_token,
        )
        assert r.status_code == 200
        el = parse_soap(r)
        assert get_text(el, "success") == "true"
        assert get_text(el, "stored_value") == "hello"
        mock.set.assert_called_once_with("test-key", "hello", ttl=60)
        mock.delete.assert_called_once_with("test-key")
    finally:
        app.cache = None


def test_cache_test_no_auth(soap):
    r = soap("cache_test", "<key>k</key><value>v</value>")
    assert is_fault(r)
    assert get_fault_code(r) == "Client.Auth.Missing"


def test_cache_test_not_configured(soap, access_token):
    r = soap(
        "cache_test",
        "<key>k</key><value>v</value>",
        access_token=access_token,
    )
    assert is_fault(r)
    assert get_fault_code(r) == "Server"
