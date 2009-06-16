#!/usr/bin/python

import textwrap
import asyncore
try:
    import json as simplejson
except ImportError:
    import simplejson

import twitter
import twitstream

def GetFavorites(api, 
                 user=None,
                 page=None):
    if user:
        url = 'http://twitter.com/favorites/%s.json' % user
    elif not user and not api._username:
        raise TwitterError("User must be specified if API is not authenticated.")
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

twitstream.parser.add_option('-g', '--pages', help="Number of pages of favorites", type='int', default=3)

if __name__ == '__main__':
    (options, args) = twitstream.parser.parse_args()
    if not (options.password and options.username):
        twitstream.parser.error("Username and password required")
    a = twitter.Api(username=options.username, password=options.password)
    if len(args) == 1:
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
    method = 'follow'
    print "Following:"
    print status_wrap.fill(", ".join(fave_usernames))
    url = twitstream.BASEURL % method
    data = twitstream.POSTMETHODS[method] % ','.join(fave_friends)
    d = twitstream.TwitterStreamPOST(options.username, options.password, url, prettyprint, data)
    asyncore.loop()
