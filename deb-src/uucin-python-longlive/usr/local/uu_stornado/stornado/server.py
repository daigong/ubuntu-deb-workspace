from gevent import monkey
monkey.patch_all()

import os
import logging
import contextlib
import multiprocessing
from gevent.server import StreamServer

logger = logging.getLogger()
here = os.path.abspath(os.path.dirname(__file__))


class BaseRequestHandler(object):

    """Base class for request handler classes.

    This class is instantiated for each request to be handled.  The
    constructor sets the instance variables request, client_address
    and server, and then calls the handle() method.  To implement a
    specific service, all you need to do is to derive a class which
    defines a handle() method.

    The handle() method can find the request as self.request, the
    client address as self.client_address, and the server (in case it
    needs access to per-server information) as self.server.  Since a
    separate instance is created for each request, the handle() method
    can define arbitrary other instance variariables.

    """

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server

    def setup(self):
        """
        The start handler must perform setup method
        """
        pass

    def handle(self):
        pass

    def finish(self):
        """
        If the successful execution of the handler, will run this method
        """
        pass

    def destroy(self):
        """
        Called after this handler lifecycle
        """
        pass


class BaseServer(StreamServer):

    def __init__(self, listener, request_handler=None):
        StreamServer.__init__(self, listener)
        self.request_handler = request_handler

    @classmethod
    def start_request(cls, request_handler, client_address):
        """
        Start a request,this method does not allow an exception is thrown.
        """
        logger.debug('start_request(%s:%s)' % client_address)

    @classmethod
    def verify_request(cls, request_handler, client_address):
        """
        Verify request,this method does not allow an exception is thrown.
        """
        logger.debug('verify_request(%s:%s)' % client_address)

    def handle(self, client_socket, client_address):
        with contextlib.closing(client_socket):
            request_handler = self.request_handler(
                client_socket, client_address, self)
            self.start_request(request_handler, client_address)
            self.verify_request(request_handler, client_address)
            try:
                request_handler.setup()
                request_handler.handle()
                request_handler.finish()
            except BaseException as e:
                logger.exception(e)
                self.handle_error(request_handler, client_address)
            finally:
                request_handler.destroy()
                self.close_request(request_handler, client_address)

    @classmethod
    def handle_error(cls, request_handler, client_address):
        """
        Handler is called when an exception occurs
        """
        logger.debug('handle_error(%s:%s)' % client_address)

    @classmethod
    def close_request(cls, request_handler, client_address):
        """
        Closing request called
        """
        logger.debug('close_request(%s:%s)' % client_address)


class StornadoServer(BaseServer):

    def __init__(self, listener, request_handler):
        BaseServer.__init__(self, listener, request_handler=request_handler)
        self.backlog = 100000
        self.max_accept = 100
        self.timeout = 300
        self.min_delay = 0.01
        self.max_delay = 1
        self.stop_timeout = 1

    def _serve_forever(self):
        self.start_accepting()
        self._stopped_event.wait()

    def serve_forever(self, num_proccesses=1):
        self.pre_start()
        for _ in range(num_proccesses - 1):
            multiprocessing.Process(target=self._serve_forever).start()
        self._serve_forever()
