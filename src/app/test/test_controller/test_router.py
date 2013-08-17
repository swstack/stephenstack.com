from app.controller.router import Router
from app.test.utilities import MockResourceManager
from app.view.templates import TemplateBuilder
from mock import Mock
from wsgi_intercept import add_wsgi_intercept, remove_wsgi_intercept
from wsgi_intercept.urllib2_intercept import install_opener
import json
import unittest
import urllib2


def JSON(obj):
    return json.dumps(obj)


class TestRouter(unittest.TestCase):
    def setUp(self):
        self._resource_manager = MockResourceManager()
        self._template_builder = TemplateBuilder(self._resource_manager)
        self._template_builder.start()
        self._router = Router(resource_manager=self._resource_manager,
                              template_builder=self._template_builder,
                              login_manager=Mock(),
                              database=Mock(),
                              platform=Mock())
        self._router.start()
        self._app = self._router.get_wsgi_app()
        install_opener()
        add_wsgi_intercept("localhost", 8080, lambda: self._app)

    def tearDown(self):
        remove_wsgi_intercept("localhost", 8080)
        self._router = None
        self._template_builder = None
        self._resource_manager = None
        self._app = None

    #===========================================================================
    # Helpers
    #===========================================================================
    def _route_index(self):
        return urllib2.urlopen("http://localhost:8080/").read()

    def _route_login(self, post_data):
        return urllib2.urlopen("http://localhost:8080/login", post_data).read()

    def _route_logout(self):
        return urllib2.urlopen("http://localhost:8080/logout").read()

    def _route_static(self, asset):
        return urllib2.urlopen("http://localhost:8080/static").read()

    def _assert_json_response(self, expected_json, resp):
        """ `expected_json` in object form, unencoded """
        self.assertEqual(json.loads(expected_json), resp.body.read())

    #===========================================================================
    # Tests
    #===========================================================================
    def test_index(self):
        resp = self._route_index()
        self.assertNotEqual(resp, None)

    def test_login_without_state(self):
        try:
            self._route_login(JSON({"auth_code": "1234"}))
        except Exception, e:
            self.assertEqual(e.code, 401)

    def test_login_without_auth_code(self):
        try:
            self._route_login(JSON({"state": "1234"}))
        except Exception, e:
            self.assertEqual(e.code, 401)

    def test_login_with_creds(self):
        self._route_login(JSON({
                                "state": "1234",
                                "auth_code": "5678",
                                }))

if __name__ == '__main__':
    unittest.main()
