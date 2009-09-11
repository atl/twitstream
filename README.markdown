# twitstream #

A super-simple asynchronous python library for speaking with Twitter's
[streaming API][]. Implemented basic authentication and non-authenticating
proxy support in the rudimentary HTTP client.

The idea was to make the least effort possible to get things working. All of
the standard HTTP client libraries seemed to block until the end of
transmission, making them inappropriate for use with the streaming API.

For a Twisted solution, see [twitty-twister][].

[streaming API]: http://apiwiki.twitter.com/Streaming-API-Documentation
[twitty-twister]: http://github.com/dustin/twitty-twister/blob/master/example/feed.py

## Requirements ##

Python 2.5 or higher. If using Python 2.5, also uses [simplejson][] (which is
included in Python 2.6 as [json][]). The more elaborate example programs
`fixreplies.py` and `textori.py` also require the [python-twitter][] library.

If you have [PycURL][] installed, you can benefit from its time-tested,
non-blocking HTTP client implementation. Otherwise, it falls back to the
custom, basic implementation built upon the standard library. Both the
`twitasync.py` and the `twitcurl.py` modules transparently expose the same
basic interface to the main `twitstream.py` module: all typical usage will
focus on the `twitstream` module.

[simplejson]: http://pypi.python.org/pypi/simplejson/
[json]: http://docs.python.org/library/json.html
[python-twitter]: http://code.google.com/p/python-twitter/
[PycURL]: http://pycurl.sourceforge.net/

## Usage ##

Twitstream is usable from the command line as a rudimentary client:

    twitstream.py spritzer
    twitstream.py track ftw fail
    twitstream.py follow 12 13 15 16 20 87

Every usage of the streaming API requires authentication against a user
account. The methods available to the general public are `spritzer`, `track`,
and `follow`.

## textori ##

A simple implementation of a tweet display roughly modeled on [twistori][].
Takes in keywords and pretty-prints a live `track`ing stream from the keywords 
entered. The below-listed keywords are the default setting.

    textori.py love hate think believe feel wish

The code in this example is most notable for the tweet text unescaping and
parsing all accomplished in a single (lengthy) callable.

[twistori]: http://twistori.com/

## fixreplies ##

As a proof-of-concept, there's the modestly-named `fixreplies.py`, which mines
your friends, followers, favorites and/or conversations to derive a list of
people to follow (which can cause a lot of API calls at startup). It then uses
the [streaming API][]'s `follow` method to get all tweets to and from those
chosen users. For example, the following command line will check your latest
500 status messages for people to whom you've replied, and filters out the
people you do not already follow as well as a couple celebrities that everyone
seems to empathize with:

    fixreplies.py --pages 5 --chat --friends --exclude=stephenfry,Oprah

For Mac users, there is a `--growl` option, which uses the [Growl][]
notification framework and its Python interface available in the 
[Growl SDK][]. The class does its best at distinguishing between categories 
of status messages, allowing a user to change display options.

This code example uses a variant upon the status pretty-printing of the
textori example. The chief purpose of this example is to use Twitter's
traditional API in order to get more use out of the streaming API. 

[Growl]: http://growl.info/
[Growl SDK]: http://growl.info/downloads_developers.php

## stats ##

A proof-of-concept showing that you don't need to print out every tweet in the
callback. `stats.py` sets up a counter/histogram on the status characteristic
desired. When halted (interrupted with ctrl-C or a `KeyboardInterrupt`), it
prints a summary of the statistic collected.

    stats.py friends
    stats.py timezone --max 15

## warehouse ##

If you want to examine statistics off-line, the latest batch of schema-free
JSON document stores, like [MongoDB][] or Apache [CouchDB][], make for good
candidates. `warehouse.py` runs the `spritzer` method and stores each status
message in the designated data store. The implementation currently includes
adaptors for MongoDB and CouchDB, and would welcome models for your favorite
ORM+RDBMS.

    warehouse.py
    warehouse.py mongo://localhost:27017/db/twitcollection

The most notable addition in this example is the correct handling of `delete`
updates: it attempts to delete the referenced status message if it is in the
database.

[MongoDB]: http://www.mongodb.org/
[CouchDB]: http://couchdb.apache.org/

# Programming #

The interface provides relatively low-level specialized streaming HTTP GET and
POST classes (currently geared specifically towards Twitter, and provided in
both an [asynchat][] and a [libcurl][] flavor), a general `twitstream`
function that accepts an API method name and routes the software there, and
individual functions that match the API methods (including `spritzer`,
`track`, and `follow`). Each of these returns a request-like object that, when
invoked with the `run()` method, opens the connection and continues into a
loop until interrupted. The only programming you need to provide is a function
(or callable) that gets called with a dictionary containing the latest single
status.

[asynchat]: http://docs.python.org/library/asynchat.html
[libcurl]: http://curl.haxx.se/libcurl/

For example, the basic
[spritz.py](http://github.com/atl/twitstream/blob/master/spritz.py) example
shows the minimum amount of work needed to have a fully working program, using
some built-in facilities for command-line option processing, documentation,
and prompting for a username and password. For something truly minimal, you
could use something like this:

    #!/usr/bin/env python
    
    from twitstream import twitstream
    
    USER = 'test'
    PASS = 'test'
    
    # Define a function/callable to be called on every status:
    def callback(status):
        print "%s:\t%s\n" % (status.get('user', {}).get('screen_name'), status.get('text'))
    
    if __name__ == '__main__':
        # Call a specific API method from the twitstream module: 
        stream = twitstream.spritzer(USER, PASS, callback)
        
        # Loop forever on the streaming call:
        stream.run()
