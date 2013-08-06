from app.controller.login import GAPIException
from app.model.model import Resume, Message
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig
import json
import logging
import random
import string

logger = logging.getLogger("webserver")


def _json_response(body, status):
    try:
        body = json.dumps(body)
    except TypeError:
        body = ""
        logger.error("Could not serialize to JSON! -- %s", body)
    finally:
        return Response(body=body,
                        status=status,
                        headers={"Content-Type": "application/json"})


# TODO: Become more restful

class Router(object):
    #================================================================================
    # Construction
    #================================================================================
    def __init__(self, resource_manager,
                       template_builder,
                       login_manager,
                       database,
                       platform):
        # Dependencies --------------------------------------------------------------
        self._resource_manager = resource_manager
        self._template_builder = template_builder
        self._login_manager = login_manager
        self._database = database
        self._platform = platform

        # Internal state ------------------------------------------------------------
        self._static_root = None
        self._config = None
        self._app = None

    def start(self):
        # Setup Pyramid configurator
        self._config = \
            Configurator(session_factory=UnencryptedCookieSessionFactoryConfig("pwnd"))

        # Route: /static/<file> (:method:static)
        self._config.add_static_view(name="static",
                                     path=self._resource_manager.get_fs_resource_root())

        # Route: /login (:method:login)
        self._config.add_route("login", "/login")
        self._config.add_view(self.login,
                              route_name="login",
                              request_method="POST",
                              permission="read")

        # Route: /logout (:method:logout)
        self._config.add_route("logout", "/logout")
        self._config.add_view(self.logout,
                              route_name="logout",
                              request_method="POST",
                              permission="read")

        # Route: /admin (:method:admin)
        self._config.add_route("admin", "/admin")
        self._config.add_view(self.admin,
                              route_name="admin",
                              request_method="GET",
                              permission="read")

        # Route: /resume (:method:resume)
        self._config.add_route("get-resume", "/resume/{type}")
        self._config.add_view(self.resume,
                              route_name="get-resume",
                              request_method="GET",
                              permission="read")

        # Route: /upload/resume (:method:upload_resume)
        self._config.add_route("upload-resume", "/upload/resume")
        self._config.add_view(self.upload_resume,
                              route_name="upload-resume",
                              request_method="POST",
                              permission="read")

        # Route: /index (:method:update_message_board)
        self._config.add_route("messageboard", "/messageboard")
        self._config.add_view(self.update_message_board,
                              route_name="messageboard",
                              request_method="GET",
                              permission="read")

        # Route: /index (:method:message)
        self._config.add_route("message", "/message")
        self._config.add_view(self.message,
                              route_name="message",
                              request_method="POST",
                              permission="read")

        # Route: /index (:method:index)
        self._config.add_route("index", "/")
        self._config.add_view(self.index,
                              route_name="index",
                              request_method="GET",
                              permission="read")

        # Make WSGI application object
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

        # template vars
        template_vars = {}

        # get user web session
        session = request.session

        # gen and save state
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for _ in xrange(32))
        session['state'] = state
        template_vars.update(STATE=unicode(state))

        # get last uploaded pdf resume timestamp if possible
        pdf_resume = self._database.get_most_recent_pdf_resume()
        if pdf_resume:
            last_uploaded = pdf_resume.datetime_uploaded
        else:
            last_uploaded = ""

        template_vars.update(resume={
                                     "last_uploaded": last_uploaded,
                                     }
                             )

        return Response(self._template_builder.get_index(template_vars))

    def login(self, request):
        """Ensure that the request is not a forgery and that the user sending
        this connect request is the expected user.

        This ``POST`` request is expected to have a `state` and `auth_code`
        encoded as json in the HTTP body.
        """
        decoded_json = json.loads(request.body)

        state = decoded_json.get("state")
        if not state:
            return _json_response("Missing `POST` data: `state`", 401)

        auth_code = decoded_json.get("auth_code")
        if not auth_code:
            return _json_response("Missing 'POST` data: `auth_code`", 401)

        try:
            result = self._login_manager.login(request.session, state, auth_code)
        except GAPIException, e:
            return _json_response(e.msg, e.status_code)
        else:
            user = {
                    "id": result.id,
                    "name": result.name,
                    "thumbnail_url": result.thumbnail_url,
                    "profile_pic_url": result.profile_pic_url,
                    }
            return _json_response(user, 200)

    # admin only
    def upload_resume(self, request):
        """Save a Resume object to the DB"""
        new_resume_pdf = request.POST["new_resume_pdf"]
        new_resume_docx = request.POST["new_resume_docx"]

        if new_resume_pdf is None:
            return _json_response("Need a pdf resume bro", 200)

        if new_resume_docx is None:
            return _json_response("Need .doc resume bro", 200)

        # extract pdf filename and data
        filename_pdf = str(new_resume_pdf.filename)
        file_pdf = new_resume_pdf.file

        # extract docx filename and data
        filename_docx = str(new_resume_docx.filename)
        file_docx = new_resume_docx.file

        # database session and current datetime
        session_db = self._database.get_session()
        dt_current = self._platform.time_datetime_now()

        # make docx Resume
        session_db.add(Resume(
                              filedata=file_docx.read(),
                              filename=filename_docx,
                              filetype="docx",
                              datetime_uploaded=dt_current,
                              ))

        # make pdf Resume
        session_db.add(Resume(
                              filedata=file_pdf.read(),
                              filename=filename_pdf,
                              filetype="pdf",
                              datetime_uploaded=dt_current,
                              ))

        # save
        session_db.commit()

        return Response("Cool")

    def resume(self, request):
        """GET Resume PDF file content"""
        filetype = request.matchdict.get("type")
        if filetype == "pdf":
            most_recent_resume = self._database.get_most_recent_pdf_resume()
        elif filetype == "docx":
            most_recent_resume = self._database.get_most_recent_docx_resume()

        if most_recent_resume:
            filedata = most_recent_resume.filedata
        else:
            filedata = ""

        return Response(
                        body=filedata,
                        status=200,
                        headers={
                                 "Content-Type": "application/octet-stream",
                                 "Content-Disposition": "attachment",
                                 }
                        )

    # admin only
    def admin(self, request):
        return Response(self._template_builder.get_admin({}))

    def update_message_board(self, request):
        """Return a list of messages between the currently logged in user and
        myself, descending starting w/ most recent.
        """
        session = request.session
        convo = self._database.get_conversation(session["gapi_id"])
        return _json_response(convo, 200)

    def message(self, request):
        decoded_msg = json.loads(request.body).get("msg")

        # if not message, do nothing
        if not decoded_msg:
            return _json_response("", 200)

        session = request.session
        user = self._database.get_user(gapi_id=session["gapi_id"])
        me = self._database.get_user(gapi_id=self._database.my_gapi_id)

        session_db = self._database.get_session()
        session_db.add(
                Message(
                        sender=user.id,
                        receiver=me.id,
                        msg_data=decoded_msg,
                        datetime_sent=self._platform.time_datetime_now(),
                        )
        )
        session_db.commit()
        return Response("Thanks", 200)
