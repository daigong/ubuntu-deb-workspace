#encoding:utf-8
import sys
import os
import time
import logging
import contextlib
import psycopg2.extras
from bingo.builder.document import DocumentBuilder
from bingo.database import get_postgres_conn, get_xapian_conn, configure


settings = {
    "postgresql.database": "bottle_20130428",
    "postgresql.username": "postgres",
    "postgresql.password": "123456",
    "postgresql.host": "192.168.6.16",
    "postgresql.port": 5432
}

configure(settings)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
count = 0  # 初始化计数


def make_index(sql):
    global count
    with contextlib.closing(get_xapian_conn(False)) as db:
        with contextlib.closing(get_postgres_conn()) as conn:
            with contextlib.closing(
                conn.cursor('all_pois', cursor_factory=psycopg2.extras.DictCursor)
            ) as cursor:
                cursor.execute(sql)
                while True:
                    logger.info("The remaining %d data unhandled" % count)
                    many_result = cursor.fetchmany(3000)
                    if not many_result:
                        break
                    for poi in many_result:
                        builder = DocumentBuilder(poi)
                        doc = builder.build()
                        db.add_document(doc)
                        count = count - 1
                    db.flush()
                    db.commit()


def get_table_list():
    table_list = []
    with open(sys.argv[1]) as f:  # 获取任务列表
        for table in f:
            table_list.append(table.strip())
    return table_list


def run():
    start_time = time.time()
    poi_tables = get_table_list()
    table_count = len(poi_tables)
    print('table count:%s' % table_count)
    for poi_table in poi_tables:
        settings['xapian.database.path'] = os.path.abspath(poi_table)
        os.makedirs(settings['xapian.database.path'])
        configure(settings)
        make_table(poi_table)
        table_count -= 1
        print('table count:%d' % table_count)
    end_time = time.time()
    print('use seconds :%s' % str(end_time - start_time))


def make_table(poi_table):
    global count
    count_sql = 'select count(1) from %s' % poi_table
    with contextlib.closing(get_postgres_conn()) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            cursor.execute(count_sql)
            count = cursor.fetchone()[0]
    make_index("select * from %s" % poi_table)
