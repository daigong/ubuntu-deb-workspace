#encoding:utf-8
import os
from bingo.database import get_postgres_conn
import contextlib
from bingo.cjk import seg_text as seg_text

poi_type_keywords = {}
poi_brand_type_keywords = {}
address_ends = set()
here = os.path.abspath(os.path.dirname(__file__))


def __init__():
    if not poi_brand_type_keywords:
        poi_brand_type_keywords_path = os.path.join(here, '../data/poi_brand_type_keywords')
        with open(poi_brand_type_keywords_path) as f:
            for line in f:
                line = line.decode('utf-8').rstrip('\r\n')
                params = line.split('\t')
                if len(params) == 2 and params[1]:
                    poi_brand_type_keywords[int(params[0])] = params[1]
    if not poi_type_keywords:
        poi_type_keywords_path = os.path.join(here, '../data/poi_type_keywords')
        with open(poi_type_keywords_path) as f:
            for line in f:
                params = line.decode("utf-8").rstrip('\r\n').split('\t')
                if len(params) == 2 and params[1]:
                    poi_type_keywords[int(params[0])] = params[1].rstrip('\r\n')
    if not address_ends:
        address_ends_file = os.path.join(here, '../data/address.ends')
        with open(address_ends_file) as f:
            for line in f:
                line = line.decode('utf-8').rstrip('\r\n')
                address_ends.add(line)


def get_poi_brand_keywords(poi_id):
    sql = "select brand_type from geo.poi_brand_relation where id = %s" % poi_id
    with contextlib.closing(get_postgres_conn()) as conn:
        with contextlib.closing(conn.cursor('poi_brand_relation')) as cursor:
            cursor.execute(sql)
            for brand_type in cursor:
                if brand_type in poi_brand_type_keywords:
                    for keyword in seg_text(poi_brand_type_keywords[brand_type]):
                        yield keyword
    raise StopIteration()


def get_poi_type_keywords(original_type):
    if original_type in poi_type_keywords:
        return seg_text(poi_type_keywords[original_type])
    return ()


def filter_admin_name(base_term):
    index = len(base_term)
    if index > 1 and base_term[-1:] in address_ends:
        index = -1
    elif index > 2 and base_term[-2:] in address_ends:
        index = -2
    elif index > 3 and base_term[-3:0] in address_ends:
        index = -3
    if index < 0:
        return base_term[:index]
    else:
        return None


# 初始化数据
__init__()
