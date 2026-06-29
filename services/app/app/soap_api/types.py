from spyne.model import Array, Boolean, ComplexModel, Integer, Unicode


class AuthHeader(ComplexModel):
    __namespace__ = "urn:flask-soap-boilerplate"

    class Attributes(ComplexModel.Attributes):
        min_occurs = 0

    access_token = Unicode


class SoapResponse(ComplexModel):
    success = Boolean
    message = Unicode


# --- Data payloads ---


class HealthData(ComplexModel):
    status = Unicode
    timestamp = Unicode


class AuthData(ComplexModel):
    access_token = Unicode
    refresh_token = Unicode


class EventItem(ComplexModel):
    id = Unicode
    sqs_message_id = Unicode
    type = Unicode
    payload = Unicode
    status = Unicode
    created_at = Unicode
    processed_at = Unicode


class EventData(ComplexModel):
    message_id = Unicode


class EventListData(ComplexModel):
    items = Array(EventItem)


class MediaData(ComplexModel):
    media_id = Unicode
    url = Unicode
    expires_in = Integer


class CachePingData(ComplexModel):
    available = Boolean


class CacheTestData(ComplexModel):
    matched = Boolean
    key = Unicode
    stored_value = Unicode
    ttl = Integer


# --- Unified responses ---


class HealthResponse(SoapResponse):
    data = HealthData


class RegisterResponse(SoapResponse):
    pass


class AuthResponse(SoapResponse):
    data = AuthData


class EventResponse(SoapResponse):
    data = EventData


class EventListResponse(SoapResponse):
    data = EventListData


class MediaResponse(SoapResponse):
    data = MediaData


class CachePingResponse(SoapResponse):
    data = CachePingData


class CacheTestResponse(SoapResponse):
    data = CacheTestData
