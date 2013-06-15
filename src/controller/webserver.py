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

    def __init__(self, login_manager):
        Thread.__init__(self)
        Router.__init__(self)
        self.template_vars = {}
        self.login_manager = login_manager

    #================================================================================
    # Private/Protected
    #================================================================================
    def _refresh_template_vars(self):
        self.template_vars["users"] = self.login_manager.get_users()

    #================================================================================
    # Thread Interface
    #================================================================================
    def run(self):
        run(host=self.host, port=self.port, quiet=True)

    #================================================================================
    # Route Interface
    #================================================================================
    def handle_index(self):
        self._refresh_template_vars()
        index = jinja_env.get_template("index.html")
        return index.render(self.template_vars)

    def handle_login(self, username, password):
        self.login_manager.on_login(username, password)
        self._refresh_template_vars()
