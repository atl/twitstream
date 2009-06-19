#!/usr/bin/env python

import textwrap
import asyncore
import getpass
import re
import htmlentitydefs
try:
    import json as simplejson
except ImportError:
    import simplejson

import twitter
import twitstream

USAGE = """%prog [options] [user]

Grabs the users who were recently favorited, by pages of 20 
messages, and creates a follow list for those favorite users.
The Streaming API 'follow' method gets each of the named users'
public status messages and the replies to each of them."""

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
            print '\033[7m' + st.user.screen_name + '\033[0m:'
        else:
            print '\033[95m' + st.user.screen_name + ':\033[0m'            
        mess = self.ent_pat.sub(self.unescape, st.text)
        mess = self.wrap.fill(mess)
        mess = self.friend_pat.sub(self.inverse, mess)
        mess = self.user_pat.sub(self.bold, mess)
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
    

if __name__ == '__main__':
    twitstream.parser.add_option('-g', '--pages', help="Number of pages of favorites", type='int', default=3)
    twitstream.parser.usage = USAGE
    (options, args) = twitstream.parser.parse_args()
    
    if not options.username:
        twitstream.parser.error("Username required")
    if not options.password:
        options.password = getpass.getpass(prompt='Password for %s: ' % options.username)
    a = twitter.Api(username=options.username, password=options.password)
    
    if len(args) > 0:
        user = args[0]
    else:
        user = None
    
    fave_friends = set()
    fave_usernames = set()
    for p in range(options.pages):
        ff = GetFavorites(a, user=user, page=p)
        for f in ff:
            fave_friends.add(str(f.user.id))
            fave_usernames.add(str(f.user.screen_name))
    
    print "Following:"
    print status_wrap.fill(", ".join(fave_usernames))
    prettyprint = Formatter(fave_usernames)
    twitstream.follow(options.username, options.password, prettyprint, fave_friends, options.debug)
    
    asyncore.loop()
