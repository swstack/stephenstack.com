from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig
import json
import logging
import random
import string

logger = logging.getLogger("webserver")


class WSGIException(Exception):
    def __init__(self, msg, status_code=404):
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return repr("%s -- %s" % (self.msg, self.status_code))


def _json_response(body, status):
    return \
        Response(
             body=json.dumps(body),
             status=status,
             headers={
                      "Content-Type": "application/json",
                      }
                 )


class Router(object):
    #================================================================================
    # Construction
    #================================================================================
    def __init__(self, resource_manager,
                       template_builder,
                       login_manager):
        # Dependencies --------------------------------------------------------------
        self._resource_manager = resource_manager
        self._template_builder = template_builder
        self._login_manager = login_manager

        # Internal state ------------------------------------------------------------
        self._static_root = None
        self._config = None
        self._app = None

    def start(self):
        # Setup Pyramid configurator
        self._config = \
            Configurator(session_factory=UnencryptedCookieSessionFactoryConfig("pwnd"))

        # Route: /index (:method:index)
        self._config.add_route("index", "/")
        self._config.add_view(self.index,
                              route_name="index",
                              request_method="GET",
                              permission="read")

        # Route: /static/<file> (:method:static)
        self._config.add_static_view(name="static",
                                     path=self._resource_manager.get_fs_resource_root())

        # Route: /login/<state> (:method:login)
        self._config.add_route("login", "/login")
        self._config.add_view(self.login,
                              route_name="login",
                              request_method="POST",
                              permission="read")
        self._app = self._config.make_wsgi_app()

        # Route: /login/<state> (:method:login)
        self._config.add_route("logout", "/logout")
        self._config.add_view(self.login,
                              route_name="logout",
                              request_method="POST",
                              permission="read")
        self._app = self._config.make_wsgi_app()

    #================================================================================
    # Internal
    #================================================================================
    def _get_static_root(self):
        """Return path to static assets/resources"""
        if not self._static_root:
            self._static_root = self._resource_manager.get_fs_resource_root()
        return self._static_root

    #================================================================================
    # Public
    #================================================================================
    def get_wsgi_app(self):
        """Return standard wsgi application,
                        http://www.python.org/dev/peps/pep-0333/
        """
        return self._app

    #================================================================================
    # Routes
    #================================================================================
    def logout(self, request):
        """Revoke current user's token and reset their session."""
        session = request.session
        self._login_manager.logout(session)
        return _json_response("Successfully disconnected", 200)

    def index(self, request):
        """Dat index"""
        session = request.session
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for _ in xrange(32))
        session['state'] = state
        template_vars = {
              "resume": "",
              "STATE": unicode(state)
        }
        return Response(self._template_builder.get_index(template_vars))

    def login(self, request):
        """Ensure that the request is not a forgery and that the user sending
        this connect request is the expected user.
        """
        unencoded_json = json.loads(request.body)
        session = request.session
        state = unencoded_json["state"]
        auth_code = unencoded_json["auth_code"]
        result = self._login_manager.login(session, state, auth_code)
        return _json_response(result, 200)
