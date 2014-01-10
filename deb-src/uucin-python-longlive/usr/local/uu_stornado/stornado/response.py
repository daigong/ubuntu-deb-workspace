#encoding:utf-8
import gevent
import logging
from requests import Session
from .settings import RESPONSE_BUSSINESS_TABLE


logger = logging.getLogger()


class MessageResponse(object):

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.timeout = server.timeout
        self.session = Session()

    def makeResponse(self, line):
        """
            重写makeResponse方法
        """
        num = line[0:8]  # 交易编码
        bussiness_table = RESPONSE_BUSSINESS_TABLE[num]
        return self.getPage(bussiness_table, num, line[8:])

    def request_url(self, method, url, data, headers):
        response = self.session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            stream=True
        )
        content = response.raw.read()
        content_encoding = response.headers.get(
            'content-encoding', ''
        ).lower()
        status_code = str(response.status_code)
        return {
            'is_gzip': 'y' if content_encoding == 'gzip' else 'n',
            'content': content,
            'status_code': status_code,
        }

    def getPage(self, bussiness_table, num, raw):
        try:
            with gevent.Timeout(self.timeout, True):
                bussiness_url = bussiness_table[0]
                req_url = bussiness_url.replace('{raw}', raw)
                method = bussiness_table[1]
                headers = {
                    'Accept-Encoding': 'gzip',
                    'X-Forwarded-For': self.client_address[0],
                }
                if method == 'GET' or method == 'DELETE':
                    url, body = req_url, None
                else:
                    headers.update({
                        'Content-type': 'application/x-www-form-urlencoded'
                    })
                    if '?' in req_url:
                        url, body = req_url.split('?')
                    else:
                        url, body = req_url, None
                response = self.request_url(method, url, body, headers)
                return self.makeResult(num, **response)
        except BaseException as e:
            logger.exception(e)
            return self.makeResult(num)

    @classmethod
    def makeResult(cls, num, **kwargs):
        is_gzip = kwargs.get('is_gzip', 'n')
        content = kwargs.get('content', '')
        status_code = kwargs.get('status_code', '500')
        result = ''.join([
            num,
            status_code,
            is_gzip,
            content,
        ])
        return result

    def close(self):
        self.session.close()
