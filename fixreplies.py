#!/usr/bin/env python

import textwrap
import asyncore
import getpass
import re
import sys
import htmlentitydefs
from optparse import OptionGroup
try:
    import json as simplejson
except ImportError:
    import simplejson

import twitter
import twitstream

USAGE = """%prog [options] [user]

Grabs the users that are members of all of the filter sets.
The Streaming API 'follow' method gets each of the named users'
public status messages and the replies to each of them.

Note that there can be a heavy API load at the start, roughly
the number of pages times the number of predicates, so be 
careful!"""

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
        if not st.user:
            if options.debug:
                print >> sys.stderr, status
            return
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
    parser = twitstream.parser
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
    
    if not(options.friends or options.followers or options.favorites or options.mention or options.chat):
        raise StandardError("Require at least one filter to be named")
    
    twitstream.ensure_credentials(options)
    
    a = twitter.Api(username=options.username, password=options.password)
    
    if len(args) > 0:
        user = args[0]
    else:
        user = options.username
    
    follow = dict()
    if options.favorites:
        friends = dict()
        for p in range(options.pages):
            ss = GetFavorites(a, user=user, page=p+1)
            for s in ss:
                friends[str(s.user.id)] = str(s.user.screen_name)
        follow = filter_dict_with_set(follow, friends)
        if options.debug: print "after filtering favorites:", follow
    
    if options.mention:
        friends = dict()
        for p in range(options.pages):
            ss = a.GetReplies(page=p+1)
            for s in ss:
                friends[str(s.user.id)] = str(s.user.screen_name)
        follow = filter_dict_with_set(follow, friends)
        if options.debug: print "after filtering mentions:", follow
    
    if options.chat:
        friends = dict()
        for p in range(options.pages):
            ss = a.GetUserTimeline(screen_name=user, page=p+1, count=100)
            for s in ss:
                if s.in_reply_to_user_id:
                    friends[str(s.in_reply_to_user_id)] = str(s.in_reply_to_screen_name)
        follow = filter_dict_with_set(follow, friends)
        if options.debug: print "after filtering chatters:", follow
    
    if options.friends:
        friends = set(map(str, GetFriendIds(a, screen_name=user)))
        if not follow:
            friends = dict(map(lambda x:(x,''), friends))
        follow = filter_dict_with_set(follow, friends)
        if options.debug: print "after filtering friends:", follow
    
    if options.followers:
        friends = set(map(str, GetFollowerIds(a, screen_name=user)))
        if not follow:
            friends = dict(map(lambda x:(x,''), friends))
        follow = filter_dict_with_set(follow, friends)
        if options.debug: print "after filtering followers:", follow
    
    if options.exclude:
        ss = options.exclude.split(',')
        invdict = dict(map(lambda x:(x[1],x[0]), follow.items()))
        for s in ss:
            if s in invdict:
                del invdict[s]
        follow = dict(map(lambda x:(x[1],x[0]), invdict.items()))
        if options.debug: print "after filtering excludes:", follow
    
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
    
    stream = twitstream.follow(options.username, options.password, prettyprint, follow_ids)
    
    stream.run()
