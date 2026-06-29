from flask_jwt_extended import create_access_token, create_refresh_token
from spyne.error import Fault

from app.extensions import db
from app.models.user import User
from app.utils.auth import decode_jwt

from ..types import AuthData, AuthResponse, RegisterResponse


def register(flask_app, ctx, email, password):
    if not email or not password:
        return RegisterResponse(
            success=False, message="Email and password are required"
        )

    email = email.strip().lower()

    with flask_app.app_context():
        if User.query.filter_by(email=email).first():
            return RegisterResponse(success=False, message="Email already registered")
        try:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flask_app.logger_adapter.log(
                "register failed", level=flask_app.logger_adapter.Level.ERROR, exc=e
            )
            return RegisterResponse(success=False, message="Registration failed")

    return RegisterResponse(success=True, message="User registered successfully")


def login(flask_app, ctx, email, password):
    if not email or not password:
        raise Fault("Client", "Email and password are required")

    email = email.strip().lower()

    with flask_app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                raise Fault("Client.Auth.Invalid", "Invalid credentials")

            return AuthResponse(
                success=True,
                message="",
                data=AuthData(
                    access_token=create_access_token(identity=str(user.id)),
                    refresh_token=create_refresh_token(identity=str(user.id)),
                ),
            )
        except Fault:
            raise
        except Exception as e:
            flask_app.logger_adapter.log(
                "login failed", level=flask_app.logger_adapter.Level.ERROR, exc=e
            )
            raise Fault("Server", "Login failed") from e


def refresh_token(flask_app, ctx, token):
    if not token:
        raise Fault("Client.Auth.Missing", "Refresh token is required")

    with flask_app.app_context():
        user_id = decode_jwt(flask_app, token, token_type="refresh")
        return AuthResponse(
            success=True,
            message="",
            data=AuthData(
                access_token=create_access_token(identity=user_id),
                refresh_token=None,
            ),
        )
