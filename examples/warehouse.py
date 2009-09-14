#!/usr/bin/env python

import sys
from twitstream import twitstream
from urlparse import urlunsplit, urlsplit
from binascii import unhexlify, hexlify


# Provide documentation:
USAGE = """%prog [options] [dburl]

Store a real-time subset of all twitter statuses in MongoDB or CouchDB.
The optional dburl is constructed as:
  [mongo|couch]://host:port/path

MongoDB offers up to two levels of path (database/collection), while
CouchDB uses one. The default behavior is to try CouchDB first, falling
back to MongoDB on localhost, with a path of "test" (or "test/test")."""

class Mongo(object):
    from pymongo.connection import Connection
    from pymongo.objectid import ObjectId
    def __init__(self, location=None, port=None, path=''):
        if not port:
            port = None
        self.conn = self.Connection(host=location, port=port)
        (pathdb, foo, pathcoll) = path.partition('/')
        if not pathdb:
            pathdb = 'test'
        if not pathcoll:
            pathcoll = pathdb
        self.data = self.conn[pathdb][pathcoll]
    
    def status_id(self, num):
        """Derive an ObjectID from the status id."""
        return self.ObjectId(unhexlify('74776974' + ("%x" % num).zfill(16)))
    
    def remove(self, num):
        self.data.remove(self.status_id(num))
    
    def twitsafe(self, status):
        """Change Longs to hex strings to work around MongoDB's assumption
        of 32-bit ints."""
        status['_id'] = self.status_id(status.get('id'))
        if status.get('id'):
            status['id'] = ('%x' % status['id']).zfill(16)
        if status.get('in_reply_to_status_id'):
            status['in_reply_to_status_id'] = ('%x' % status['in_reply_to_status_id']).zfill(16)
        return status
    
    def store(self, num, status):
        self.data.save(status)

class Couch(object):
    from couchdb.client import Server
    def __init__(self, location=None, port=None, path=''):
        lp = list([location or 'localhost', port or 5984])
        lp[1] = str(lp[1])
        dburl = urlunsplit(('http', ':'.join(lp), '', '', ''))
        self.conn = self.Server(dburl)
        if not path:
            path = 'test'
        if path not in self.conn:
            self.data = self.conn.create(path)
        else:
            self.data = self.conn[path]
    
    def status_id(self, num):
        return ("%x" % num).zfill(16)
    
    def remove(self, num):
        del self.data[self.status_id(num)]
    
    def twitsafe(self, status):
        return status
    
    def store(self, num, status):
        self.data[self.status_id(num)] = status


KNOWN = {'mongo': Mongo,
         'couch': Couch}


class Warehouse(object):
    def __init__(self, dburl=''):
        if not dburl:
            try:
                import couchdb
                dburl = 'couch://'
                del couchdb
            except ImportError:
                import pymongo
                dburl = 'mongo://'
                del pymongo
        (self.scheme, self.location, self.port, self.path) = self.urlparse(dburl)
        self.db = KNOWN[self.scheme](self.location, self.port, self.path)
    
    def __call__(self, status):
        if status.get('delete'):
            try:
                self.db.remove(status.get('delete').get('status').get('id'))
                print >> sys.stderr, "-",
            except Exception:
                print >> sys.stderr, ",",
            sys.stderr.flush()
        elif status.get('user'):
            idnum = status.get('id')
            self.db.twitsafe(status)
            try:
                self.db.store(idnum, status)
                print >> sys.stderr, ".",
            except Exception:
                print >> sys.stderr, ";",
            sys.stderr.flush()
        else:
            print >> sys.stderr, '\n' + status
            
    def urlparse(self, url):
        (scheme, foo, rem, bar, baz) = urlsplit(url)
        rem = rem.lstrip('/')
        (locport, foo, path) = rem.partition('/')
        (location, foo, port) = locport.partition(':')
        if not port: port = 0
        return (scheme, location, int(port), path)

if __name__ == '__main__':
    # Inherit the built in parser and use it to get credentials:
    parser = twitstream.parser
    parser.usage = USAGE
    (options, args) = parser.parse_args()
    twitstream.ensure_credentials(options)
    if args:
        dburl = args[0]
    else:
        dburl = ''
    
    callback = Warehouse(dburl)
    
    # Call a specific API method in the twitstream module: 
    stream = twitstream.spritzer(options.username, options.password, callback,
                                 debug=options.debug, engine=options.engine)
    
    # Loop forever on the streaming call:
    try:
        stream.run()
    finally:
        stream.cleanup()
    
