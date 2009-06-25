#!/usr/bin/env python

from collections import defaultdict
import types
import re
import math

# The key module provided here:
import twitstream

# Provide documentation:
USAGE = """stats.py [options] <key>

Extract statistics from the spritzer stream until interrupted.
Potential keys are: %s"""

link_re = re.compile(">([^<]+)</a>")

def linked(string):
    m = link_re.search(string)
    if m:
        return m.groups()[0]
    else:
        return string

def log_spacing(integer):
    m = math.sqrt(10)
    if integer == 0:
        return 0
    return m ** math.floor(math.log(integer, m))

def lin_len(string):
    return 10 * math.floor(len(string)/10)
    
class Counter(object):
    def __init__(self, field):
        self.field = field
        self.path = self.FIELDS[field]
        self.counter = defaultdict(int)
        self.col = 0
    
    def __call__(self, status):
        key = status
        for elem in self.path:
            if isinstance(elem, types.FunctionType) or isinstance(elem, types.BuiltinFunctionType):
                key = elem(key)
            else:
                key = key[elem]
        self.counter[key] += 1
        print ".",
        self.col += 1
        if self.col > 36:
            print "\n"
            self.col = 0
    
    def top(self, count):
        if self.field in self.UNORDERED:
            hist = sorted(self.counter.items(), key=lambda x: x[1], reverse=True)
            for val in hist[:count]:
                print "%6d:\t%s\n" % (val[1], val[0])
        else:
            hist = sorted(self.counter.items(), key=lambda x: x[0])
            for val in hist:
                print "%6d:\t%d\n" % val
    
    FIELDS = {'source': ('source', linked),
              'client': ('source', linked),
              'user':   ('user', 'screen_name'),
              'timezone': ('user', 'time_zone'),
              'followers': ('user', 'followers_count', log_spacing),
              'friends': ('user', 'friends_count', log_spacing),
              'favourites': ('user', 'favourites_count', log_spacing),
              'favorites': ('user', 'favourites_count', log_spacing),
              'statuses': ('user', 'statuses_count', log_spacing),
              'length':   ('text', lin_len),
              }

    UNORDERED = set(('source', 'client', 'user', 'timezone'))

if __name__ == '__main__':
    # Inherit the built in parser and use it to get credentials:
    parser = twitstream.parser
    parser.usage = USAGE % ", ".join(Counter.FIELDS)
    parser.add_option('-m', '--maximum', help="Maximum number of results to print (for non-numerical lists) (default: 5, -1 for all)", type='int', default=5)
    (options, args) = parser.parse_args()
    
    if len(args) == 1 and args[0] in Counter.FIELDS:
        field = args[0]
    else:
        raise NotImplementedError("Requires exactly one argument from %s" % ", ".join(FIELDS.keys()))
    
    twitstream.ensure_credentials(options)            
    count = Counter(field)
    # Call a specific API method in the twitstream module: 
    stream = twitstream.spritzer(options.username, options.password, count, debug=options.debug)
    
    # Loop forever on the streaming call:
    try:
        stream.run()
    except: 
        stream.cleanup()
        print count.top(options.maximum)
    
