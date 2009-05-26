"""
Test for web server.
"""
import logging
import server
import threading
import time
import unittest
import urllib2

_isWebStarted = False

def _ifNecessaryStartWeb():
    global _isWebStarted
    
    if not _isWebStarted:
        web = WebThread()
        web.start()
        # FIXME: Wait for server to be ready properly.
        time.sleep(1)
        _isWebStarted = True

# FIXME: Shut down server when test is done.

class WebThread(threading.Thread):
    """Thread to run the test web server in."""
    
    PORT = 8642
    
    def run(self):
        server.main(WebThread.PORT)
        # FIXME: Let exception result in the test case to fail.
        
class WebTest(unittest.TestCase):
    """TestCase for web module."""
    
    def _fetch(self, url):
        # Disable proxies.
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
        # Fetch response from server.
        try:
            result = opener.open(url)
        except IOError:
            _ifNecessaryStartWeb()
            result = opener.open(url)
        return result
    
    def _getHtmlText(self, relativeUrl=""):
        response = self._fetch("http://localhost:%d/%s" % (WebThread.PORT, relativeUrl))
        try:
            self.assertEquals(response.info()["Content-type"], "text/html")
            result = response.read()
        finally:
            response.close()
        return result
        
    def testAbout(self):
        text = self._getHtmlText("about").lower()
        self.assertTrue(text.find("about") >= 0)

    def testForm(self):
        text = self._getHtmlText().lower()
        self.assertTrue(text.find("<form") >= 0)
    
    def testValidateProperData(self):
        # TODO: Implement: testValidateProperData
        pass

    def testValidateBrokenData(self):
        # TODO: Implement: testValidateBrokenData
        pass

    def testValidateProperIcd(self):
        # TODO: Implement: testValidateProperIcd
        pass

    def testValidateBrokenIcd(self):
        # TODO: Implement: testValidateBrokenIcd
        pass

if __name__ == "__main__": # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    logging.getLogger("cutplace.server").setLevel(logging.INFO)
    unittest.main()