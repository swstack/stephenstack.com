from bottle import run
from controller.routes import Router
from util.paths import HTTP_TEMPLATES
from threading import Thread
import jinja2
import logging

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(HTTP_TEMPLATES),
                               autoescape=True)

logger = logging.getLogger("webserver")


class WebServer(Router, Thread):
    port = 8080
    host = "localhost"

    def __init__(self):
        Thread.__init__(self)
        Router.__init__(self)
        self.template_vars = {}

    #================================================================================
    # Thread Interface
    #================================================================================
    def run(self):
        run(host=self.host, port=self.port, quiet=True)

    #================================================================================
    # Public Interface
    #================================================================================
    def handle_request_get(self, request):
        """Must return"""
        index = jinja_env.get_template("index.html")
        return index.render(self.template_vars)

    def handle_request_post(self, request):
        pass
