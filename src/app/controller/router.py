from app.controller.login import GAPIException
from app.model.model import Resume
from pyramid.config import Configurator
from pyramid.response import Response, FileResponse
from pyramid.session import UnencryptedCookieSessionFactoryConfig
import datetime
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
        logger.error("Could not serialize to JSON!! -- %s", body)
    finally:
        return Response(body=body,
                        status=status,
                        headers={"Content-Type": "application/json"})


class Router(object):
    #================================================================================
    # Construction
    #================================================================================
    def __init__(self, resource_manager,
                       template_builder,
                       login_manager,
                       database):
        # Dependencies --------------------------------------------------------------
        self._resource_manager = resource_manager
        self._template_builder = template_builder
        self._login_manager = login_manager
        self._database = database

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
        session = request.session
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for _ in xrange(32))
        session['state'] = state
        template_vars = {
              "resume": "",
              "STATE": unicode(state)
        }
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
            return _json_response(result, 200)

    def upload_resume(self, request):
        """Save a Resume object to the DB"""
        new_resume_pdf = request.POST["new_resume_pdf"]
        new_resume_docx = request.POST["new_resume_docx"]

        if new_resume_pdf is None:
            return _json_response("Need a pdf resume bro", 200)

        if new_resume_docx is None:
            return _json_response("Need .doc resume bro", 200)

        # extract pdf filename and data
        filename_pdf = new_resume_pdf.filename
        file_pdf = new_resume_pdf.file

        # extract docx filename and data
        filename_docx = new_resume_docx.filename
        file_docx = new_resume_docx.file

        # database session and current datetime
        session_db = self._database.get_session()
        current_dt = datetime.datetime.now()

        # make docx Resume
        session_db.add(Resume(
                              file=file_docx.read(),
                              filename=str(filename_docx),
                              filetype="docx",
                              date_uploaded=current_dt,
                              ))

        # make pdf Resume
        session_db.add(Resume(
                              file=file_pdf.read(),
                              filename=str(filename_pdf),
                              filetype="pdf",
                              date_uploaded=current_dt,
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
        else:
            most_recent_resume = ""
        return Response(
                            most_recent_resume.file,
                            content_type="application/pdf",
                            )

    def admin(self, request):
        return Response(self._template_builder.get_admin({}))
