from bottle import route, static_file, get, request, post, run
from threading import Thread
import logging


HOST = "localhost"
PORT = 8080

templates = None
static_root = None


def start(_templates, _static_root):
    global templates, static_root
    templates = _templates
    static_root = _static_root
    run(host=HOST, port=PORT, quiet=True)


@get('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root=static_root)


@route("/")
def index():
    return templates.get_index()
