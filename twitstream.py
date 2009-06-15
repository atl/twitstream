import asynchat, asyncore, socket, base64, urllib, sys
from urlparse import urlparse
from optparse import OptionParser

try:
    import json
except ImportError:
    import simplejson as json


USAGE = """usage: %prog <credentials> method [params]

Public methods are 'spritzer', 'follow', and 'track'."""

GETMETHODS =  ['firehose',
               'gardenhose',
               'spritzer',]

POSTMETHODS = {'birddog': 'follow=%s',
               'shadow':  'follow=%s',
               'follow':  'follow=%s',
               'track':   'track=%s',}

BASEURL = "http://stream.twitter.com/%s.json"

class TwitterStreamGET(asynchat.async_chat):
    def __init__(self, user, pword, url):
        asynchat.async_chat.__init__(self)
        self.authkey = base64.b64encode("%s:%s" % (user, pword))
        self.url = url
        self.host = urlparse(url)[1]
        try:
            proxy = urlparse(urllib.getproxies()['http'])[1].split(':')
            proxy[1] = int(proxy[1])
            self.proxy = tuple(proxy)
        except:
            self.proxy = None
        self.set_terminator("\r\n")
        self.inbuf = ""
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.proxy:
            self.connect( self.proxy )
        else:
            self.connect( (self.host, 80) )
    
    def collect_incoming_data(self, data):
        self.inbuf += data
    
    def found_terminator(self):
        if self.inbuf.startswith("HTTP/1.0") and not self.inbuf.startswith("HTTP/1.0 2"):
            print >> sys.stderr, self.inbuf
        elif self.inbuf.startswith('{'):
            a = json.loads(self.inbuf)
            print a['text'], '\n'
        self.inbuf = ""
    
    def handle_connect(self):
        request  = 'GET %s HTTP/1.1\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += '\r\n'
        self.push(request)
    
    def handle_close(self):
        self.close()
    
class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, data=''):
        TwitterStreamGET.__init__(self, user, pword, url)
        self.data = data
    
    def handle_connect(self):
        request  = 'POST %s HTTP/1.1\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'Content-Type: application/x-www-form-urlencoded\r\n'
        request += 'Content-Length: %d\r\n' % len(self.data)
        request += '\r\n'
        request += '%s\r\n' % self.data
        self.push(request)
    
if __name__ == '__main__':
    parser = OptionParser(usage=USAGE)
    parser.add_option('-p', '--password', help="Twitter password (required)")
    parser.add_option('-u', '--user', help="Twitter username (required)")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("Require one argument method")
    else:
        method = args[0]
        url = BASEURL % method
    if not (options.password and options.user):
        parser.error("Username and password required")
    if method in GETMETHODS:
        c = TwitterStreamGET(options.user, options.password, url)
    elif method in POSTMETHODS.keys():
        data = POSTMETHODS[method] % ','.join(args[1:])
        d = TwitterStreamPOST(options.user, options.password, url, data)
    asyncore.loop()
