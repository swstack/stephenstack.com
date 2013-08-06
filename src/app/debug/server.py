from threading import Thread
from wsgiref.simple_server import make_server


class Server(Thread):
    def __init__(self, router, host="0.0.0.0", port=8080):
        Thread.__init__(self)
        self._router = router
        self._host = host
        self._port = port

    def run(self):
        server = make_server(self._host, self._port, self._router.get_wsgi_app())
        server.serve_forever()
