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
    def handle_home(self):
        home = jinja_env.get_template("home.html")
        return home.render()

    def handle_profile(self):
        profile = jinja_env.get_template("profile.html")
        resume = self.resume_builder.get_pdf_resume()
        return profile.render({"resume": resume})

    def handle_da_codes(self):
        codes = jinja_env.get_template("codes.html")
        return codes.render()

    def handle_playground(self):
        playground = jinja_env.get_template("playground.html")
        return playground.render({"users": self.login_manager.get_users()})

    def handle_login(self):
        login = jinja_env.get_template("login.html")
        return login.render()

    def handle_do_login(self, username, password):
        self._login(username, password)
