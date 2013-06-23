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

    def __init__(self, login_manager, resume_builder):
        Thread.__init__(self)
        Router.__init__(self)
        self._template_vars = {}
        self.login_manager = login_manager
        self.resume_builder = resume_builder

    #================================================================================
    # Private/Protected
    #================================================================================
    def _login(self, username, password):
        self.login_manager.on_login(username, password)

    #================================================================================
    # Thread Interface
    #================================================================================
    def run(self):
        run(host=self.host, port=self.port, quiet=True)

    #================================================================================
    # Route Interface
    #================================================================================
    def handle_index(self):
        index = jinja_env.get_template("index.html")
        return index.render(self._template_vars)

    def web_refresh(self):
        self._template_vars["resume"] = self.resume_builder.get_html_resume()
        self._template_vars["users"] = self.login_manager.get_users()
        return self.handle_index()

    def handle_login(self):
        login = jinja_env.get_template("login.html")
        return login.render()

    def handle_do_login(self, username, password):
        self._login(username, password)
