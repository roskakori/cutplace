"""Webserver to provide a simple GUI for cutplace."""
import cgi
import BaseHTTPServer
import icd
import logging
import select
import StringIO
import sys
import version

_SERVER_VERSION = "CutplaceHTTP/%s" % version.VERSION_NUMBER

class WfileWritingIcdEventListener(icd.IcdEventListener):
    def __init__(self, wfile, itemCount):
        assert wfile is not None
        assert itemCount is not None
        assert itemCount > 0, "itermCount=%r" % itemCount
        self.wfile = wfile
        self.itemCount = itemCount
        self.acceptedCount = 0
        self.rejectedCount = 0

    def _writeRow(self, row, cssClass):
        if len(row) == 1:
            colspanText = " colspan=\"%d\"" % self.itemCount
        else:
            colspanText = ""
        self.wfile.write("<tr>\n")
        for item in row:
            self.wfile.write("<td class=\"%s\"%s>%s</td>\n" % (cssClass, colspanText, cgi.escape(item)))
        self.wfile.write("</tr>\n")
        
    def acceptedRow(self, row):
        self._writeRow(row, "ok")
    
    def rejectedRow(self, row, errorMessage):
        self._writeRow(row, "error")
        self._writeRow([errorMessage], "error")
    
    def checkAtRowFailed(self, row, errorMessage):
        self._writeRow(row, "error")
    
    def checkAtEndFailed(self, errorMessage):
        self._writeRow(["check at end failed: %s" % errorMessage], "error")
    
    def dataFormatFailed(self, errorMessage):
        self._writeRow(["data format is broken: %s" % errorMessage], "error")

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = _SERVER_VERSION
    _STYLE = """
    body {
      background-color: #ffffff;
      color: #000000;
      font-family: sans-serif;
    }
    td {
      border-color: #e0e0e0;
      border-style: solid;
      border-width: 1px;
      margin: 0;
      padding: 0;
    }
    th {
      background-color: #e0e0e0;
    }
    .ok {
      background-color: #e0ffe0;
    }
    .error {
      background-color: #ffe0e0;
    }
"""
    _FORM = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Cutplace ICD Validator</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Cutplace ICD Validator</h1>
<p>Version %s</p>
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
</body></html>
""" % (_STYLE, version.VERSION_NUMBER)
    
    def do_GET(self):
        log = logging.getLogger("cutplace.server")
        log.info("%s %r" % (self.command, self.path))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(Handler._FORM)
        self.wfile.close()

    def do_POST(self):
        log = logging.getLogger("cutplace.server")
        log.info("%s %r" % (self.command, self.path))

        self.send_header("Content-type", "text/html")
        self.end_headers()
        # FIXME: Send 200 only if everything worked out, otherise 4xx error messages look rather messy.
        self.send_response(200)

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
        # throw away additional data [see bug #427345]
        while select.select([self.rfile._sock], [], [], 0)[0]:
            if not self.rfile._sock.recv(1):
                break
        
        if "icd" in fileMap:
            icdContent = fileMap["icd"][0]
        else:
            icdContent = None
        if "data" in fileMap:
            dataContent = fileMap["data"][0]
        else:
            dataContent = None
        
        self.wfile.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Validation results</title>
  <style type="text/css">%s
  </style>
</head><body>
<h1>Validation results</h1>
""" % (Handler._STYLE))

        if icdContent:
            try:
                icdData = StringIO.StringIO(icdContent)
                i = icd.InterfaceDescription()
                i.read(icdData)
                if dataContent:
                    self.wfile.write("<table><tr>")
                    # Write table headings.
                    for title in i.fieldNames:
                        self.wfile.write("<th>%s</th>" % cgi.escape(title))
                    self.wfile.write("</tr>")

                    # Start listening to validation events.
                    wfileListener = WfileWritingIcdEventListener(self.wfile, len(i.fieldNames))
                    i.addIcdEventListener(wfileListener)
                    try:
                        dataReadable = StringIO.StringIO(dataContent)
                        i.validate(dataReadable)
                    except:
                        self.send_error(400, "cannot validate data: %s\n\n%s" % (sys.exc_info()[1], icdContent))
                    finally:
                        self.wfile.write("</table>")
                        i.removeIcdEventListener(wfileListener)
                else:
                    log.info("ICD is valid")
                    self.wfile.write("ICD file is valid.")
            except:
                log.error("cannot parse IDC", exc_info=1)
                self.send_error(400, "cannot parse ICD: %s\n\n<pre>%s</pre>" % (cgi.escape(sys.exc_info()[1]), cgi.escape(icdContent)))
        else:
            errorMessage = "ICD file must be specified"
            log.error(errorMessage)
            self.send_error(400, "%s." % cgi.escape(errorMessage))
                             
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    serverLog = logging.getLogger("cutplace.server")
    serverLog.setLevel(logging.INFO)

    PORT = 8000
    
    httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
    serverLog.info("%s serving at port %d" % (_SERVER_VERSION, PORT))
    serverLog.info("Press Control-C to exit")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        serverLog.info("exited")
    