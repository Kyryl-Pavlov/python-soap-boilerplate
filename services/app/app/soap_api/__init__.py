from spyne.application import Application
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from .service import make_soap_service


def create_soap_wsgi_app(flask_app):
    service_cls = make_soap_service(flask_app)
    spyne_app = Application(
        [service_cls],
        tns="urn:flask-soap-boilerplate",
        in_protocol=Soap11(validator="soft"),
        out_protocol=Soap11(),
    )
    return WsgiApplication(spyne_app)
