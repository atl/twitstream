import pycurl
import sys
from urllib import urlencode, getproxies
try:
    # I'm told that simplejson is faster than 2.6's json
    import simplejson as json
except ImportError:
    import json


USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream), using PycURL"

class TwitterStreamGET(object):
    def __init__(self, user, pword, url, action, debug=False, preprocessor=json.loads):
        self.debug = debug
        self.userpass = "%s:%s" % (user, pword)
        self.preprocessor = preprocessor
        self.url = url
        try:
            self.proxy = getproxies()['https']
        except:
            self.proxy = ''
        self.contents = ""
        self.action = action
        self._request = None
    
    @property
    def request(self):
        self._request = pycurl.Curl()
        self._request.setopt(self._request.URL, self.url)
        self._request.setopt(self._request.USERPWD, self.userpass)
        if self.proxy:
            self._request.setopt(self._request.PROXY, self.proxy)
        self._request.setopt(self._request.WRITEFUNCTION, self.body_callback)
        self._request.setopt(self._request.FTP_SSL, pycurl.FTPSSL_ALL)
        return self._request
    
    def body_callback(self, buf):
        self.contents += buf
        q = self.contents.split('\r\n')
        for s in q[:-1]:
            if s.startswith('{'):
                if self.preprocessor:
                    a = self.preprocessor(s)
                else:
                    a = s
                self.action(a)
        self.contents = q[-1]
    
    def run(self, request=None):
        if request:
            self._request = request
        else:
            self.request
        self._request.perform()
    
    def cleanup(self):
        print >> sys.stderr, self.contents
        self._request.close()

class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=tuple(), debug=False, preprocessor=json.loads):
        TwitterStreamGET.__init__(self, user, pword, url, action, debug, preprocessor)
        self.data = data
    
    @property
    def request(self):
        self._request = pycurl.Curl()
        self._request.setopt(self._request.URL, self.url)
        self._request.setopt(self._request.USERPWD, self.userpass)
        if self.proxy:
            self._request.setopt(self._request.PROXY, self.proxy)
        self._request.setopt(self._request.WRITEFUNCTION, self.body_callback)
        self._request.setopt(self._request.POST, 1)
        self._request.setopt(self._request.POSTFIELDS, urlencode(self.data))
        return self._request
    

