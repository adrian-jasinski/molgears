# -*- coding: utf-8 -*-
"""
Functional test suite for the root controller.

This is an example of how functional tests can be written for controllers.

As opposed to a unit-test, which test a small unit of functionality,
functional tests exercise the whole application and its WSGI stack.

Please read http://pythonpaste.org/webtest/ for more information.

"""

from nose.tools import ok_

from molgears.tests import TestController

class TestRootController(TestController):
    """Tests for the method in the root controller."""

### Dodaj projekty
#    def test_start(self):
#        """The front page is working properly"""
#        response = self.app.get('/start')
#        msg = 'Select a project'
#        # You can look for specific strings:
#        ok_(msg in response)

        # You can also access a BeautifulSoup'ed response in your tests
        # (First run $ easy_install BeautifulSoup
        # and then uncomment the next two lines)

        # links = response.html.findAll('a')
        # print links
        # ok_(links, "Mummy, there are no links here!")

## UTWORZ TEST DODAWANIA PROJEKTU
#    def test_MDM(self):
#        """The project page is working properly"""
#        response = self.app.get('/MDM')
#        ok_('MDM Project information page' in response)

#    def test_data(self):
#        """The data display demo works with HTML"""
#        response = self.app.get('/data.html?a=1&b=2')
#        response.mustcontain("<td>a</td>", "<td>1</td>",
#                             "<td>b</td>", "<td>2</td>")

#    def test_data_json(self):
#        """The data display demo works with JSON"""
#        resp = self.app.get('/data.json?a=1&b=2')
#        ok_(dict(page='data', params={'a':'1', 'b':'2'}) == resp.json, resp.json)

    def test_secc_with_manager(self):
        """The manager can access the secure controller"""
        # Note how authentication is forged:
        environ = {'REMOTE_USER': 'manager'}
        resp = self.app.get('/admin', extra_environ=environ, status=200)
        ok_('Admin Panel' in resp.text, resp.text)

    def test_secc_with_editor(self):
        """The editor cannot access the secure controller"""
        environ = {'REMOTE_USER': 'editor'}
        self.app.get('/admin', extra_environ=environ, status=403)
        # It's enough to know that authorization was denied with a 403 status

    def test_secc_with_anonymous(self):
        """Anonymous users must not access the secure controller"""
        self.app.get('/admin', status=401)
        # It's enough to know that authorization was denied with a 401 status
