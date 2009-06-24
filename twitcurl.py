import pycurl
import sys
from urllib import urlencode
try:
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
            # Respect libproxy's default of 1080:
            proxy[1] = int(proxy[1]) or 1080
            self.proxy = tuple(proxy)
        except:
            self.proxy = None
        self.contents = ""
        self.action = action
        self.debug = debug
        self.request = None
    
    def prepare_request(self):
        self.request = pycurl.Curl()
        self.request.setopt(self.request.URL, self.url)
        self.request.setopt(self.request.USERPWD, self.userpass)
        if self.proxy:
            self.request.setopt(self.request.PROXY, self.proxy)
        self.request.setopt(self.request.WRITEFUNCTION, self.body_callback)
        return self.request
    
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
            self.request = request
        else:
            self.prepare_request()
        self.request.perform()
    

class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=tuple(), debug=False):
        TwitterStreamGET.__init__(self, user, pword, url, action, debug)
        self.data = data
    
    def prepare_request(self):
        self.request = pycurl.Curl()
        self.request.setopt
        self.request.setopt(self.request.URL, self.url)
        self.request.setopt(self.request.USERPWD, self.userpass)
        if self.proxy:
            self.request.setopt(self.request.PROXY, self.proxy)
        self.request.setopt(self.request.POST, 1)
        self.request.setopt(self.request.POSTFIELDS, urlencode(self.data))
        self.request.setopt(self.request.WRITEFUNCTION, self.body_callback)
        return self.request
    