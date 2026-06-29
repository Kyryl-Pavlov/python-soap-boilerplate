"""
E2E smoke tests — run against a fully started stack (docker-compose.ci.yml).
Each test hits real Postgres, LocalStack S3/SQS, and Redis through Nginx.
No mocks. Happy paths only — edge cases belong in integration tests.

Run:
    docker compose -f docker-compose.ci.yml up -d --wait --build
    pytest tests/app/e2e/
    docker compose -f docker-compose.ci.yml down
"""

import base64

from tests.app.e2e.conftest import get_text, is_fault, parse_body


def test_health_check(soap):
    r = soap("get_health")
    assert r.status_code == 200
    assert not is_fault(r)
    el = parse_body(r)
    assert get_text(el, "status") == "ok"
    assert get_text(el, "timestamp") is not None


def test_register_and_login(soap):
    r = soap(
        "register", "<email>smoke@ci-test.internal</email><password>Smoke1!</password>"
    )
    assert r.status_code == 200
    el = parse_body(r)
    assert get_text(el, "success") == "true"

    r2 = soap(
        "login", "<email>smoke@ci-test.internal</email><password>Smoke1!</password>"
    )
    assert r2.status_code == 200
    el2 = parse_body(r2)
    assert get_text(el2, "access_token") is not None
    assert get_text(el2, "refresh_token") is not None


def test_authenticated_list_events(soap, access_token):
    r = soap("list_events", access_token=access_token)
    assert r.status_code == 200
    assert not is_fault(r)


def test_publish_event(soap, access_token):
    r = soap(
        "publish_event",
        '<event_type>e2e.smoke</event_type><payload>{"source": "ci"}</payload>',
        access_token=access_token,
    )
    assert r.status_code == 200
    assert not is_fault(r)
    el = parse_body(r)
    assert get_text(el, "message_id") is not None


def test_media_upload_and_get_url(soap, access_token):
    file_b64 = base64.b64encode(b"e2e smoke content").decode()
    r = soap(
        "upload_media",
        f"<filename>e2e.png</filename>"
        f"<file_data_b64>{file_b64}</file_data_b64>"
        f"<content_type>image/png</content_type>",
        access_token=access_token,
    )
    assert r.status_code == 200
    assert not is_fault(r)
    el = parse_body(r)
    media_id = get_text(el, "media_id")
    assert media_id is not None
    assert get_text(el, "url") is not None

    r2 = soap(
        "get_media_url", f"<media_id>{media_id}</media_id>", access_token=access_token
    )
    assert r2.status_code == 200
    assert not is_fault(r2)
    el2 = parse_body(r2)
    assert get_text(el2, "url") is not None
