from bottle import route, static_file, get, request, post
from util.paths import HTTP_STATIC
import logging

webserver = None

logger = logging.getLogger("router")


class Router(object):

    def __init__(self):
        global webserver
        webserver = self


@get('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root=HTTP_STATIC)


@route("/")
def index():
    return webserver.handle_index()


@post("/login")
def login():
    username = request.forms.get("username", None)
    password = request.forms.get("password", None)
    if not username and password:
        return ""
    else:
        return webserver.handle_login(username, password)
