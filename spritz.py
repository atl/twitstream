#!/usr/bin/env python

# The two modules needed externally:
import getpass, asyncore

# The key module provided here:
import twitstream

# Provide documentation:
USAGE = """%prog [options] 

Show a real-time subset of all twitter statuses."""

# Define a function/callable called on every status:
def callback(status):
    print "%s:\t%s\n" % (status.get('user', {}).get('screen_name'), status.get('text'))

if __name__ == '__main__':
    # Inherit the built in parser and use it to get credentials:
    parser = twitstream.parser
    parser.usage = USAGE
    (options, args) = parser.parse_args()
    twitstream.ensure_credentials(options)
    
    # Call a specific API method in the twitstream module: 
    stream = twitstream.spritzer(options.username, options.password, callback, debug=options.debug)
    
    # Loop forever on the streaming call:
    stream.run()
