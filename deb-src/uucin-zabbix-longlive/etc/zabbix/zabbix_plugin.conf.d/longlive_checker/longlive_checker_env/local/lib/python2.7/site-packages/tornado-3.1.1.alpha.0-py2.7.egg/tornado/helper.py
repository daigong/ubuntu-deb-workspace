#encoding:utf-8
from StringIO import StringIO
import gzip,urllib
#压缩
def compress(raw): 
    out_file=StringIO()
    try:
        with gzip.GzipFile(fileobj=out_file,mode="wb") as gzip_out:
            gzip_out.write(raw)
            gzip_out.flush()
            gzip_out.close()
        out_file.seek(0)
        return out_file.read()
    finally:
        out_file.close()
#解压
def uncompress(raw):
    file_in=StringIO(raw)
    try:
        gzip_in=gzip.GzipFile(fileobj=file_in,mode="r")
        return gzip_in.read()
    finally:
        file_in.close()

def urldecode(query,charset="utf-8"):
    d = {}
    a = query.split('&')
    for s in a:
        if s.find('='):
            k,v = map(urllib.unquote, s.split('='))
            try:
                d[k]=v.decode(charset)
            except KeyError:
                d[k] = [v]
    return d
