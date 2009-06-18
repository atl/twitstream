#!/usr/bin/env python

import textwrap
import asyncore
import getpass
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

def prettyprint(status):
    st = twitter.Status.NewFromJsonDict(status)
    print '\033[94m' + st.user.screen_name + ':\033[0m'
    print status_wrap.fill(st.text)

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
    
    twitstream.follow(options.username, options.password, prettyprint, fave_friends, options.debug)
    
    asyncore.loop()
