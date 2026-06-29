import os
import time

from flask import Flask, g, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from . import models  # noqa: F401 — registers models with SQLAlchemy for migrations
from .config import config
from .extensions import db, jwt, migrate
from .logging.cloudwatch_logger import CloudWatchLogger
from .logging.logger import AppLogger, ConsoleLogger
from .logging.loki_logger import LokiLogger
from .logging.sentry_logger import SentryLogger
from .services.cache_service import CacheService


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    loggers = [ConsoleLogger(debug=app.config.get("DEBUG", False))]

    sentry_dsn = app.config.get("SENTRY_DSN")
    if sentry_dsn:
        loggers.append(SentryLogger(dsn=sentry_dsn, environment=config_name))

    cw_log_group = app.config.get("CLOUDWATCH_LOG_GROUP")
    if cw_log_group:
        try:
            loggers.append(
                CloudWatchLogger(
                    log_group=cw_log_group,
                    stream_name=app.config.get("CLOUDWATCH_STREAM_NAME", "app"),
                    region=app.config.get("AWS_DEFAULT_REGION", "us-east-1"),
                    aws_access_key_id=app.config.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=app.config.get("AWS_SECRET_ACCESS_KEY"),
                    endpoint_url=app.config.get("CLOUDWATCH_ENDPOINT_URL"),
                )
            )
        except Exception as e:
            app.logger.warning(f"CloudWatch logger unavailable, skipping: {e}")

    loki_url = app.config.get("LOKI_URL")
    if loki_url:
        loggers.append(
            LokiLogger(
                url=loki_url,
                labels={"app": "flask-soap-boilerplate", "env": config_name},
            )
        )

    app.logger_adapter = AppLogger(*loggers)

    redis_url = app.config.get("REDIS_URL")
    app.cache = CacheService.from_url(redis_url) if redis_url else None

    PrometheusMetrics(
        app, group_by="endpoint", default_labels={"app": "flask-soap-boilerplate"}
    )

    from .soap_api import create_soap_wsgi_app

    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app, {"/soap": create_soap_wsgi_app(app)}
    )

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.before_request
    def record_start_time():
        g.request_start = time.perf_counter()

    @app.after_request
    def log_response_time(response):
        if hasattr(g, "request_start"):
            duration_ms = round((time.perf_counter() - g.request_start) * 1000, 2)
            app.logger_adapter.log(
                "response",
                level=AppLogger.Level.INFO,
                data={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
        return response

    return app
