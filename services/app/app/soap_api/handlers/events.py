import json

from spyne.error import Fault

import app.services.aws_sqs_service as sqs
from app.models.event import Event
from app.utils.auth import verify_access_token

from ..types import (
    EventData,
    EventItem,
    EventListData,
    EventListResponse,
    EventResponse,
)


def publish_event(flask_app, ctx, event_type, payload):
    user_id = verify_access_token(flask_app, ctx)

    if not event_type or not event_type.strip():
        raise Fault("Client", "Event type is required")

    try:
        payload_dict = json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        raise Fault("Client", "Payload must be valid JSON") from None

    with flask_app.app_context():
        try:
            message_id = sqs.send_event(event_type.strip(), payload_dict)
        except Exception as e:
            flask_app.logger_adapter.log(
                "publish_event failed",
                level=flask_app.logger_adapter.Level.ERROR,
                data={"user_id": user_id},
                exc=e,
            )
            raise Fault("Server", "Failed to publish event") from e

    return EventResponse(
        success=True, message="", data=EventData(message_id=message_id)
    )


def list_events(flask_app, ctx):
    verify_access_token(flask_app, ctx)

    with flask_app.app_context():
        try:
            rows = Event.query.order_by(Event.created_at.desc()).limit(100).all()
        except Exception as e:
            flask_app.logger_adapter.log(
                "list_events failed", level=flask_app.logger_adapter.Level.ERROR, exc=e
            )
            raise Fault("Server", "Failed to fetch events") from e

        items = [
            EventItem(
                id=str(r.id),
                sqs_message_id=r.sqs_message_id,
                type=r.type,
                payload=json.dumps(r.payload) if r.payload else None,
                status=r.status,
                created_at=r.created_at.isoformat(),
                processed_at=r.processed_at.isoformat() if r.processed_at else None,
            )
            for r in rows
        ]
        return EventListResponse(
            success=True,
            message="",
            data=EventListData(items=items),
        )
