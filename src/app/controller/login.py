from apiclient.discovery import build
from app.model.model import User, Message
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    flow_from_clientsecrets
import httplib2
import logging

logger = logging.getLogger("login")


class GAPIException(Exception):
    def __init__(self, msg, status_code=404):
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return repr("%s -- %s" % (self.msg, self.status_code))


class LoginManager(object):
    def __init__(self, database, resource_manager, platform):
        self._resource_manager = resource_manager
        self._database = database
        self._platform = platform
        self._path_client_secrets = \
            self._resource_manager.get_fs_resource_path("client_secrets.json")
        self._gapi = None

    def start(self):
        self._gapi = build('plus', 'v1')

    #===========================================================================
    # Internal
    #===========================================================================
    def _create_and_update_local_user_if_needed(self, user_data):
        gapi_id = user_data["id"]

        session_db = self._database.get_session()

        user = self._database.get_user(gapi_id=gapi_id)

        thumbnail_url = user_data["image"]["url"]
        profile_pic_url = user_data["image"]["url"].replace("sz=50", "sz=200")

        if user:
            logger.info("User already exists locally.")
            user.thumbnail_url = thumbnail_url
            user.profile_pic_url = profile_pic_url
        else:
            logger.info("Creating user %s", gapi_id)
            user = User(
                        gapi_id=gapi_id,
                        name=user_data["displayName"],
                        thumbnail_url=thumbnail_url,
                        profile_pic_url=profile_pic_url,
                        )
            session_db.add(user)

            intro_msg = Message(
                                sender=self._database.\
                                            get_user(self._database.my_gapi_id).id,
                                receiver=user.id,
                                msg_data="Welcome to my site!",
                                datetime_sent=self._platform.time_datetime_now(),
                                )
            session_db.add(intro_msg)

        # save
        session_db.commit()
        return user

    #===========================================================================
    # Public
    #===========================================================================
    def login(self, session, state, auth_code):
        if state != session.get("state", 1):
            GAPIException("Invalid state parameter", 401)

        # TODO: this is a best practice apparently
#        del session['state']

        try:
            # Upgrade the authorization code into a credentials object

            oauth_flow = flow_from_clientsecrets(self._path_client_secrets,
                                                 scope='')
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
        gapi_id = credentials.id_token['sub']

        # Store the access token in the session for later use.
        session['credentials'] = credentials
        session['gapi_id'] = gapi_id

        # get some data about the user
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)

            # Get specific user data
            user_data = self._gapi.people().get(userId="me").execute(http=http)

        except AccessTokenRefreshError:
            raise GAPIException("Access token expcetion", 401)

        # create local user if needed
        user = self._create_and_update_local_user_if_needed(user_data)

        return user

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
