import sys
from gevent.pywsgi import WSGIServer
from gevent import monkey
monkey.patch_all()
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()
from pyramid.paster import get_app, setup_logging


def main(port):
    ini_path = './production.ini'
    setup_logging(ini_path)
    app = get_app(ini_path, 'main')
    server = WSGIServer(('', port), app)
    server.backlog = 256
    server.serve_forever()

if __name__ == "__main__":
    main(int(sys.argv[1]))
