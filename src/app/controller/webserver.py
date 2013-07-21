from apiclient.discovery import build
from beaker.middleware import SessionMiddleware
from bottle import route, app, static_file, get, request, post, run
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    flow_from_clientsecrets
from threading import Thread
import json

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './data',
    'session.auto': True
}

app = SessionMiddleware(app(), session_opts)

HOST = "localhost"
PORT = 8080

appcore = None
PATH_CLIENT_SECRETS = None

SERVICE = build('plus', 'v1')


class Webserver(Thread):
    def __init__(self, _appcore, resource_manager):
        Thread.__init__(self)
        global appcore, PATH_CLIENT_SECRETS
        appcore = _appcore
        PATH_CLIENT_SECRETS = \
            resource_manager.get_fs_resource_path("client_secrets.json")
        self._resource_manager = resource_manager

    def run(self):
        run(host=HOST, port=PORT, quiet=True)


@get('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root=appcore.get_static_root())


@post("/login")
def login():
    params = request.params
    result = appcore.login(params["username"], params["password"])
    return json.dumps({"result": result})


@route("/")
def index():
    return appcore.get_index()


@route("/connect")
def connect():
    """Exchange the one-time authorization code for a token and
    store the token in the session."""
    # Ensure that the request is not a forgery and that the user sending
    # this connect request is the expected user.
    session = request.environ.get('beaker.session')

    if request.args.get('state', '') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Normally, the state is a one-time token; however, in this example,
    # we want the user to be able to connect and disconnect
    # without reloading the page.  Thus, for demonstration, we don't
    # implement this best practice.
    # del session['state']

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets(PATH_CLIENT_SECRETS, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session['credentials'] = credentials
    session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Successfully connected user.', 200))
    response.headers['Content-Type'] = 'application/json'
    return response
