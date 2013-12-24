from gevent import monkey
monkey.patch_all()

import sys
import getopt
from raven import Client
from raven.contrib.bottle import Sentry
from location.api import application

application.catchall = False
client = Client('http://aa881eaaaa7845a187d23a3b03606a72:2d283126172541249f6f5a6b0e916ea7@sentry.uucin.com/6')
application = Sentry(application, client)


addr, port = '127.0.0.1', 7001
opts, _ = getopt.getopt(sys.argv[1:], "b:")
for opt, value in opts:
    if opt == '-b':
        addr, port = value.split(":")

from gevent.pywsgi import WSGIServer

server = WSGIServer((addr, int(port)), application)
server.backlog = 256
server.max_accept = 30000
server.serve_forever()
