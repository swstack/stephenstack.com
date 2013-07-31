from apiclient.discovery import build
from app.controller.login import AuthCodeException, AccessTokenException
from beaker.middleware import SessionMiddleware
from threading import Thread
import bottle
import json
import logging
import random
import string

appcore = None
PATH_CLIENT_SECRETS = None

GAPI = build('plus', 'v1')

logger = logging.getLogger("webserver")


def _json_response(body, status):
    response = bottle.Response(body=json.dumps(body), status=status)
    response.set_header("Content-Type", "application/json")
    return response


class Server(Thread):
    #================================================================================
    # Construction
    #================================================================================
    def __init__(self, resource_manager,
                       template_builder,
                       login_manager,
                       host="0.0.0.0",
                       port=8080,
                       session_options=None):
        Thread.__init__(self)

        # Save dependencies ---------------------------------------------------------
        self._resource_manager = resource_manager
        self._template_builder = template_builder
        self._login_manager = login_manager
        self._host = host
        self._port = port
        self._session_options = session_options or \
            {
             'session.type': 'file',
             'session.cookie_expires': 300,
             'session.data_dir': self._resource_manager.get_fs_resource_path("store"),
             'session.auto': True
            }

        # Internal state ------------------------------------------------------------
        self._static_root = None

        # Create and route WSGI Bottle application ----------------------------------
        self._bottle_app = bottle.Bottle()
        self._route_app(self._bottle_app)

    def run(self):
        bottle.run(
            app=SessionMiddleware(self._bottle_app, self._session_options),
            host=self._host,
            port=self._port,
        )

    #================================================================================
    # Internal
    #================================================================================
    def _route_app(self, app):
        app.route("/", method="GET", callback=self.index)
        app.route('/static/<filepath:path>', method="GET", callback=self.static)
        app.route("/login/<state>", method="POST", callback=self.login)
        app.route("/logout", method="POST", callback=self.logout)

    def _get_static_root(self):
        if not self._static_root:
            self._static_root = self._resource_manager.get_fs_resource_root()
        return self._static_root

    #================================================================================
    # Routes
    #================================================================================
    def static(self, filepath):
        return bottle.static_file(filepath, root=self._get_static_root())

    def login(self, state):
        """Exchange the one-time authorization code for a token and
        store the token in the session."""
        # Ensure that the request is not a forgery and that the user sending
        # this connect request is the expected user.
        session = bottle.request.environ.get('beaker.session')
        state_request = state
        state_session = session.get("state", 1)
        if state_request != state_session:
            return _json_response('Invalid state parameter.', 401)

        # TODO: this is a best practice apparently
#        del session['state']

        gapi_one_time_auth_code = bottle.request.body.read()

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

    def logout(self):
        """Revoke current user's token and reset their session."""
        session = bottle.request.environ.get('beaker.session')
        self._login_manager.logout(session)
        return _json_response("Successfully disconnected", 200)

    def index(self):
        print "INDEX"
        session = bottle.request.environ.get('beaker.session')
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for x in xrange(32))
        logger.info("Saving state key for session: %s", state)
        session['state'] = state
        session.save()

        template_vars = {
              "resume": "",
              "STATE": unicode(state)
        }
        return self._template_builder.get_index(template_vars)
