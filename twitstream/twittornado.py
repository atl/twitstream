import socket
import base64
import urllib
import sys
from urlparse import urlparse
from tornado import iostream, ioloop
try:
    import json
except ImportError:
    import simplejson as json
import ssl

# Yes, this is very strongly based upon the twitasync approach.
# There was little call to change my approach on a first pass,
# and the IOStream interface is very similar to asyncore/asynchat.

USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream), using tornado.iostream"

class TwitterStreamGET(object):
    def __init__(self, user, pword, url, action, debug=False, preprocessor=json.loads):
        self.authkey = base64.b64encode("%s:%s" % (user, pword))
        self.preprocessor = preprocessor
        self.url = url
        self.host = urlparse(url)[1]
        try:
            proxy = urlparse(urllib.getproxies()['https'])[1].split(':')
            proxy[1] = int(proxy[1]) or 443
            self.proxy = tuple(proxy)
        except:
            self.proxy = None
        self.action = action
        self.debug = debug
        self.terminator = "\r\n"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = None
        if self.proxy:
            self.connect( self.proxy )
        else:
            self.connect( (self.host, 443) )
    
    @property
    def request(self):
        request  = 'GET %s HTTP/1.0\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'User-Agent: %s\r\n' % USERAGENT
        request += '\r\n'
        return request
    
    def connect(self, host):
        self.sock.connect(host)
        self.sock = ssl.wrap_socket(self.sock, do_handshake_on_connect=False)
        self.stream = iostream.SSLIOStream(self.sock)
    
    def found_terminator(self, data):
        if data.startswith("HTTP/1") and not data.endswith("200 OK\r\n"):
            print >> sys.stderr, data
        if data.startswith('{'):
            if self.preprocessor:
                a = self.preprocessor(data)
            else:
                a = data
            self.action(a)
        if self.debug:
            print >> sys.stderr, data
        self.stream.read_until(self.terminator, self.found_terminator)
        
    def run(self):
        self.stream.write(self.request)
        self.stream.read_until(self.terminator, self.found_terminator)
        ioloop.IOLoop.instance().start()
    
    def cleanup(self):
        self.stream.close()

class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=tuple(), debug=False, preprocessor=json.loads):
        TwitterStreamGET.__init__(self, user, pword, url, action, debug, preprocessor)
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
