import base64
import uuid
from io import BytesIO

from spyne.error import Fault

import app.services.aws_s3_service as s3
from app.extensions import db
from app.models.media import Media
from app.utils.auth import verify_access_token

from ..types import MediaData, MediaResponse

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "mp4", "mov"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_media(flask_app, ctx, filename, file_data_b64, content_type):
    user_id = verify_access_token(flask_app, ctx)

    if not filename:
        raise Fault("Client", "Filename is required")

    if not allowed_file(filename):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise Fault("Client", f"File type not allowed. Permitted: {allowed}")

    try:
        file_bytes = base64.b64decode(file_data_b64)
    except Exception:
        raise Fault("Client", "file_data_b64 must be valid base64") from None

    with flask_app.app_context():
        try:
            s3_key = s3.upload_file(BytesIO(file_bytes), user_id, filename)
        except Exception as e:
            flask_app.logger_adapter.log(
                "upload_media failed",
                level=flask_app.logger_adapter.Level.ERROR,
                data={"user_id": user_id},
                exc=e,
            )
            raise Fault("Server", "File upload failed") from e

        try:
            record = Media(user_id=uuid.UUID(user_id), content_key=s3_key)
            db.session.add(record)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise Fault("Server", "Failed to save file record") from None

        try:
            signed_url = s3.get_presigned_url(s3_key)
        except Exception:
            raise Fault("Server", "Failed to generate URL") from None

        return MediaResponse(
            success=True,
            message="",
            data=MediaData(media_id=str(record.id), url=signed_url, expires_in=3600),
        )


def get_media_url(flask_app, ctx, media_id):
    user_id = verify_access_token(flask_app, ctx)

    with flask_app.app_context():
        try:
            record = db.session.get(Media, uuid.UUID(media_id))
        except ValueError:
            raise Fault("Client", "Invalid media ID") from None

        if not record or str(record.user_id) != user_id:
            raise Fault("Client", "Not found")

        try:
            return MediaResponse(
                success=True,
                message="",
                data=MediaData(
                    media_id=str(record.id),
                    url=s3.get_presigned_url(record.content_key),
                    expires_in=3600,
                ),
            )
        except Exception:
            raise Fault("Server", "Failed to generate URL") from None
