import jwt as pyjwt
from spyne.error import Fault

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"


def decode_jwt(flask_app, token: str, token_type: str = "access") -> str:
    try:
        payload = pyjwt.decode(
            token,
            flask_app.config["JWT_SECRET_KEY"],
            algorithms=[flask_app.config.get("JWT_ALGORITHM", "HS256")],
        )
        if payload.get("type") != token_type:
            raise Fault("Client.Auth.Invalid", f"Expected {token_type} token")
        return payload["sub"]
    except pyjwt.ExpiredSignatureError:
        raise Fault(
            "Client.Auth.Expired", "Token has expired — call refresh_token to renew"
        ) from None
    except pyjwt.InvalidTokenError:
        raise Fault(
            "Client.Auth.Invalid", "Token is invalid — re-login required"
        ) from None


def get_token_from_header(ctx) -> str | None:
    doc = ctx.in_document
    if doc is None:
        return None
    header = doc.find(f"{{{SOAP_ENV_NS}}}Header")
    if header is None:
        return None
    for auth_el in header:
        if auth_el.tag.split("}")[-1] == "AuthHeader":
            for child in auth_el:
                if child.tag.split("}")[-1] == "access_token":
                    return child.text
    return None


def verify_access_token(flask_app, ctx) -> str:
    token = get_token_from_header(ctx)
    if not token:
        raise Fault("Client.Auth.Missing", "Access token required in AuthHeader")
    return decode_jwt(flask_app, token, token_type="access")
