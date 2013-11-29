import psycopg2,contextlib
import psycopg2.extras

import re

split = re.compile('[^a-z]').split

def getConnection():
    return psycopg2.connect(database='emg_org0',\
            user='postgres',\
            password='postgres123',\
            host='192.168.6.20') 


def main(sql):
    count = 0
    f = open("crf_pinyin_training.txt","w")
    str_tmpl = '%s\tPINYIN\t%s\n'
    with contextlib.closing(getConnection()) as conn:
        with contextlib.closing(conn.cursor('all_pois',cursor_factory=psycopg2.extras.DictCursor)) as cursor:
            cursor.execute(sql)
            while True:
                many_result = cursor.fetchmany(3000)
                if not many_result:
                    break
                for pinyins in many_result:
                    count += 1
                    for pinyin in split(pinyins[0]):
                        pinyin_length = len(pinyin)
                        for i in range(pinyin_length):
                            if pinyin_length == 1:
                                f.write(str_tmpl % (pinyin[i],'S'))
                            elif i == 0:
                                f.write(str_tmpl % (pinyin[i],'B'))
                            elif i == 1 and pinyin_length > 3:
                                f.write(str_tmpl % (pinyin[i],'B1'))
                            elif i == 2 and pinyin_length > 4:
                                f.write(str_tmpl % (pinyin[i],'B2'))
                            elif i == pinyin_length - 1:
                                f.write(str_tmpl % (pinyin[i],'E'))
                            else:
                                f.write(str_tmpl % (pinyin[i],'M'))
                print("count:%d" % count)
    f.close()

sql = """
SELECT strprontext
  FROM oes.servname
where strprontext is not null and strprontext <> ''"""
main(sql)
