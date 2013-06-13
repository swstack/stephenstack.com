from bottle import run
from controller.routes import Router
from util.paths import HTTP_TEMPLATES
import jinja2
import logging

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(HTTP_TEMPLATES),
                               autoescape=True)

logger = logging.getLogger("webserver")


class WebServer(Router):
    port = 8080
    host = "localhost"

    def __init__(self):
        Router.__init__(self)
        self.template_vars = {}

    def serve_forever(self):
        run(host=self.host, port=self.port, quiet=True)
