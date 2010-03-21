"""
Web server to provide a simple GUI for cutplace.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import cgi
import BaseHTTPServer
import errno
import interface
import logging
import os
import select
import StringIO
import sys
import tempfile
import threading
import time
import tools
import urllib
import version

"""
Default port the web server will use unless specified otherwise.
According to <http://www.iana.org/assignments/port-numbers>,
this number is unassigned.
"""
DEFAULT_PORT = 8778

_SERVER_VERSION = "cutplace/%s" % version.VERSION_NUMBER

_allowShutDown = False
_readyToShutDown = False

class _HtmlWritingValidationEventListener(interface.ValidationEventListener):
    """
    `ValidationEventListener` that writes accepted and rejected rows as HTML table.
    """
    def __init__(self, htmlTargetFile, itemCount):
        assert htmlTargetFile is not None
        assert itemCount is not None
        assert itemCount > 0, "itemCount=%r" % itemCount
        self._htmlTargetFile = htmlTargetFile
        self._itemCount = itemCount
        self.acceptedCount = 0
        self.rejectedCount = 0
        self.checkAtEndFailedCount = 0

    def _writeRow(self, row, cssClass):
        assert cssClass is not None
        self._htmlTargetFile.write("<tr>\n")
        for item in row:
            self._htmlTargetFile.write("<td class=\"%s\">%s</td>\n" % (cssClass, cgi.escape(item)))
        self._htmlTargetFile.write("</tr>\n")
        
    def _writeTextRow(self, text):
        assert text is not None
        self._htmlTargetFile.write("<tr>\n")
        self._htmlTargetFile.write("<td colspan=\"%d\">%s</td>\n" % (self._itemCount, cgi.escape(text)))
        self._htmlTargetFile.write("</tr>\n")
        
    def acceptedRow(self, row):
        assert row is not None
        self.acceptedCount += 1
        self._writeRow(row, "ok")
    
    def rejectedRow(self, row, error):
        assert row is not None
        assert error is not None
        self.rejectedCount += 1
        self._writeRow(row, "error")
        self._writeTextRow("%s" % error)
    
    def checkAtEndFailed(self, error):
        assert error is not None
        self.checkAtEndFailedCount += 1
        self._writeTextRow("check at end failed: %s" % error)
    
class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = _SERVER_VERSION
    _IO_BUFFER_SIZE = 8192
    _STYLE = """
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
    _FOOTER = "<hr><a href=\"http://cutplace.sourceforge.net/\">cutplace</a> %s" % version.VERSION_NUMBER

    _FORM = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
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

    _ABOUT = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
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
""" % (_STYLE, version.VERSION_TAG, cgi.escape(tools.pythonVersion()), cgi.escape(tools.platformVersion()), _FOOTER)

    _SHUTDOWN = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
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
        log.info("%s %r" % (self.command, self.path))

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
        elif (self.path == "/shutdown"):
            global _allowShutDown
            global _readyToShutDown
            if _allowShutDown:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(Handler._SHUTDOWN)
                self.wfile.close()
                _readyToShutDown = True
            else:
                self.send_error(400, "cannot shutdown server: the shutdown feature must be enabled when starting the server")
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
            fileMap = {} # Unknown content-type
        
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
                        log.debug("writing html to temporary file: %r" % validationHtmlFile.name)
                        validationHtmlFile.write("<table><tr>")
                        # Write table headings.
                        for title in icd.fieldNames:
                            validationHtmlFile.write("<th>%s</th>" % cgi.escape(title))
                        validationHtmlFile.write("</tr>")
    
                        # Start listening to validation events.
                        htmlListener = _HtmlWritingValidationEventListener(validationHtmlFile, len(icd.fieldNames))
                        icd.addValidationEventListener(htmlListener)
                        try:
                            dataReadable = StringIO.StringIO(dataContent)
                            icd.validate(dataReadable)
                            icd.removeValidationEventListener(htmlListener)
                            validationHtmlFile.write("</table>")
                            
                            self.send_response(200)
                            self.send_header("Content-type", "text/html")
                            self.end_headers()
                            
                            # Write the contents of the temporary HTML file to the web page.
                            self.wfile.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Validation results</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Validation results</h1>
""" % (Handler._STYLE))
                            self.wfile.write("""<table>
  <tr><td>Rows accepted:</td><td>%d</td></tr>
  <tr><td>Rows rejected:</td><td>%d</td></tr>
  <tr><td>Checks at end failed:</td><td>%d</td></tr>
</table>
""" %(htmlListener.acceptedCount, htmlListener.rejectedCount, htmlListener.checkAtEndFailedCount))
                            validationHtmlFile.seek(0)
                            buffer = validationHtmlFile.read(Handler._IO_BUFFER_SIZE)
                            while buffer:
                                self.wfile.write(buffer)
                                buffer = validationHtmlFile.read(Handler._IO_BUFFER_SIZE)
                            self.wfile.write(Handler._FOOTER)
                        except:
                            self.send_error(400, "cannot validate data: %s" % cgi.escape(str(sys.exc_info()[1])))
                    finally:
                        validationHtmlFile.close()
                else:
                    log.info("ICD is valid")
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write("ICD file is valid.")
            except:
                log.error("cannot parse ICD", exc_info=1)
                self.send_error(400, "cannot parse ICD: %s" % cgi.escape(str(sys.exc_info()[1])))
        else:
            errorMessage = "ICD file must be specified"
            log.error(errorMessage)
            self.send_error(400, "%s." % cgi.escape(errorMessage))


