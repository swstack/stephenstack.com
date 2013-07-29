from apiclient.discovery import build
from beaker.middleware import SessionMiddleware
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    flow_from_clientsecrets
from threading import Thread
import bottle
import httplib2
import json
import logging
import random
import string

appcore = None
PATH_CLIENT_SECRETS = None

SERVICE = build('plus', 'v1')

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
        self._path_client_secrets = \
            self._resource_manager.get_fs_resource_path("client_secrets.json")

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

        # Normally, the state is a one-time token; however, in this example,
        # we want the user to be able to connect and disconnect
        # without reloading the page.  Thus, for demonstration, we don't
        # implement this best practice.
        # del session['state']

        code = bottle.request.body.read()

        try:
            # Upgrade the authorization code into a credentials object
            self._login_manager.login()

            oauth_flow = flow_from_clientsecrets(self._path_client_secrets, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            return _json_response("Failed to upgrade the auth code.", 401)

        # An ID Token is a cryptographically-signed JSON object encoded in base 64.
        # Normally, it is critical that you validate an ID Token before you use it,
        # but since you are communicating directly with Google over an
        # intermediary-free HTTPS channel and using your Client Secret to
        # authenticate yourself to Google, you can be confident that the token you
        # receive really comes from Google and is valid. If your server passes the
        # ID Token to other components of your app, it is extremely important that
        # the other components validate the token before using it.
        gplus_id = credentials.id_token['sub']

        # Store the access token in the session for later use.
        session['credentials'] = credentials
        session['gplus_id'] = gplus_id

        # get some data about the user
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            # Get a list of people that this user has shared with this app.
            my_circles = SERVICE.people().list(userId='me', collection='visible').execute(http=http)
            me = SERVICE.people().get(userId="me").execute(http=http)
        except AccessTokenRefreshError:
            return _json_response('Failed to refresh access token.', 500)

        bigger_img_url = me["image"]["url"].replace("sz=50", "sz=200")
        me["image"]["url"] = bigger_img_url
        return _json_response(me, 200)

    def logout(self):
        """Revoke current user's token and reset their session."""
        session = bottle.request.environ.get('beaker.session')

        # Only disconnect a connected user.
        credentials = session.get('credentials')
        if credentials is None:
            return _json_response("Current user not connected.", 401)

        # Execute HTTP GET request to revoke current token.
        access_token = credentials.access_token
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]

        if result['status'] == '200':
            # Reset the user's session.
            del session['credentials']
            return _json_response("Successfully disconnected", 200)
        else:
            # For whatever reason, the given token was invalid.
            return _json_response("Failed to revoke token for given user.", 400)

    def index(self):
        session = bottle.request.environ.get('beaker.session')
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for x in xrange(32))
        logger.info("Saving state key for session: %s", state)
        session['state'] = state
        session.save()

        template_vars = {
#              "resume": self._resume_builder.get_resume(),
              "CLIENT_ID": unicode(self._login_manager.get_client_id()),
              "STATE": unicode(state)
        }
        return self._template_builder.get_index(template_vars)
