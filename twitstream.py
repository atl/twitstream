#!/usr/bin/env python

import asynchat, asyncore, socket, base64, urllib, sys
import getpass
from urlparse import urlparse
from optparse import OptionParser
from functools import partial

try:
    import json
except ImportError:
    import simplejson as json


USAGE = """usage: %prog <credentials> method [params]

Public methods are 'spritzer', 'follow', and 'track'."""

GETMETHODS  = ['firehose',
               'gardenhose',
               'spritzer',]

POSTPARAMS  = {'birddog': 'follow',
               'shadow':  'follow',
               'follow':  'follow',
               'track':   'track',}

BASEURL = "http://stream.twitter.com/%s.json"

USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream)"

def DEFAULTACTION(status):
    print "%s:\t%s\n" % (status.get('user', {}).get('screen_name'), status.get('text'))
    
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
    

def twitstream(method, user, pword, action, defaultdata=[], debug=False, **kwargs):
    '''General function to set up an asynchat object on twitter. Chooses GET or
    POST according to the API method.
    
    Parameter action is a callable that takes a dict derived from simplejson.
    
    Parameter defaultdata expects an iterable of strings as the default parameter 
    (follow or track) on a POST method. If there are additional parameters you
    wish to use, they can be passed in **kwargs.'''
    url = BASEURL % method
    if method in GETMETHODS:
        return TwitterStreamGET(user, pword, url, action, debug)
    elif method in POSTPARAMS.keys():
        data = {POSTPARAMS[method]: ','.join(defaultdata)}
        data.update(kwargs)
        return TwitterStreamPOST(user, pword, url, action, data, debug)
    else:
        raise NotImplementedError("Unknown method: %s" % method)

firehose   = partial(twitstream, 'firehose')
gardenhose = partial(twitstream, 'gardenhose')
spritzer   = partial(twitstream, 'spritzer')
birddog    = partial(twitstream, 'birddog')
shadow     = partial(twitstream, 'shadow')
follow     = partial(twitstream, 'follow')
track      = partial(twitstream, 'track')

spritzer.__doc__ = "obtain a real-time stream of a subset of all public status messages"
follow.__doc__   = "receive all public status messages from, and all public replies to, the twitter user IDs"
track.__doc__    = "receive all real-time mentions of any of the input terms"

parser = OptionParser(usage=USAGE)
parser.add_option('-p', '--password', help="Twitter password")
parser.add_option('-u', '--username', help="Twitter username (required)")
parser.add_option('--debug', action='store_true', dest='debug', 
                    default=False, help="Print debug information")

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
    twitstream(method, options.username, options.password, DEFAULTACTION, defaultdata=args[1:], debug=options.debug)
    asyncore.loop()
