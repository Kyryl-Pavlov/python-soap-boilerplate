from tests.app.integration.conftest import (
    get_fault_code,
    get_text,
    is_fault,
    parse_soap,
)


def test_register_success(soap):
    r = soap("register", "<email>new@example.com</email><password>Pass123!</password>")
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "success") == "true"


def test_register_duplicate_email(soap):
    soap("register", "<email>dup@example.com</email><password>Pass123!</password>")
    r = soap("register", "<email>dup@example.com</email><password>Pass123!</password>")
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "success") == "false"
    assert "already registered" in (get_text(el, "message") or "").lower()


def test_login_success(soap):
    soap("register", "<email>login@example.com</email><password>Pass123!</password>")
    r = soap("login", "<email>login@example.com</email><password>Pass123!</password>")
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "access_token") is not None
    assert get_text(el, "refresh_token") is not None


def test_login_invalid_credentials(soap):
    r = soap("login", "<email>nobody@example.com</email><password>wrong</password>")
    assert is_fault(r)
    assert get_fault_code(r) == "Client.Auth.Invalid"


def test_refresh_token_success(soap):
    soap("register", "<email>ref@example.com</email><password>Pass123!</password>")
    r = soap("login", "<email>ref@example.com</email><password>Pass123!</password>")
    el = parse_soap(r)
    rt = get_text(el, "refresh_token")

    r2 = soap("refresh_token", f"<refresh_token>{rt}</refresh_token>")
    assert r2.status_code == 200
    el2 = parse_soap(r2)
    assert get_text(el2, "access_token") is not None


def test_refresh_token_wrong_type(soap, access_token):
    r = soap("refresh_token", f"<refresh_token>{access_token}</refresh_token>")
    assert is_fault(r)
    assert get_fault_code(r) == "Client.Auth.Invalid"
