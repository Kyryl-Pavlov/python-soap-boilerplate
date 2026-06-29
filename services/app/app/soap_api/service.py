from spyne.decorator import rpc
from spyne.model import Unicode
from spyne.service import ServiceBase

from .handlers import auth, cache, events, health, media
from .types import (
    AuthHeader,
    AuthResponse,
    CachePingResponse,
    CacheTestResponse,
    EventListResponse,
    EventResponse,
    HealthResponse,
    MediaResponse,
    RegisterResponse,
)


def make_soap_service(flask_app):
    class SoapService(ServiceBase):
        _in_header = AuthHeader

        @rpc(_returns=HealthResponse)
        def get_health(ctx):
            return health.get_health(flask_app, ctx)

        @rpc(Unicode, Unicode, _returns=RegisterResponse)
        def register(ctx, email, password):
            return auth.register(flask_app, ctx, email, password)

        @rpc(Unicode, Unicode, _returns=AuthResponse)
        def login(ctx, email, password):
            return auth.login(flask_app, ctx, email, password)

        @rpc(Unicode, _returns=AuthResponse)
        def refresh_token(ctx, refresh_token):
            return auth.refresh_token(flask_app, ctx, refresh_token)

        @rpc(Unicode, Unicode, _returns=EventResponse)
        def publish_event(ctx, event_type, payload):
            return events.publish_event(flask_app, ctx, event_type, payload)

        @rpc(_returns=EventListResponse)
        def list_events(ctx):
            return events.list_events(flask_app, ctx)

        @rpc(Unicode, Unicode, Unicode, _returns=MediaResponse)
        def upload_media(ctx, filename, file_data_b64, content_type):
            return media.upload_media(
                flask_app, ctx, filename, file_data_b64, content_type
            )

        @rpc(Unicode, _returns=MediaResponse)
        def get_media_url(ctx, media_id):
            return media.get_media_url(flask_app, ctx, media_id)

        @rpc(_returns=CachePingResponse)
        def cache_ping(ctx):
            return cache.cache_ping(flask_app, ctx)

        @rpc(Unicode, Unicode, _returns=CacheTestResponse)
        def cache_test(ctx, key, value):
            return cache.cache_test(flask_app, ctx, key, value)

    return SoapService
