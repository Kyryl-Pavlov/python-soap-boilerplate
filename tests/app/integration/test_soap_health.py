from tests.app.integration.conftest import get_text, parse_soap


def test_get_health_returns_ok(soap):
    r = soap("get_health")
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "status") == "ok"
    assert get_text(el, "timestamp") is not None