class WaitForServerToBeReadyThread(threading.Thread):
    """Thread to wait for server to be ready."""
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None):
        super(WaitForServerToBeReadyThread, self).__init__(group, target, name, args, kwargs)
        self.site = None
        self.maxRetries = 100
        self.delayBetweenRetryInSeconds = 0.2
        self.siteAvailable = False

    def run(self):
        assert self.site is not None
        assert self.maxRetries > 0
        assert self.delayBetweenRetryInSeconds > 0

        log = logging.getLogger("cutplace.web.wait")
        self.siteAvailable = False
        retries = 0
        log.info("wait for server to be ready")
        while not self.siteAvailable and (retries < self.maxRetries):
            try:
                # Attempt to open the validation form.
                # Use no proxy because it is a local-only connection anyway.
                urllib.urlopen(self.site, proxies={}).close()
                self.siteAvailable = True
            except IOError:
                log.error("cannot find server yet, retry=%d/%d" % (retries, self.maxRetries), exc_info=1)
                time.sleep(self.delayBetweenRetryInSeconds)
                retries += 1
    
class OpenBrowserThread(WaitForServerToBeReadyThread):
    """Thread to open the cutplace's validation form in the web browser."""
    def run(self):
        super(OpenBrowserThread, self).run()

        log = logging.getLogger("cutplace.browser")
        if self.siteAvailable:
            log.info("open web browser")
            try:
                # HACK: Attempt to import webbrowser only here because this module is not available
                # for Jython 2.5.
                import webbrowser
                webbrowser.open(self.site)
            except ImportError, error:
                log.warning("cannot browse site %r: %s" % (self.site, error))
        else:
            log.warning("cannot find server at <%s>, giving up; try to connect manually" % self.site)

def main(port=DEFAULT_PORT, isOpenBrowser=False, allowShutDown=False):
    # TODO: Get rid of super ugly global `_allowShutDown`.
    global _allowShutDown
    global _readyToShutDown
    
    log = logging.getLogger("cutplace.web")
    _allowShutDown = allowShutDown
    httpd = BaseHTTPServer.HTTPServer(("", port), Handler)
    site = "http://localhost:%d/" % port
    log.info(_SERVER_VERSION)
    log.debug("site=%r, isOpenBrowser=%r" % (site, isOpenBrowser))
    if isOpenBrowser:
        browserOpener = OpenBrowserThread()
        browserOpener.site = site
        browserOpener.start()
    log.info("Visit <%s> to connect" % site)
    log.info("Press Control-C to shut down")
    try:
        while not _readyToShutDown:
            httpd.handle_request()
    except KeyboardInterrupt:
        # Ignore Control-C and proceed with shut down.
        pass
    log.info("Shut down")
                                     
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    main()
