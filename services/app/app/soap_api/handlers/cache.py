from spyne.error import Fault

from app.utils.auth import verify_access_token

from ..types import CachePingData, CachePingResponse, CacheTestData, CacheTestResponse


def cache_ping(flask_app, ctx):
    with flask_app.app_context():
        cache = flask_app.cache
        return CachePingResponse(
            success=True,
            message="",
            data=CachePingData(available=bool(cache and cache.ping())),
        )


def cache_test(flask_app, ctx, key, value):
    verify_access_token(flask_app, ctx)

    if not key or not value:
        raise Fault("Client", "Key and value are required")

    with flask_app.app_context():
        cache = flask_app.cache
        if not cache:
            raise Fault("Server", "Cache is not configured")

        try:
            cache.set(key, value, ttl=60)
            stored = cache.get(key)
            remaining_ttl = cache.ttl(key)
            cache.delete(key)
        except Exception as e:
            flask_app.logger_adapter.log(
                "cache_test failed", level=flask_app.logger_adapter.Level.ERROR, exc=e
            )
            raise Fault("Server", "Cache operation failed") from e

        return CacheTestResponse(
            success=True,
            message="",
            data=CacheTestData(
                matched=stored == value,
                key=key,
                stored_value=str(stored) if stored is not None else None,
                ttl=remaining_ttl,
            ),
        )
