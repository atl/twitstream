import pycurl
import sys
from urllib import urlencode
try:
    # I'm told that simplejson is faster than 2.6's json
    import simplejson as json
except ImportError:
    import json


USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream)"

class TwitterStreamGET(object):
    def __init__(self, user, pword, url, action, debug=False):
        self.userpass = "%s:%s" % (user, pword)
        self.url = url
        try:
            proxy = urlparse(urllib.getproxies()['http'])[1].split(':')
            # Respect libcurl's default of 1080:
            proxy[1] = int(proxy[1]) or 1080
            self.proxy = tuple(proxy)
        except:
            self.proxy = None
        self.contents = ""
        self.action = action
        self.debug = debug
        self._request = None
    
    @property
    def request(self):
        self._request = pycurl.Curl()
        self._request.setopt(self._request.URL, self.url)
        self._request.setopt(self._request.USERPWD, self.userpass)
        if self.proxy:
            self._request.setopt(self._request.PROXY, self.proxy)
        self._request.setopt(self._request.WRITEFUNCTION, self.body_callback)
        return self._request
    
    def body_callback(self, buf):
        self.contents += buf
        q = self.contents.split('\r\n')
        for s in q[:-1]:
            if s.startswith('{'):
                a = json.loads(s)
                self.action(a)
        self.contents = q[-1]
    
    def run(self, request=None):
        if request:
            self._request = request
        else:
            self.request
        self._request.perform()
    

class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=tuple(), debug=False):
        TwitterStreamGET.__init__(self, user, pword, url, action, debug)
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
    

