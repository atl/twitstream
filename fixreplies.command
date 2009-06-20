#!/usr/bin/env python
"""
Double-clickable from the Mac OS X Finder.

Currently requires simplejson and python-twitter to be installed.
"""
import asynchat, asyncore, socket, base64, urllib, sys
import getpass
import textwrap
import re
import htmlentitydefs
from urlparse import urlparse
from optparse import OptionParser, OptionGroup
from functools import partial
try:
    import json as simplejson
except ImportError:
    import simplejson

import twitter

GETMETHODS  = ['firehose',
               'gardenhose',
               'spritzer',]

POSTPARAMS  = {'birddog': 'follow',
               'shadow':  'follow',
               'follow':  'follow',
               'track':   'track',}

BASEURL = "http://stream.twitter.com/%s.json"

USERAGENT = "twitstream.py (http://www.github.com/atl/twitstream)"


USAGE = """fixreplies.command is a script that provides a realtime stream of
Twitter statuses. It mines your Favorites, Mentions, the users you reply to,
your Friends, and your Followers. It chooses up to 200 users to follow from
the users that are in all of the lists you supply, and then provides a
real-time stream of all public status messages to and from those users.

No passwords are stored or sent anywhere but to Twitter."""

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
            a = simplejson.loads(self.inbuf)
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

tfollow     = partial(twitstream, 'follow')

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


def GetFavorites(api, 
                 user=None,
                 page=None):
    if user:
        url = 'http://twitter.com/favorites/%s.json' % user
    elif not user and not api._username:
        raise twitter.TwitterError("User must be specified if API is not authenticated.")
    else:
        url = 'http://twitter.com/favorites.json'
    parameters = {}
    if page:
        parameters['page'] = page
    json = api._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    api._CheckForTwitterError(data)
    return [twitter.Status.NewFromJsonDict(x) for x in data]


def GetFollowerIds(api, user_id=None, screen_name=None):
    '''Fetch an array of numeric IDs for every user the specified user is followed by. If called with no arguments,
     the results are follower IDs for the authenticated user.  Note that it is unlikely that there is ever a good reason
     to use both of the kwargs.

     Args:
       user_id: Optional.  Specfies the ID of the user for whom to return the followers list.
       screen_name:  Optional.  Specfies the screen name of the user for whom to return the followers list.

    '''
    url = 'http://twitter.com/followers/ids.json'
    parameters = {}
    if user_id:
        parameters['user_id'] = user_id
    if screen_name:
        parameters['screen_name'] = screen_name
    json = api._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    api._CheckForTwitterError(data)
    return data

def GetFriendIds(api, user_id=None, screen_name=None):
    '''Fetch an array of numeric IDs for every user the specified user is followed by. If called with no arguments,
     the results are follower IDs for the authenticated user.  Note that it is unlikely that there is ever a good reason
     to use both of the kwargs.

     Args:
       user_id: Optional.  Specfies the ID of the user for whom to return the followers list.
       screen_name:  Optional.  Specfies the screen name of the user for whom to return the followers list.

    '''
    url = 'http://twitter.com/friends/ids.json'
    parameters = {}
    if user_id:
        parameters['user_id'] = user_id
    elif screen_name:
        parameters['screen_name'] = screen_name
    else:
        raise twitter.TwitterError("One of user_id or screen_name must be specified.")
    json = api._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    api._CheckForTwitterError(data)
    return data

status_wrap = textwrap.TextWrapper(initial_indent='    ', subsequent_indent='    ')

class Formatter(object):
    
    url_pat = re.compile(r'\b(http://\S+[^\s\.\,\?\)\]\>])', re.IGNORECASE)
    ent_pat = re.compile("&#?\w+;")
    user_pat = re.compile(r'(@\w+)')
    wrap = textwrap.TextWrapper(initial_indent='    ', subsequent_indent='    ')
    
    def __init__(self, friends=[]):
        self.friend_pat = re.compile('(@%s)\\b' % "|@".join(friends), re.IGNORECASE)
        self.friends = friends
    
    def __call__(self, status):
        st = twitter.Status.NewFromJsonDict(status)
        if st.user.screen_name in self.friends:
            print '\033[94m\033[1m' + st.user.screen_name + '\033[0m:'
        else:
            print '\033[95m' + st.user.screen_name + ':\033[0m'            
        mess = self.ent_pat.sub(self.unescape, st.text)
        mess = self.wrap.fill(mess)
        mess = self.friend_pat.sub(self.bold, mess)
        mess = self.url_pat.sub(self.underline, mess)
        print mess + '\n'
    
    @staticmethod
    def bold(m):
        return '\033[1m' + m.group(1) + '\033[0m'
    
    @staticmethod    
    def underline(m):
        return '\033[4m' + m.group(1) + '\033[0m'
    
    @staticmethod
    def inverse(m):
        return '\033[7m' + m.group(1) + '\033[0m'
    
    @staticmethod
    def unescape(m):
        "http://effbot.org/zone/re-sub.htm#unescape-html"
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    

