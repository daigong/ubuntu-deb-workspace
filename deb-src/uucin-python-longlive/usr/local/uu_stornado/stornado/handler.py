#encoding:utf-8
import uuid
import random
import gevent
import logging
from Crypto.Cipher import AES
from .server import BaseRequestHandler
from .response import MessageResponse


logger = logging.getLogger()


class LineHandler(BaseRequestHandler):

    delimiter = '\r\n'
    MAX_LENGTH = 1048576

    def __init__(self, request, client_address, server):
        BaseRequestHandler.__init__(self, request, client_address, server)
        self.connection_closed = False
        self._buffer = ''
        self.timeout = 60 * 5

    def clearLineBuffer(self):
        """
        Clear buffered data.
        @return: All of the cleared buffered data.
        @rtype: C{str}
        """
        b = self._buffer
        self._buffer = ""
        return b

    def setTimeout(self, timeout):
        self.timeout = timeout

    def sendLine(self, line):
        self.request.sendall(line + self.delimiter)

    def handle(self):
        """
        socket handle
        """
        while not self.connection_closed:
            raw = None
            with gevent.Timeout(self.timeout, False):
                raw = self.request.recv(1024)
            if not raw:
                break
            self._buffer = self._buffer + raw
            line_split = self._buffer.split(self.delimiter)
            if len(line_split) > 1:
                for line in line_split[:-1]:
                    if len(line) < 2:  # 心跳包
                        self.sendLine(line)
                    else:
                        self.lineReceived(line)
                del self._buffer
                self._buffer = line_split[-1]
            elif len(self._buffer) > self.MAX_LENGTH:
                break

    def lineReceived(self, line):
        pass

    def destroy(self):
        self.close()

    def close(self):
        self.connection_closed = True


class MessageHandler(LineHandler):

    key = '$9Zz\xee\xb4h\xa8\xf4h\x01g8\x19\xffc'
    response_class = MessageResponse

    def setup(self):
        """
        此处连接生成时执行
        """
        self.delimiter = uuid.uuid4().bytes
        ciph, iv = self.encrypt_by_aes_cbc(self.delimiter)
        self.request.sendall(iv + ciph)
        self.connection_closed = False
        raw = None
        with gevent.Timeout(self.timeout, False):
            raw = self.request.recv(16)
        if raw != self.delimiter:
            self.close()

    def encrypt_by_aes_cbc(self, data):
        ivParameterSpec = ''.join(
            chr(random.randint(0, 255)) for _ in range(16))
        encryptor = AES.new(self.key, AES.MODE_CBC, ivParameterSpec)
        ciph = encryptor.encrypt(data)
        return ciph, ivParameterSpec

    def lineReceived(self, line):
        response = MessageResponse(
            self.request, self.client_address, self.server)
        self.sendLine(response.makeResponse(line))
