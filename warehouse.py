#!/usr/bin/env python

import sys
import twitstream
from urlparse import urlunsplit, urlsplit


# Provide documentation:
USAGE = """%prog [options] [dburl]

Store a real-time subset of all twitter statuses in MongoDB or CouchDB.
The optional dburl is constructed as:
  [mongo|couch]://host:port/path

MongoDB offers up to two levels of path (database/collection), while
CouchDB only uses one. The default is to try CouchDB in preference to
MongoDB on localhost, with a path of "test"."""

class Mongo(object):
    from pymongo.connection import Connection
    from pymongo.objectid import ObjectId
    def __init__(self, location=None, port=None, path=''):
        self.conn = self.Connection(host=location, port=port)
        pth = path.split('/', 1)
        if len(pth) < 1:
            pth.append('test')
        if len(pth) < 2:
            pth.append(pth[0])
        coll = conn[pth[0]]
        self.db = coll[pth[1]]
    
    def status_id(self, num):
        return self.ObjectId('74776974' + ("%x" % num).zfill(16))
    
    def remove(self, num):
        self.db.remove(status_id(num))
    
    def twitsafe(self, status):
        if status.get('id'):
            status['id'] = ('%x' % status['id']).zfill(16)
        if status.get('in_reply_to_status_id'):
            status['in_reply_to_status_id'] = ('%x' % status['in_reply_to_status_id']).zfill(16)
        status['_id'] = self.status_id(status.get('id'))
        return status
    
    def store(self, num, status):
        self.db.save(status)

class Couch(object):
    from couchdb.client import Server
    def __init__(self, location=None, port=None, path=''):
        lp = list([location or 'localhost', port or 5984])
        lp[1] = str(lp[1])
        dburl = urlunsplit(('http', ':'.join(lp), path, '', ''))
        self.conn = self.Server(dburl)
        if not path:
            path = 'test'
        if path not in self.conn:
            self.conn.create(path)
        self.db = self.conn[path]
    
    def status_id(self, num):
        return ("%x" % num).zfill(16)
    
    def remove(self, num):
        del self.db[self.status_id(num)]
    
    def twitsafe(self, status):
        return status
    
    def store(self, num, status):
        self.db[self.status_id(num)] = status


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
                import mongodb
                dburl = 'mongo://'
                del mongodb
        (self.scheme, self.location, self.port, self.path) = self.urlparse(dburl)
        self.db = KNOWN[self.scheme](self.location, self.port, self.path)
    
    def __call__(self, status):
        if status.get('delete'):
            try:
                self.db.remove(status.get('delete').get('status').get('id'))
                print >> sys.stderr, "-",
            except:
                print >> sys.stderr, ",",
            sys.stderr.flush()
        elif status.get('user'):
            self.db.twitsafe(status)
            try:
                self.db.store(status.get('id'), status)
                print >> sys.stderr, ".",
            except ImportError:
                print >> sys.stderr, ";",
            sys.stderr.flush()
        else:
            print >> sys.stderr, '\n' + status
            
    def urlparse(self, url):
        (scheme, foo, rem, bar, baz) = urlsplit(url)
        rem = rem.lstrip('/')
        (locport, foo, path) = rem.partition('/')
        (location, foo, port) = locport.rpartition(':')
        return (scheme, location, port, path)

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
    stream = twitstream.spritzer(options.username, options.password, callback, debug=options.debug)
    
    # Loop forever on the streaming call:
    stream.run()
