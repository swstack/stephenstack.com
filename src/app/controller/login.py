from apiclient.discovery import build
from app.controller.router import WSGIException
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    flow_from_clientsecrets
import httplib2


class GAPIException(WSGIException):
    def __init__(self, *args, **kwargs):
        WSGIException.__init__(self, *args, **kwargs)


class LoginManager(object):
    def __init__(self, database, resource_manager):
        self._resource_manager = resource_manager
        self.database = database
        self._path_client_secrets = \
            self._resource_manager.get_fs_resource_path("client_secrets.json")
        self._gapi = build('plus', 'v1')

    def start(self):
        pass

    #================================================================================
    # Public
    #================================================================================
    def login(self, session, state, auth_code):
        if state != session.get("state", 1):
            GAPIException("Invalid state parameter", 401)

        # TODO: this is a best practice apparently
#        del session['state']

        try:
            # Upgrade the authorization code into a credentials object

            oauth_flow = flow_from_clientsecrets(self._path_client_secrets, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            raise GAPIException("Auth code exception", 401)

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
            my_circles = self._gapi.people().\
                        list(userId='me', collection='visible').execute(http=http)

            # Get specific user data
            me = self._gapi.people().get(userId="me").execute(http=http)

            result = dict(me, **my_circles)
        except AccessTokenRefreshError:
            raise GAPIException("Access token expcetion", 401)

        bigger_img_url = result["image"]["url"].replace("sz=50", "sz=200")
        result["image"]["url"] = bigger_img_url
        return result

    def logout(self, session):
        # Only disconnect a connected user.
        credentials = session.get('credentials')
        if credentials is None:
            raise GAPIException("User not connected", 401)

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
            raise GAPIException("For whatever reason, the token is invalid.")
