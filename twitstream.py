#!/usr/bin/env python

import asynchat, asyncore, socket, base64, urllib, sys
import getpass
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

USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream)"

def DEFAULTACTION(status):
    print "%s:\t%s\n" % (status.get('user', {}).get('screen_name'), status.get('text'))
    
class TwitterStreamGET(asynchat.async_chat):
    def __init__(self, user, pword, url, action):
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
        self.inbuf = ""
        self.action = action
        self.set_terminator("\r\n")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.proxy:
            self.connect( self.proxy )
        else:
            self.connect( (self.host, 80) )
    
    def collect_incoming_data(self, data):
        self.inbuf += data
    
    def found_terminator(self):
        if self.inbuf.startswith("HTTP/1") and not self.inbuf.endswith("200 OK"):
            print >> sys.stderr, self.inbuf
        elif self.inbuf.startswith('{'):
            a = json.loads(self.inbuf)
            self.action(a)
        self.inbuf = ""
    
    def handle_connect(self):
        request  = 'GET %s HTTP/1.0\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'User-Agent: %s\r\n' % USERAGENT
        request += '\r\n'
        self.push(request)
    
    def handle_close(self):
        self.close()
    
class TwitterStreamPOST(TwitterStreamGET):
    def __init__(self, user, pword, url, action, data=''):
        TwitterStreamGET.__init__(self, user, pword, url, action)
        self.data = data
    
    def handle_connect(self):
        request  = 'POST %s HTTP/1.0\r\n' % self.url
        request += 'Authorization: Basic %s\r\n' % self.authkey
        request += 'Accept: application/json\r\n'
        request += 'User-Agent: %s\r\n' % USERAGENT
        request += 'Content-Type: application/x-www-form-urlencoded\r\n'
        request += 'Content-Length: %d\r\n' % len(self.data)
        request += '\r\n'
        request += '%s\r\n' % self.data
        self.push(request)
    

parser = OptionParser(usage=USAGE)
parser.add_option('-p', '--password', help="Twitter password")
parser.add_option('-u', '--username', help="Twitter username (required)")

if __name__ == '__main__':
    (options, args) = parser.parse_args()
    if not options.username:
        parser.error("Username required")
    if not options.password:
        options.password = getpass.getpass(prompt='Password for %s: ' % options.username)
    if len(args) < 1:
        parser.error("Require one argument method")
    else:
        method = args[0]
        url = BASEURL % method
    if method in GETMETHODS:
        TwitterStreamGET(options.username, options.password, url, DEFAULTACTION)
    elif method in POSTMETHODS.keys():
        data = POSTMETHODS[method] % ','.join(args[1:])
        TwitterStreamPOST(options.username, options.password, url, DEFAULTACTION, data)
    asyncore.loop()
