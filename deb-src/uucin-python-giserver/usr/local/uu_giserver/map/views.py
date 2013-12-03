#encoding:utf-8
import os
import struct
from contextlib import closing
from django.conf import settings
from django.http import HttpResponse

DEFAULT_GRID_FILE = {
    4294967295: "4294967295.png",  # 陆地空图片默认背景
    4294967294: "4294967294.png",  # 陆地
    4294967293: "4294967293.png",  # 海洋空图片默认背景
    4294967292: "4294967292.png",  # 水体
}


def send_grid_file(request, version, scale, x, y, index):
    grid_file_path = os.sep.join([
        settings.MAP_FILE_PATH,
        version,
        'grid',
        scale,
        x,
        y,
    ])
    default_grid_file_path = os.sep.join([
        settings.MAP_FILE_PATH,
        version,
        'grid',
        'default',
    ])
    response = HttpResponse(content_type='image/png')
    response['Cache-Control'] = 'max-age=31536000'
    if os.path.exists(grid_file_path):
        with closing(file(grid_file_path)) as grid_file:
            grid_file.seek(int(index))
            offsize = struct.unpack(">I", grid_file.read(4))[0]
            if offsize < 4294967280:  # 有效值
                size = struct.unpack(">I", grid_file.read(4))[0]
                grid_file.seek(offsize)
                response.write(grid_file.read(size))
            else:
                path = os.sep.join([
                    default_grid_file_path,
                    DEFAULT_GRID_FILE[offsize],
                ])
                with closing(file(path)) as grid_file:
                    response.write(grid_file.read())
    else:  # 不存在返回默认值
        if int(scale) < 25000:  # 陆地空图背景
            path = os.sep.join([
                default_grid_file_path,
                DEFAULT_GRID_FILE[4294967295],
            ])
        else:  # 海洋空图片背景
            path = os.sep.join([
                default_grid_file_path,
                DEFAULT_GRID_FILE[4294967293],
            ])
        with closing(file(path)) as grid_file:
            response.write(grid_file.read())
    return response


def send_text_file(request, version, scale, x, y, index):
    text_file_path = os.sep.join([
        settings.MAP_FILE_PATH,
        version,
        'text',
        scale,
        x,
        y,
    ])
    callback = request.REQUEST.get("callback", "callback")
    response = HttpResponse(content_type='text/javascript; charset=UTF-8')
    response['Cache-Control'] = 'max-age=31536000'
    response.status_code = 204
    if os.path.exists(text_file_path):
        with closing(file(text_file_path)) as text_file:
            text_file.seek(int(index))
            offsize = struct.unpack(">I", text_file.read(4))[0]
            if offsize != 4294967295:  # 有效值
                size = struct.unpack(">I", text_file.read(4))[0]
                text_file.seek(offsize)
                response.write("%s(%s)" % (callback, text_file.read(size).decode("utf-8")))
                response.status_code = 200
    return response
