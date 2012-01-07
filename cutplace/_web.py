"""
Web server to provide a simple GUI for cutplace.
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
import cgi
import BaseHTTPServer
import logging
import StringIO
import sys
import tempfile

import interface
import version
import _tools

"""
Default port the web server will use unless specified otherwise.
According to <http://www.iana.org/assignments/port-numbers>,
this number is unassigned.
"""
DEFAULT_PORT = 8778

_SERVER_VERSION = u"cutplace/%s" % version.VERSION_NUMBER

# Sleep time for server related polling.
_TICK_IN_SECONDS = 0.1


class _HtmlWritingValidationListener(interface.BaseValidationListener):
    """
    `BaseValidationListener` that writes accepted and rejected rows as HTML table.
    """
    def __init__(self, htmlTargetFile, itemCount):
        assert htmlTargetFile is not None
        assert itemCount is not None
        assert itemCount > 0, u"itemCount=%r" % itemCount
        self._htmlTargetFile = htmlTargetFile
        self._itemCount = itemCount
        self.acceptedCount = 0
        self.rejectedCount = 0
        self.checkAtEndFailedCount = 0

    def _writeRow(self, row, cssClass):
        assert cssClass is not None
        self._htmlTargetFile.write(u"<tr>\n")
        for item in row:
            self._htmlTargetFile.write(u"<td class=\"%s\">%s</td>\n" % (cssClass, cgi.escape(item)))
        self._htmlTargetFile.write(u"</tr>\n")

    def _writeTextRow(self, text):
        assert text is not None
        self._htmlTargetFile.write(u"<tr>\n")
        self._htmlTargetFile.write(u"<td colspan=\"%d\">%s</td>\n" % (self._itemCount, cgi.escape(text)))
        self._htmlTargetFile.write(u"</tr>\n")

    def acceptedRow(self, row, location):
        assert row is not None
        self.acceptedCount += 1
        self._writeRow(row, "ok")

    def rejectedRow(self, row, error):
        assert row is not None
        assert error is not None
        self.rejectedCount += 1
        self._writeRow(row, "error")
        self._writeTextRow(u"%s" % error)

    def checkAtEndFailed(self, error):
        assert error is not None
        self.checkAtEndFailedCount += 1
        self._writeTextRow(u"check at end failed: %s" % error)


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = _SERVER_VERSION
    _IO_BUFFER_SIZE = 8192
    _STYLE = u"""
    body {
      background-color: #ffffff;
      color: #000000;
      font-family: sans-serif;
    }
    h1 {
        background-color: #f9f300;
        width: 100%;
    }
    td {
      border-width: 0;
    }
    tr {
      border-width: 0;
    }
    th {
      background-color: #dddddd;
      border-width: 0;
    }
    .ok {
      background-color: #ddffdd;
    }
    .error {
      background-color: #ffdddd;
    }
"""
    _FOOTER = u"<hr><a href=\"http://cutplace.sourceforge.net/\">cutplace</a> %s" % version.VERSION_NUMBER

    _FORM = u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Cutplace</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Cutplace</h1>
<p>Validate data according to an interface control document.</p>
<form action="cutplace" method="post" enctype="multipart/form-data">
<table border="0">
  <tr>
    <td>ICD file:</td>
    <td><input name="icd" type="file" size="50"></td>
  </tr>
  <tr>
    <td>Data file:</td>
    <td><input name="data" type="file" size="50"></td>
  </tr>
  <tr>
    <td><input type="submit" value="Validate"></td>
  </tr>
</table>
</form>
%s
</body></html>
""" % (_STYLE, _FOOTER)

    _ABOUT = u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>About cutplace</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>About cutplace</h1>
