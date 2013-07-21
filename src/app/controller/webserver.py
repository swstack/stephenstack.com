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


class Webserver(Thread):
    HOST = "0.0.0.0"
    PORT = 8080

    def __init__(self, _appcore, resource_manager):
        Thread.__init__(self)
        global appcore, PATH_CLIENT_SECRETS
        appcore = _appcore
        PATH_CLIENT_SECRETS = \
            resource_manager.get_fs_resource_path("client_secrets.json")
        self._resource_manager = resource_manager

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


@bottle.get('/static/<filepath:path>')
def static(filepath):
    return bottle.static_file(filepath, root=appcore.get_static_root())


@bottle.post("/login")
def login():
    params = bottle.request.params
    result = appcore.login(params["username"], params["password"])
    return json.dumps({"result": result})


@bottle.post("//connect")
def connect():
    """Exchange the one-time authorization code for a token and
    store the token in the session."""
    # Ensure that the request is not a forgery and that the user sending
    # this connect request is the expected user.
    session = bottle.request.environ.get('beaker.session')

    state_request = bottle.request.params.get('state', 0)
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

        oauth_flow = flow_from_clientsecrets(PATH_CLIENT_SECRETS, scope='')
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

    stored_credentials = session.get('credentials')
    stored_gplus_id = session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        return _json_response("Current user already connected.", 200)

    # Store the access token in the session for later use.
    session['credentials'] = credentials
    session['gplus_id'] = gplus_id
    return _json_response("Successfully connected user.", 200)


@bottle.post('/disconnect')
def disconnect():
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


@bottle.get('//people')
def people():
    """Get list of people user has shared with this app."""
    session = bottle.request.environ.get('beaker.session')

    credentials = session.get('credentials')
    # Only fetch a list of people for connected users.
    if credentials is None:
        return _json_response("Current user not connected.", 401)
    try:
        # Create a new authorized API client.
        http = httplib2.Http()
        http = credentials.authorize(http)
        # Get a list of people that this user has shared with this app.
        google_request = SERVICE.people().list(userId='me', collection='visible')
        result = google_request.execute(http=http)
        return _json_response(result, 200)
    except AccessTokenRefreshError:
        return _json_response('Failed to refresh access token.', 500)


@bottle.get("/")
def index():
    session = bottle.request.environ.get('beaker.session')
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
    logger.info("Saving state key for session: %s", state)
    session['state'] = state
    session.save()
    return appcore.get_index(STATE=state)
