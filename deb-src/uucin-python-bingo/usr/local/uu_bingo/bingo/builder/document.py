#encoding:utf-8
import json
import re
import logging
import xapian
from bingo.cjk import seg_text as seg_text
from bingo.cjk import is_chinese_number, chinese_to_number, is_number
from .helper import get_poi_brand_keywords, get_poi_type_keywords, filter_admin_name
from bingo import pinyin


group_letter_pattern = u'[a-z]+[*?]*|[A-Z]+[*?]*'
group_letters = re.compile(group_letter_pattern, re.UNICODE).findall
logger = logging.getLogger()


class DocumentBuilder(object):

    def __init__(self, data):
        self.data = data
        self.doc = xapian.Document()

    def build(self):
        self.make_id()
        self.make_original_data()
        self.make_mini_type()
        self.make_admin_code()
        self.make_post_code()
        self.make_latitude_longitude()
        self.make_prov_code()
        self.make_city_code()
        self.make_heat_code()
        self.make_poi_name()
        self.make_remark()
        self.make_first_letters()
        self.make_all_letters()
        self.make_address()
        self.make_tel_num()
        self.make_original_name()
        self.make_brand_name()
        return self.doc

    def make_id(self):
        _id = str(self.data['id'])
        self.doc.add_term('ID' + _id)

    def make_original_data(self):
        m = {}
        for key in self.data.keys():
            if key not in ['lat', 'lon', 'timestamp']:
                m[key] = self.data[key]
        lon = self.data['lon'] / (2560 * 3600.0)
        lat = self.data['lat'] / (2560 * 3600.0)
        m['lat'] = lat
        m['lon'] = lon
        dump_data = json.dumps(m)
        logger.debug("doc data:%s" % dump_data)
        self.doc.set_data(dump_data)

    def make_mini_type(self):
        mini_type = self.data['min_type']
        logger.debug('min_type %d' % mini_type)
        self.doc.add_value(0, xapian.sortable_serialise(int(mini_type)))

    def make_admin_code(self):
        admin_code = self.data['admin_code']
        logger.debug('admin_code %d' % admin_code)
        self.doc.add_value(1, xapian.sortable_serialise(int(admin_code)))

    def make_post_code(self):
        post_code = self.data['post_code']
        if not post_code:
            return
        logger.debug('post_code %d' % post_code)
        self.doc.add_value(2, xapian.sortable_serialise(int(post_code)))

    def make_latitude_longitude(self):
        lon = self.data['lon'] / (2560 * 3600.0)
        lat = self.data['lat'] / (2560 * 3600.0)
        logger.debug('lat,lon %f,%f' % (lat, lon))
        coords = xapian.LatLongCoords()
        coords.append(xapian.LatLongCoord(lat, lon))
        self.doc.add_value(3, coords.serialise())

    def make_prov_code(self):
        prov_code = self.data['prov_code']
        logger.debug('prov_code %d' % prov_code)
        self.doc.add_value(4,  xapian.sortable_serialise(int(prov_code)))

    def make_city_code(self):
        city_code = self.data['city_code']
        logger.debug('city_code %d' % city_code)
        self.doc.add_value(5,  xapian.sortable_serialise(int(city_code)))

    def make_heat_code(self):
        heat_code = self.data.get('heat_code', 0)
        if heat_code:
            logger.debug('heat_code %d' % heat_code)
            self.doc.add_value(6, xapian.sortable_serialise(int(heat_code)))

    def add_simple_posting(self, text, field, add_full_text=True):
        if not text:
            return
        logger.debug("debug name:%s" % text)
        terms = seg_text(text)
        for term in terms:
            fadmin_name = filter_admin_name(term)
            if fadmin_name:
                self.doc.add_term(field + fadmin_name)
            if is_chinese_number(term):
                self.doc.add_term(field + 'D' + unicode(chinese_to_number(term)))
            if is_number(term):
                self.doc.add_term(field + 'D' + unicode(term))
            if term not in text:
                self.doc.add_term(field + term)
            else:
                index = text.index(term)
                self.doc.add_posting(field + term, index)
        if add_full_text and len(terms) != 1:
            self.doc.add_term(field + text)

    def make_poi_name(self):
        poi_shortname = self.data['poi_shortname'].lower().strip()
        if poi_shortname:
            self.add_simple_posting(poi_shortname, 'PN')
        poi_name = self.data['poi_name'].lower().strip()
        logger.debug('poi_name %s' % poi_name)
        self.add_simple_posting(poi_name, 'PN')

    def make_remark(self):
        remark = self.data.get('remark','')
        if not remark:
            return
        remark = remark.lower().strip()
        if remark and self.data['min_type'] != 17152:  # 关联道路
            self.add_simple_posting(remark, 'AR')
        elif remark:  # 关联公交
            self.add_simple_posting(remark, 'AB', add_full_text=False)

    def make_first_letters(self):
        first_letters = self.data['first_letters'].lower().strip()
        logger.debug('first_letters %s' % first_letters)
        self.doc.add_term('FL'+first_letters)

    def make_all_letters(self):
        all_letters = self.data['all_letters'].lower().strip()
        logger.debug('all_letters %s' % all_letters)
        all_letters_keywords = self.data.get(
            'all_letters_keywords',
            ''
        )
        terms = set()
        if all_letters_keywords:
            all_letters_keywords = all_letters_keywords.lower().strip()
            index = 0
            for term in seg_text(all_letters_keywords):
                self.doc.add_posting('PY' + term, index)
                index += 1
                terms.add(term)
        if all_letters:
            for letters in group_letters(all_letters):
                letters = letters.lower()
                for term in pinyin.tokenize(letters):
                    if term not in terms:
                        self.doc.add_term('PY' + term)
                        terms.add(term)
        logger.debug('terms:%s' % str(terms))

    def make_address(self):
        address = self.data.get('address_keywords', '')
        if not address:
            return
        address = address.lower().strip()
        logger.debug('address %s' % address)
        if not address:
            return
        logger.debug("debug name:%s" % address)
        terms = seg_text(address)
        for term in terms:
            if is_chinese_number(term):
                self.doc.add_term('ADD' + unicode(chinese_to_number(term)))
            if is_number(term):
                self.doc.add_term('ADD' + unicode(term))
            fadmin_name = filter_admin_name(term)
            if fadmin_name:
                self.doc.add_term('AD' + fadmin_name)
            if not term:
                continue
            if term not in address:
                self.doc.add_term('AD' + term)
            else:
                index = address.index(term)
                self.doc.add_posting('AD' + term, index)

        if len(terms) != 1:
            self.doc.add_term('AD' + address)

    def make_tel_num(self):
        tel_num = self.data['tele_num']
        logger.debug('tel_num %s' % tel_num)
        self.add_simple_posting(tel_num, 'TN')

    def make_original_name(self):
        original_type_id = self.data['original_type']
        for original_type_keyword in get_poi_type_keywords(original_type_id):
            logger.debug('original:%s' % original_type_keyword)
            self.doc.add_term('OT' + original_type_keyword.lower())
            if is_chinese_number(original_type_keyword):
                self.doc.add_term('OTD' + unicode(chinese_to_number(original_type_keyword)))
            if is_number(original_type_keyword):
                self.doc.add_term('OTD' + unicode(original_type_keyword))

    def make_brand_name(self):
        poi_id = self.data['id']
        for brand_keyword in get_poi_brand_keywords(poi_id):
            logger.debug('brand_keyword:%s' % brand_keyword)
            self.doc.add_term('BR' + brand_keyword.lower())
            if is_chinese_number(brand_keyword):
                self.doc.add_term('BRD' + unicode(chinese_to_number(brand_keyword)))
            if is_number(brand_keyword):
                self.doc.add_term('BRD' + unicode(brand_keyword))
