from datetime import datetime, timezone

from ..types import HealthData, HealthResponse


def get_health(flask_app, ctx):
    return HealthResponse(
        success=True,
        message="",
        data=HealthData(
            status="ok",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
