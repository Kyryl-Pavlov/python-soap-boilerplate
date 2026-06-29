from unittest.mock import patch

from tests.app.integration.conftest import (
    get_fault_code,
    get_text,
    is_fault,
    parse_soap,
)


def test_publish_event_success(soap, access_token):
    with patch("app.services.aws_sqs_service.send_event", return_value="msg-123"):
        r = soap(
            "publish_event",
            '<event_type>user.created</event_type><payload>{"id": "1"}</payload>',
            access_token=access_token,
        )
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "message_id") == "msg-123"


def test_publish_event_no_auth(soap):
    r = soap("publish_event", "<event_type>test</event_type><payload>{}</payload>")
    assert is_fault(r)
    assert get_fault_code(r) == "Client.Auth.Missing"


def test_publish_event_expired_token(soap):
    expired = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiJ1c2VyMSIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE2MDAwMDAwMDB9"
        ".signature"
    )
    r = soap(
        "publish_event",
        "<event_type>test</event_type><payload>{}</payload>",
        access_token=expired,
    )
    assert is_fault(r)
    assert get_fault_code(r) in ("Client.Auth.Expired", "Client.Auth.Invalid")


def test_list_events_success(soap, access_token):
    r = soap("list_events", access_token=access_token)
    assert r.status_code == 200
    assert not is_fault(r)
