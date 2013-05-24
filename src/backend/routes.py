from bottle import route, redirect, static_file, post, request
from util.paths import HTTP_STATIC
import logging

webserver = None

logger = logging.getLogger("router")


class Router(object):

    def __init__(self):
        global webserver
        webserver = self


@route('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root=HTTP_STATIC)


@route("/")
def index():
    webserver.
