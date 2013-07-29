"""
session.query(MyClass).filter(MyClass.name == 'some name', MyClass.id > 5)
"""
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    flow_from_clientsecrets
import httplib2
import json


class AuthCodeException(Exception):
    pass


class AccessTokenException(Exception):
    pass


class UserNotConnectedException(Exception):
    pass


class LoginManager(object):
    def __init__(self, database, resource_manager):
        self._resource_manager = resource_manager
        self.database = database
        self._client_secrets = None
        self._path_client_secrets = \
            self._resource_manager.get_fs_resource_path("client_secrets.json")

    def start(self):
        self._load_client_secrets()

    #================================================================================
    # Internal
    #================================================================================
    def _load_client_secrets(self):
        if not self._client_secrets:
            raw = open(self._resource_manager.\
                       get_fs_resource_path("client_secrets.json"), "r").read()
            self._client_secrets = json.loads(raw)

    #================================================================================
    # Public
    #================================================================================
    def get_client_id(self):
        return self._client_secrets["web"]["client_id"]

    def login(self, gapi_one_time_auth_code, session, GAPI):
        try:
            # Upgrade the authorization code into a credentials object

            oauth_flow = flow_from_clientsecrets(self._path_client_secrets, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(gapi_one_time_auth_code)
        except FlowExchangeError:
            raise AuthCodeException()

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

            # Get a list of people that this user has shared with this app
            my_circles = GAPI.people().list(userId='me', collection='visible').execute(http=http)

            # Get specific user data
            me = GAPI.people().get(userId="me").execute(http=http)

            result = dict(me, **my_circles)
        except AccessTokenRefreshError:
            raise AccessTokenException()

        return result

    def logout(self, session):
        # Only disconnect a connected user.
        credentials = session.get('credentials')
        if credentials is None:
            raise UserNotConnectedException()

        # Execute HTTP GET request to revoke current token.
        access_token = credentials.access_token
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]

        if result['status'] == '200':
            # Reset the user's session.
            del session['credentials']
        else:
            # For whatever reason, the given token was invalid.
            raise Exception()
