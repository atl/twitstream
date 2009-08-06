import asynchat
import asyncore
import socket
import base64
import urllib
import sys
from urlparse import urlparse

try:
    import json
except ImportError:
    import simplejson as json

USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream)"

class TwitterStreamGET(asynchat.async_chat):
    def __init__(self, user, pword, url, action, debug=False):
        asynchat.async_chat.__init__(self)
        self.authkey = base64.b64encode("%s:%s" % (user, pword))
        self.url = url
        self.host = urlparse(url)[1]
        try:
            proxy = urlparse(urllib.getproxies()['http'])[1].split(':')
            proxy[1] = int(proxy[1]) or 80
            self.proxy = tuple(proxy)
        except:
            self.proxy = None
        self.inbuf = ""
        self.action = action
        self.debug = debug
        self.set_terminator("\r\n")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.proxy:
            self.connect( self.proxy )
        else:
            self.connect( (self.host, 80) )
    
    @property
    def request(self):
        request  = 'GET %s HTTP/1.0\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'User-Agent: %s\r\n' % USERAGENT
        request += '\r\n'
        return request
    
    def collect_incoming_data(self, data):
        self.inbuf += data
    
    def found_terminator(self):
        if self.inbuf.startswith("HTTP/1") and not self.inbuf.endswith("200 OK"):
            print >> sys.stderr, self.inbuf
        elif self.inbuf.startswith('{'):
            a = json.loads(self.inbuf)
            self.action(a)
        if self.debug:
            print >> sys.stderr, self.inbuf
        self.inbuf = ""
    
    def handle_connect(self):
        if self.debug:
            print >> sys.stderr, self.request
        self.push(self.request)
    
    def handle_close(self):
        self.close()
    
    @staticmethod
    def run():
        asyncore.loop()
    
    def cleanup(self):
        print >> sys.stderr, self.inbuf
        self.close()

class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=tuple(), debug=False):
        TwitterStreamGET.__init__(self, user, pword, url, action, debug)
        self.data = data
    
    @property
    def request(self):
        data = urllib.urlencode(self.data)
        request  = 'POST %s HTTP/1.0\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'User-Agent: %s\r\n' % USERAGENT
        request += 'Content-Type: application/x-www-form-urlencoded\r\n'
        request += 'Content-Length: %d\r\n' % len(data)
        request += '\r\n'
        request += '%s' % data
        return request
    