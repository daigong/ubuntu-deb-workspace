#encoding:utf-8
import gevent
import contextlib
import logging
import urllib2
from .helper import compress
from .settings import RESPONSE_BUSSINESS_TABLE


MAX_NO_GZIP_LEN = 1024  # 单位字节
TIMEOUT = 300  # 单位秒

logger = logging.getLogger()


class MessageResponse(object):

    def __init__(self, request, client_address, server):
	self.request = request
        self.client_address = client_address
        self.server = server

    def makeResponse(self, line):
        """
            重写makeResponse方法
        """
        num = line[0:8]  # 交易编码
        bussiness_table = RESPONSE_BUSSINESS_TABLE[num]
        return self.getPage(bussiness_table, num, line[8:])

    def getPage(self, bussiness_table, num, raw):
        try:
            with gevent.Timeout(TIMEOUT, True):
                bussiness_url = bussiness_table[0]
                req_url = bussiness_url.replace('{raw}', raw)
                if bussiness_table[1] == 'GET':
                    req = urllib2.Request(req_url)
                else:
                    if '?' in req_url:
                        base_req_url, raw = req_url.split('?')
                    else:
                        base_req_url, raw = req_url, ''
                    req = urllib2.Request(base_req_url, raw)
                req.headers = {'X-Forwarded-For': self.client_address[0]}
                req.get_method = lambda: bussiness_table[1]
                with contextlib.closing(urllib2.urlopen(req)) as response:
                    return self.makeSuccess(num, response.read())
        except BaseException as error:
            return self.makeError(num, error)

    @classmethod
    def makeSuccess(cls, num, response):
        is_gzip = 'n' if len(response) < MAX_NO_GZIP_LEN else 'y'
        result = ''.join([
            num,
            '200',
            is_gzip,
            (compress(response) if is_gzip == 'y' else response)
        ])
        return result

    @classmethod
    def makeError(cls, num, error):
        logger.exception(error)
        code = '500'
        if isinstance(error, urllib2.HTTPError):
            code = str(error.code)
        return ''.join([num, code, 'n'])
