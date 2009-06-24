#!/usr/bin/env python

import sys
import getpass
from optparse import OptionParser, OptionGroup
from functools import partial

try:
    from twitcurl import TwitterStreamGET, TwitterStreamPOST
except ImportError:
    from twitasync import TwitterStreamGET, TwitterStreamPOST

USAGE = """%prog [options] method [params]

Public methods are 'spritzer', 'follow', and 'track'. Follow takes
keywords as parameters, and track takes user IDs."""

GETMETHODS  = ['firehose',
               'gardenhose',
               'spritzer',]

POSTPARAMS  = {'birddog': 'follow',
               'shadow':  'follow',
               'follow':  'follow',
               'track':   'track',}

BASEURL = "http://stream.twitter.com/%s.json"

def DEFAULTACTION(status):
    print "%s:\t%s\n" % (status.get('user', {}).get('screen_name'), status.get('text'))


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
group = OptionGroup(parser, "credentials",
                    "All usage of the Streaming API requires user credentials. "
                    "Will prompt if either of them are missing.")
group.add_option('-p', '--password', help="Twitter password")
group.add_option('-u', '--username', help="Twitter username")
parser.add_option_group(group)
parser.add_option('--debug', action='store_true', dest='debug', 
                    default=False, help="Print debug information")

def ensure_credentials(options):
    if not options.username:
        options.username = raw_input("Twitter username: ")
    if not options.password:
        options.password = getpass.getpass(prompt='Password for %s: ' % options.username)
    return options

if __name__ == '__main__':
    (options, args) = parser.parse_args()
    
    if len(args) < 1:
        parser.error("Require one argument method")
    else:
        method = args[0]
        if method not in GETMETHODS and method not in POSTPARAMS:
            raise NotImplementedError("Unknown method: %s" % method)
    
    ensure_credentials(options)
    
    stream = twitstream(method, options.username, options.password, DEFAULTACTION, defaultdata=args[1:], debug=options.debug)
    
    stream.run()
