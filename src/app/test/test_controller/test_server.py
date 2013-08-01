from app.controller.server import Server
from mock import Mock
from wsgi_intercept import add_wsgi_intercept, remove_wsgi_intercept
from wsgi_intercept.urllib2_intercept import install_opener
import unittest
import urllib2


class TestServer(unittest.TestCase):
    def setUp(self):
        install_opener()
        app = Server(Mock(), Mock(), Mock())._bottle_app
        add_wsgi_intercept("localhost", 8080, lambda: app)

    def tearDown(self):
        remove_wsgi_intercept("localhost", 8080)

    def test_one(self):
        resp = urllib2.urlopen("http://localhost:8080/").read()
        print resp


if __name__ == '__main__':
    unittest.main()
