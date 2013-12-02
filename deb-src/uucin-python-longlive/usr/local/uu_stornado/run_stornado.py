#encoding:utf-8
from gevent import monkey
monkey.patch_all()


import sys
import getopt
import multiprocessing
from stornado.server import StornadoServer
from stornado.handler import MessageHandler


addr, port = '0.0.0.0', 1001
num_proccesses = multiprocessing.cpu_count()
opts, _ = getopt.getopt(sys.argv[1:], "b:c:")
for opt, value in opts:
    if opt == '-b':
        addr, port = value.split(":")
    elif opt == '-c':
        num_proccesses = int(value)

server = StornadoServer((addr, int(port)), MessageHandler)
server.serve_forever(num_proccesses)
