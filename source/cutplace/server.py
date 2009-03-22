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

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = _SERVER_VERSION
    _FORM = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html><head><title>Cutplace ICD Validator</title></head><body>
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
""" % (version.VERSION_NUMBER)
    
    def do_GET(self):
        sys.__stderr__.write("%s %r\n" % (self.command, self.path))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(Handler._FORM)
        self.wfile.close()

    def do_POST(self):
        sys.__stderr__.write("%s %r\n" % (self.command, self.path))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
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
        
        if icdContent:
            try:
                icdData = StringIO.StringIO(icdContent)
                i = icd.InterfaceDescription()
                i.read(icdData)
                if dataContent:
                    try:
                        dataReadable = StringIO.StringIO(dataContent)
                        i.validate(dataReadable)
                        self.wfile.write("Data have been validated, see server log for results.")
                    except:
                        self.send_error(400, "cannot validate data: %s\n\n%s" % (sys.exc_info()[1], icdContent))
                else:
                    self.wfile.write("ICD file is valid.")
            except:
                self.send_error(400, "cannot parse ICD: %s\n\n%s" % (sys.exc_info()[1], icdContent))
        else:
            self.send_error(400, "ICD file must be specified")
                             
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    serverLog = logging.getLogger("cutplace.server")
    serverLog.setLevel(logging.INFO)

    PORT = 8000
    
    httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
    serverLog.info("%s serving at port %d" % (_SERVER_VERSION, PORT))
    serverLog.info("Press Control-C to exit")
    httpd.serve_forever()
    