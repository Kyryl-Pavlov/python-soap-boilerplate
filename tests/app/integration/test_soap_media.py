import base64
from unittest.mock import patch

from tests.app.integration.conftest import (
    get_fault_code,
    get_text,
    is_fault,
    parse_soap,
)

_SAMPLE_B64 = base64.b64encode(b"fake image bytes").decode()


def test_upload_media_success(soap, access_token):
    with (
        patch(
            "app.services.aws_s3_service.upload_file",
            return_value="media/user/test.jpg",
        ),
        patch(
            "app.services.aws_s3_service.get_presigned_url",
            return_value="https://s3.example.com/test.jpg",
        ),
    ):
        r = soap(
            "upload_media",
            f"<filename>test.jpg</filename>"
            f"<file_data_b64>{_SAMPLE_B64}</file_data_b64>"
            f"<content_type>image/jpeg</content_type>",
            access_token=access_token,
        )
    assert r.status_code == 200
    el = parse_soap(r)
    assert get_text(el, "media_id") is not None
    assert get_text(el, "url") == "https://s3.example.com/test.jpg"


def test_upload_media_disallowed_extension(soap, access_token):
    r = soap(
        "upload_media",
        f"<filename>malware.exe</filename>"
        f"<file_data_b64>{_SAMPLE_B64}</file_data_b64>"
        f"<content_type>application/octet-stream</content_type>",
        access_token=access_token,
    )
    assert is_fault(r)


def test_upload_media_no_auth(soap):
    r = soap(
        "upload_media",
        f"<filename>test.jpg</filename>"
        f"<file_data_b64>{_SAMPLE_B64}</file_data_b64>"
        f"<content_type>image/jpeg</content_type>",
    )
    assert is_fault(r)
    assert get_fault_code(r) == "Client.Auth.Missing"


def test_get_media_url_not_found(soap, access_token):
    import uuid

    r = soap(
        "get_media_url",
        f"<media_id>{uuid.uuid4()}</media_id>",
        access_token=access_token,
    )
    assert is_fault(r)