def filter_dict_with_set(a, b):
    if not a:
        return b
    else:
        c = a.copy()
        for y in a:
            if y not in b:
                del c[y]
        return c

if __name__ == '__main__':
    parser.add_option('-g', '--pages', help="Number of pages to check (default: 3)", type='int', default=3)
    parser.add_option('-m', '--maximum', help="Maximum number of users to track (default/max: 200)", type='int', default=200)
    group = OptionGroup(parser, "filters",
                        "Combining more than one of the user filters takes the "
                        "intersection of the predicates.")
    group.add_option('--friends', help="Limit to friends", action="store_true", dest='friends')
    group.add_option('--followers', help="Limit to followers", action="store_true", dest='followers')
    group.add_option('--favorites', help="Limit to recent favorites", action="store_true", dest='favorites')
    group.add_option('--mention', help="Limit to those who mention the user", action='store_true', dest='mention')
    group.add_option('--chat', help="Limit to those to whom the user replies", action='store_true', dest='chat')
    group.add_option('--exclude', help="Manually exclude a comma-delimited user list")
    parser.add_option_group(group)
    parser.usage = USAGE
    (options, args) = parser.parse_args()
    
    ensure_credentials(options)
    
    a = twitter.Api(username=options.username, password=options.password)
    
    user = options.username
    
    print USAGE
    
    follow = dict()
    try:
        options.pages = int(raw_input("Number of pages of Favorites to sample: "))
        friends = dict()
        for p in range(options.pages):
            ss = GetFavorites(a, user=user, page=p+1)
            for s in ss:
                friends[str(s.user.id)] = str(s.user.screen_name)
        follow = filter_dict_with_set(follow, friends)
        print "%d user IDs after filtering favorites" % len(follow)
    except:
        pass
    
    try:
        options.pages = int(raw_input("Number of pages of Mentions to sample: "))
        friends = dict()
        for p in range(options.pages):
            ss = a.GetReplies(page=p+1)
            for s in ss:
                friends[str(s.user.id)] = str(s.user.screen_name)
        follow = filter_dict_with_set(follow, friends)
        print "%d user IDs after filtering mentions"% len(follow)
    except:
        pass
    
    try:
        options.pages = int(raw_input("Number of pages of your tweets to sample: "))
        friends = dict()
        for p in range(options.pages):
            ss = a.GetUserTimeline(screen_name=user, page=p+1, count=100)
            for s in ss:
                if s.in_reply_to_user_id:
                    friends[str(s.in_reply_to_user_id)] = str(s.in_reply_to_screen_name)
        follow = filter_dict_with_set(follow, friends)
        print "%d user IDs after filtering chatters" % len(follow)
    except:
        pass
    
    try:
        zz = raw_input("Limit to your friends? ")
        print zz
        assert(zz.startswith(('y','Y')))
        friends = set(map(str, GetFriendIds(a, screen_name=user)))
        if not follow:
            friends = dict(map(lambda x:(x,''), friends))
        follow = filter_dict_with_set(follow, friends)
        print "%d user IDs after filtering friends" % len(follow)
    except AssertionError:
        pass
    
    try:
        zz = raw_input("Limit to your followers? ")
        assert(zz.startswith(('y','Y')))
        friends = set(map(str, GetFollowerIds(a, screen_name=user)))
        if not follow:
            friends = dict(map(lambda x:(x,''), friends))
        follow = filter_dict_with_set(follow, friends)
        print "%d user IDs after filtering followers" % len(follow)
    except AssertionError:
        pass
    
    zz = raw_input("Space-delimited list of users to exclude: ")
    if zz:
        ss = zz.split()
        invdict = dict(map(lambda x:(x[1],x[0]), follow.items()))
        for s in ss:
            if s in invdict:
                del invdict[s]
        follow = dict(map(lambda x:(x[1],x[0]), invdict.items()))
        print "%d user IDs after filtering excludes" % len(follow)
    
    if len(follow) < 1:
        raise StandardError("Sorry, didn't find any people to follow.")
    
    options.maximum = min(200, options.maximum)
    if len(follow) > options.maximum:
        print "found %d, discarding %d..." % (len(follow), len(follow) - options.maximum)
        follow = dict(follow.items()[:options.maximum])
    follow_ids = follow.keys()
    follow_usernames = filter(None, follow.values())
    
    print "Following %d users..." % len(follow)
    if follow_usernames:
        print status_wrap.fill(", ".join(follow_usernames))
    print
    
    prettyprint = Formatter(follow_usernames)
    
    tfollow(options.username, options.password, prettyprint, follow_ids)
    
    asyncore.loop()