<p>Cutplace: Version %s<br>
Python: Version %s<br>
Platform: %s</p>
%s
</body></html>
""" % (_STYLE, version.VERSION_TAG, cgi.escape(_tools.pythonVersion()), cgi.escape(_tools.platformVersion()), _FOOTER)

    _SHUTDOWN = u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Cutplace</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Cutplace</h1>
<p>The cutplace server has been shut down.</p>
%s
</body></html>
""" % (_STYLE, _FOOTER)

    def do_GET(self):

        log = logging.getLogger("cutplace.web")
        log.info(u"%s %r", self.command, self.path)

        if (self.path == "/"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(Handler._FORM)
            self.wfile.close()
        elif (self.path == "/about"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(Handler._ABOUT)
            self.wfile.close()
        else:
            self.send_error(404)

    def do_POST(self):
        log = logging.getLogger("cutplace.web")
        log.info("%s %r" % (self.command, self.path))

        # Parse POST option. Based on code by Pierre Quentel.
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        length = int(self.headers.getheader('content-length'))
        if ctype == 'multipart/form-data':
            fileMap = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            qs = self.rfile.read(length)
            fileMap = cgi.parse_qs(qs, keep_blank_values=1)
        else:
            fileMap = {}  # Unknown content-type

        if "icd" in fileMap:
            icdContent = fileMap["icd"][0]
        else:
            icdContent = None
        if "data" in fileMap:
            dataContent = fileMap["data"][0]
        else:
            dataContent = None

        if icdContent:
            try:
                icdData = StringIO.StringIO(icdContent)
                icd = interface.InterfaceControlDocument()
                icd.read(icdData)
                if dataContent:
                    validationHtmlFile = tempfile.TemporaryFile(suffix=".html", prefix="cutplace-web-")
                    try:
                        log.debug(u"writing html to temporary file: %r", validationHtmlFile.name)
                        validationHtmlFile.write(u"<table><tr>")
                        # Write table headings.
                        for title in icd.fieldNames:
                            validationHtmlFile.write(u"<th>%s</th>" % cgi.escape(title))
                        validationHtmlFile.write(u"</tr>")

                        # Start listening to validation events.
                        htmlListener = _HtmlWritingValidationListener(validationHtmlFile, len(icd.fieldNames))
                        icd.addValidationListener(htmlListener)
                        try:
                            dataReadable = StringIO.StringIO(dataContent)
                            icd.validate(dataReadable)
                            icd.removeValidationListener(htmlListener)
                            validationHtmlFile.write("</table>")

                            self.send_response(200)
                            self.send_header("Content-type", "text/html")
                            self.end_headers()

                            # Write the contents of the temporary HTML file to the web page.
                            self.wfile.write(u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Validation results</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Validation results</h1>
""" % (Handler._STYLE))
                            self.wfile.write(u"""<table>
  <tr><td>Rows accepted:</td><td>%d</td></tr>
  <tr><td>Rows rejected:</td><td>%d</td></tr>
  <tr><td>Checks at end failed:</td><td>%d</td></tr>
</table>
""" % (htmlListener.acceptedCount, htmlListener.rejectedCount, htmlListener.checkAtEndFailedCount))
                            validationHtmlFile.seek(0)
                            htmlFileBuffer = validationHtmlFile.read(Handler._IO_BUFFER_SIZE)
                            while htmlFileBuffer:
                                self.wfile.write(htmlFileBuffer)
                                htmlFileBuffer = validationHtmlFile.read(Handler._IO_BUFFER_SIZE)
                            self.wfile.write(Handler._FOOTER)
                        except:
                            self.send_error(400, u"cannot validate data: %s" % cgi.escape(str(sys.exc_info()[1])))
                    finally:
                        validationHtmlFile.close()
                else:
                    log.info("ICD is valid")
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(u"ICD file is valid.")
            except:
                log.error(u"cannot parse ICD", exc_info=1)
                self.send_error(400, u"cannot parse ICD: %s" % cgi.escape(str(sys.exc_info()[1])))
        else:
            errorMessage = "ICD file must be specified"
            log.error(errorMessage)
            self.send_error(400, u"%s." % cgi.escape(errorMessage))


class WebServer(_tools.FinishableThread):
    """
    Simple web server running in an own thread. It can only process one request at a time. Use `finish()` to
    finish the server.
    """
    def __init__(self, port=DEFAULT_PORT):
        super(WebServer, self).__init__("cutplace.web.server")
        self.site = "http://localhost:%d/" % port
        self._httpd = BaseHTTPServer.HTTPServer(("", port), Handler)
        self._httpd.timeout = _TICK_IN_SECONDS

    def run(self):
        self.log.info(u"%s", _SERVER_VERSION)
        self.log.info(u"Visit <%s> to connect", self.site)
        self.log.info(u"Press Control-C to shut down")
        while not self.finished:
            self._httpd.handle_request()
        self.log.info("shut down finished")


def main(port=DEFAULT_PORT, isOpenBrowser=False):
    server = WebServer(port)
    server.start()
    try:
        if isOpenBrowser:
            import webbrowser
            webbrowser.open(server.site)
        while server.isAlive():
            server.join(_TICK_IN_SECONDS)
    except KeyboardInterrupt:
        server.finish()
    finally:
        server.join()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("cutplace").setLevel(logging.INFO)
    main()
