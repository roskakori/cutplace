"""
Test for web server.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import itertools
import logging
import mimetools
import mimetypes
import os.path
import unittest
import urllib2

import dev_test
import _web

# Port to use for test web server.
_PORT = 8642


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""
    # For details, see <http://broadcast.oreilly.com/2009/07/pymotw-urllib2.html>.

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request. Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [
                part_boundary,
                'Content-Disposition: form-data; name="%s"' % name,
                '',
                value,
            ]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [
                part_boundary,
                'Content-Disposition: file; name="%s"; filename="%s"' % \
                (field_name, filename),
                'Content-Type: %s' % content_type,
                '',
                body,
            ]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


class WebTest(unittest.TestCase):
    """TestCase for web module."""
    def _createOpener(self):
        # Disable proxies.
        proxy_support = urllib2.ProxyHandler({})
        result = urllib2.build_opener(proxy_support)
        return result

    def _get(self, url):
        opener = self._createOpener()
        result = opener.open(url)
        return result

    def _post(self, icdPath, dataPath=None):
        assert icdPath is not None

        form = MultiPartForm()
        form.add_file("icd", os.path.split(icdPath)[1], open(icdPath, "rb"))

        # Build the request
        request = urllib2.Request("http://localhost:%d/cutplace" % (_PORT))
        request.add_header("User-agent", "test_web.py")
        body = str(form)
        request.add_header("Content-type", form.get_content_type())
        request.add_header("Content-length", len(body))
        request.add_data(body)

        print
        print "OUTGOING DATA:"
        print request.get_data()

        print
        print "SERVER RESPONSE:"
        opener = self._createOpener()
        result = opener.open(request)
        print result.read()
        return result

    def _getHtmlText(self, relativeUrl=""):
        assert relativeUrl is not None
        response = self._get("http://localhost:%d/%s" % (_PORT, relativeUrl))
        try:
            self.assertEquals(response.info()["Content-type"], "text/html")
            result = response.read()
        finally:
            response.close()
        return result

    def setUp(self):
        self._webServer = _web.WebServer(_PORT)
        self._webServer.start()

    def tearDown(self):
        self._webServer.finish()
        self._webServer = None

    def testAbout(self):
        text = self._getHtmlText("about").lower()
        self.assertTrue(text.find("about") >= 0)

    def testForm(self):
        text = self._getHtmlText().lower()
        self.assertTrue(text.find("<form") >= 0)

    def _testValidateProperData(self):
        # TODO: Implement: testValidateProperData
        pass

    def _testValidateBrokenData(self):
        # TODO: Implement: testValidateBrokenData
        pass

    def _testValidateProperIcd(self):
        self._post(dev_test.getTestIcdPath("customers.csv"))

    def _testValidateBrokenIcd(self):
        # TODO: Implement: testValidateBrokenIcd
        pass

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    logging.getLogger("cutplace.web").setLevel(logging.INFO)
    unittest.main()
