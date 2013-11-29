#encoding:utf-8
import os
import re
import chardet
import scseg
from scseg.quantifier import combine_quantifier
from genius import seg_cjk
from genius.digital import *
from genius.tools import StringHelper

here = os.path.abspath(os.path.dirname(__file__))

scseg.core.dict_words = None
scseg.word.Dictionary.dict_words = {}
#encoding:utf-8
import xapian
scseg.core.dict_words = scseg.word.Dictionary(os.path.join(here,'data'))

is_number = re.compile('^[0-9]+[*?]*$').match
group_ascii_cjk_pattern = u'|'.join([StringHelper.ascii_pattern, StringHelper.cjk_pattern])
group_ascii_cjk = re.compile(group_ascii_cjk_pattern, re.UNICODE).findall


def seg_text(text, join_char=';'):
    if not isinstance(text, unicode):
        encoding = chardet.detect(text)['encoding']
        text = unicode(text, encoding)
    text = join_char.join(group_ascii_cjk(text))
    return [word for word in scseg.Splitter(text)]
