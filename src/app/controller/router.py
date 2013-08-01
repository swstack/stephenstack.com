from apiclient.discovery import build
from app.controller.login import AuthCodeException, AccessTokenException
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig
import json
import logging
import random
import string

GAPI = build('plus', 'v1')

logger = logging.getLogger("webserver")


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
        if not self._static_root:
            self._static_root = self._resource_manager.get_fs_resource_root()
        return self._static_root

    #================================================================================
    # Public
    #================================================================================
    def get_wsgi_app(self):
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
        session = request.session
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for x in xrange(32))
        session['state'] = state

        template_vars = {
              "resume": "",
              "STATE": unicode(state)
        }
        return Response(self._template_builder.get_index(template_vars))

    def login(self, request):
        # Ensure that the request is not a forgery and that the user sending
        # this connect request is the expected user.
        session = request.session
        request_params = json.loads(request.body)
        state_request = request_params["state"]
        state_session = session.get("state", 1)
        if state_request != state_session:
            return _json_response('Invalid state parameter.', 401)

        # TODO: this is a best practice apparently
#        del session['state']

        gapi_one_time_auth_code = request_params["auth_code"]

        try:
            result = self._login_manager.login(gapi_one_time_auth_code, session, GAPI)
            bigger_img_url = result["image"]["url"].replace("sz=50", "sz=200")
            result["image"]["url"] = bigger_img_url
        except AuthCodeException:
            return _json_response("Auth code exception", 401)
        except AccessTokenException:
            return _json_response("Access token exception", 401)
        else:
            return _json_response(result, 200)
