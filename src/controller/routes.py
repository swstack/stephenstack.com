from bottle import route, static_file, get, request
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
    return webserver.handle_request_get(request)
