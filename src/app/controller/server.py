from apiclient.discovery import build
from beaker.middleware import SessionMiddleware
from app.controller.login import AuthCodeException, AccessTokenException
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
    HOST = "0.0.0.0"
    PORT = 8080

    #================================================================================
    # Construction
    #================================================================================
    def __init__(self, resource_manager,
                       router,
                       template_builder,
                       login_manager,
                       resume_builder):
        Thread.__init__(self)

        # Save dependencies ---------------------------------------------------------
        self._router = router
        self._resource_manager = resource_manager
        self._template_builder = template_builder
        self._login_manager = login_manager
        self._resume_builder = resume_builder

        # Register with the router --------------------------------------------------
        self._router.register_server(self)

        # Internal state ------------------------------------------------------------
        self._static_root = None

    def run(self):
        SESSION_OPTS = {
            'session.type': 'file',
            'session.cookie_expires': 300,
            'session.data_dir': self._resource_manager.get_fs_resource_path("store"),
            'session.auto': True
            }
        bottle.run(app=SessionMiddleware(bottle.app(), SESSION_OPTS),
                   host=self.HOST,
                   port=self.PORT,
                   quiet=False)

    #================================================================================
    # Internal
    #================================================================================

    #================================================================================
    # Public
    #================================================================================
    def get_static_root(self):
        if not self._static_root:
            self._static_root = self._resource_manager.get_fs_resource_root()
        return self._static_root

    def signin(self, state):
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
        session = bottle.request.environ.get('beaker.session')
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for x in xrange(32))
        logger.info("Saving state key for session: %s", state)
        session['state'] = state
        session.save()

        template_vars = {
#              "resume": self._resume_builder.get_resume(),
              "STATE": unicode(state)
        }
        return self._template_builder.get_index(template_vars)
