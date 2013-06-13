from bottle import route, redirect, static_file, post, get, request
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
    return webserver.handle_request_static(request)


@route("/")
def index():
    return webserver.handle_request_get(request)
