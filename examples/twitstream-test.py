#!/usr/bin/env python

import twitstream

(options, args) = twitstream.parser.parse_args()
    
if len(args) < 1:
    twitstream.parser.error("requires one method argument")
else:
    method = args[0]
    if method not in twitstream.GETMETHODS and method not in twitstream.POSTPARAMS:
        raise NotImplementedError("Unknown method: %s" % method)

twitstream.ensure_credentials(options)

stream = twitstream.twitstream(method, options.username, options.password, twitstream.DEFAULTACTION, 
            defaultdata=args[1:], debug=options.debug, engine=options.engine)

stream.run()
