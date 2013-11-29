#encoding:utf-8
import xapian
import logging
import json
import contextlib
import psycopg2.extras
from xapian import QueryParser
from pyramid.view import view_config
from bingo.database import get_xapian_conn, get_postgres_conn
from bingo.cjk import seg_text as seg_text
from bingo.cjk import is_chinese_number, chinese_to_number, is_number
from bingo.parser import get_poi_query_parser
from bingo.pinyin import tokenize, chinese_to_pinyin
from bingo.builder.document import DocumentBuilder
from .sorter import set_enquire_sorter

base_flags = QueryParser.FLAG_DEFAULT | QueryParser.FLAG_AUTO_SYNONYMS
#|QueryParser.FLAG_WILDCARD|QueryParser.FLAG_PARTIAL

logger = logging.getLogger()
QUERY_POI_SQL_TEMPLATE = "SELECT * FROM geo.search_poi WHERE id = %s"


def set_terms_scale_weight(term_weight_dict, operator=xapian.Query.OP_OR):
    term_list = []
    for query, weight in term_weight_dict.items():
        term = xapian.Query(xapian.Query.OP_SCALE_WEIGHT, query, weight)
        term_list.append(term)
    if len(term_list) == 1:
        return term_list[0]
    return xapian.Query(operator, term_list)


def make_term_keyword_query(term, poi_query_parser, flags):
    address_query = poi_query_parser.parse_query('ad:%s' % term, flags)
    original_query = poi_query_parser.parse_query('ot:%s' % term, flags)
    brand_query = poi_query_parser.parse_query('br:%s' % term)
    associated_road_query = poi_query_parser.parse_query(
        'ar:%s' % term, flags)
    associated_bus_query = poi_query_parser.parse_query(
        'ab:%s' % term, flags)
    term_weight_dict = {
        address_query: 5,
        original_query: 3,
        brand_query: 3,
        associated_road_query: 1,
        associated_bus_query: 1
    }
    if is_chinese_number(term) or is_number(term):
        dig = chinese_to_number(term) if not is_number(term) else term
        address_query_digital = poi_query_parser.parse_query(
            'add:%s' % dig, flags)
        term_weight_dict[address_query_digital] = 1
        original_query_digital = poi_query_parser.parse_query(
            'otd:%s' % dig, flags)
        term_weight_dict[original_query_digital] = 1
        brand_query_digital = poi_query_parser.parse_query(
            'brd:%s' % dig)
        term_weight_dict[brand_query_digital] = 1
        associated_road_query_digital = poi_query_parser.parse_query(
            'ard:%s' % dig, flags)
        term_weight_dict[associated_road_query_digital] = 1
        associated_bus_query_digital = poi_query_parser.parse_query(
            'abd:%s' % dig, flags)
        term_weight_dict[associated_bus_query_digital] = 1
    return set_terms_scale_weight(term_weight_dict)


def make_term_base_query(term, poi_query_parser, flags):
    #正常名称匹配权值10
    term_weight_dict = {poi_query_parser.parse_query(
        "pn:%s" % term, flags): 10}
    #行政区划权值+7
    term_weight_dict[
        poi_query_parser.parse_query("pn:%s AND mt:49027..49032")
    ] = 7
    pinyins = tokenize(term)
    if pinyins:
        pinyin_query_term = poi_query_parser.parse_query(
            ' AND '.join(['py:%s' % pinyin for pinyin in pinyins]),
            flags
        )
        term_weight_dict[pinyin_query_term] = 1  # 拼音匹配权值1
    if is_chinese_number(term) or is_number(term):
        dig = chinese_to_number(term) if not is_number(term) else term
        number_query = poi_query_parser.parse_query(
            'pnd:%s' % dig, flags)
        term_weight_dict[number_query] = 9  # 中文数字匹配权值9
    query = set_terms_scale_weight(term_weight_dict)
    return query


def make_term_query(request, poi_query_parser, flags=base_flags):
    """
    构建基本的查询
    """
    q = request.GET.get('q', '').strip().lower()  # 查询参数
    search_type = request.GET.get('qt', 'name')  # 查询类型
    if not q:
        return
    query_terms = []
    terms = seg_text(q, join_char=' ')
    for term in terms:
        term_query = make_term_base_query(term, poi_query_parser, flags)
        if search_type in ['keywords', ]:
            keywords_query = make_term_keyword_query(
                term, poi_query_parser, flags)
            term_query = set_terms_scale_weight({
                term_query: 10,
                keywords_query: 3,
            })
        query_terms.append(term_query)
    query = xapian.Query(xapian.Query.OP_AND, query_terms)
    full_query_term = set_terms_scale_weight({
        poi_query_parser.parse_query('pn:%s' % q, flags): 100
    })  # 完全匹配权值100
    query = xapian.Query(
        xapian.Query.OP_ELITE_SET, query, full_query_term)
    near_query_term = set_terms_scale_weight({
        poi_query_parser.parse_query(
            ' NEAR '.join(['pn:%s' % term for term in terms if term]), flags
        ): 90
    })  # 顺序匹配权值90
    return xapian.Query(
        xapian.Query.OP_ELITE_SET,
        query,
        near_query_term,
    )


def make_term_suggest_query(request, poi_query_parser, flags=base_flags):
    q = request.GET.get('q', '').strip().lower()  # 查询参数
    if not q:
        return
    terms = seg_text(q, join_char=' ')
    #正常名称匹配权值10
    query_list = []
    for term in terms:
        query = poi_query_parser.parse_query("pn:%s" % term)
        pinyins = tokenize(term)
        if pinyins:
            pinyin_query_term = poi_query_parser.parse_query(
                ' AND '.join(['py:%s' % pinyin for pinyin in pinyins]),
                flags
            )
            query = xapian.Query(
                xapian.Query.OP_ELITE_SET, query, pinyin_query_term)
        elif is_chinese_number(term) or is_number(term):
            dig = chinese_to_number(term) if not is_number(term) else term
            number_query = poi_query_parser.parse_query(
                'pnd:%s' % dig, flags)
            query = xapian.Query(
                xapian.Query.OP_ELITE_SET, query, number_query)
        query_list.append(query)
    return xapian.Query(xapian.Query.OP_AND, query_list)


def filter_range(request, poi_query_parser, query):
    """
    筛选结构集
    """
    if not query:
        return
    min_types = request.GET.get('mintype')
    if min_types:
        min_types = min_types.split(',')
        qlang = ' OR '.join(["mt:%s" % min_type for min_type in min_types])
        q1 = poi_query_parser.parse_query(qlang)
        query = xapian.Query(xapian.Query.OP_AND, query, q1)

    lat, lon, radius = request.GET.get('range', ',,').split(',')
    if lat and lon and radius:
        coords = xapian.LatLongCoords()
        coords.append(xapian.LatLongCoord(float(lat), float(lon)))
        metric = xapian.GreatCircleMetric()
        ps = xapian.LatLongDistancePostingSource(
            3,
            coords,
            metric,
            float(radius)
        )
        q1 = xapian.Query(ps)
        query = xapian.Query(xapian.Query.OP_AND, query, q1)

    cities = request.GET.get('cities')
    if cities:
        cities = cities.split(',')
        qlang = ' OR '.join(["ac:%s" % city for city in cities if city])
        q1 = poi_query_parser.parse_query(qlang)
        query = xapian.Query(xapian.Query.OP_AND, query, q1)
    return query


def make_search_matches(request, poi_query_parser, xapian_database):
    search_type = request.GET.get('qt', 'name')
    if search_type in ['name', 'keywords', 'suggest']:
        return make_term_search_matches(
            request, poi_query_parser, xapian_database)
    elif search_type == 'id':
        _id = request.GET.get('q')
        return make_id_search_matches(_id, poi_query_parser, xapian_database)
    else:
        raise ValueError('not support this search_type:%s' % search_type)


def make_id_search_matches(_id, poi_query_parser, xapian_database):
    query = poi_query_parser.parse_query(u"id:%s" % _id)
    enquire = xapian.Enquire(xapian_database)
    enquire.set_query(query)
    return enquire.get_mset(0, 1)


def make_term_search_matches(request, poi_query_parser, xapian_database):
    poi_query_parser.set_database(xapian_database)  # 设置采用flags的数据库
    search_type = request.GET.get('qt', 'name')  # 查询类型
    if search_type == 'suggest':
        flags = QueryParser.FLAG_PARTIAL
        query = make_term_suggest_query(request, poi_query_parser, flags)
    else:
        flags = base_flags
        query = make_term_query(request, poi_query_parser, flags)
    query = filter_range(
        request, poi_query_parser, query)  # 构建query
    if not query:  # 传参错误
        return
    limit = int(request.GET.get('limit', '30'))
    offset = int(request.GET.get('offset', 0))
    enquire = xapian.Enquire(xapian_database)
    enquire.set_query(query)
    st = int(request.GET.get('st', 0))  # 排序类型
    enquire = set_enquire_sorter(request, enquire, st)
    return enquire.get_mset(offset, limit, 1000)


def make_spelling_suggestion(request, poi_query_parser, xapian_database):
    q = request.GET.get('q', '').strip().lower()  # 查询参数
    if not q:
        return []
    pinyins = chinese_to_pinyin(q)
    qlang = ' AND '.join(['py:%s' % pinyin for pinyin in pinyins])
    query = poi_query_parser.parse_query(qlang, base_flags)  # 模糊语义匹配
    query = filter_range(request, poi_query_parser, query)
    near_query_term = filter_range(
        request,
        poi_query_parser,
        poi_query_parser.parse_query(
            ' ADJ '.join(['py:%s' % pinyin for pinyin in pinyins]),
            base_flags
        )
    )
    query = set_terms_scale_weight({
        query: 10,
        near_query_term: 90,
    })
    if not query:  # 传参错误
        return ''
    enquire = xapian.Enquire(xapian_database)
    enquire.set_query(query)
    suggest = []
    for matche in enquire.get_mset(0, 5, 100):
        poi_name = json.loads(matche.document.get_data())['poi_name']
        if poi_name not in suggest:
            suggest.append(poi_name)
    return suggest


def make_group_matches(request, poi_query_parser, spy, xapian_database):
    query = filter_range(
        request,
        poi_query_parser,
        make_term_query(request, poi_query_parser, base_flags))
    enquire = xapian.Enquire(xapian_database)
    enquire.add_matchspy(spy)
    enquire.set_query(query)
    enquire.set_weighting_scheme(xapian.BoolWeight())
    return enquire.get_mset(0, 10, 100000)


@view_config(route_name='search_poi', renderer='string')
def search_poi(request):
    response = {}
    try:
        response['status'] = 'OK'
        with contextlib.closing(get_xapian_conn()) as xapian_database:
            poi_query_parser = get_poi_query_parser()
            poi_query_parser.set_database(xapian_database)
            matches = make_search_matches(
                request, poi_query_parser, xapian_database)
            if matches:
                response['results'] = [
                    json.loads(
                        matche.document.get_data()
                    ) for matche in matches
                ]
                response['size'] = matches.get_matches_estimated()
            else:
                response['size'] = 0
                response['suggest'] = make_spelling_suggestion(
                    request,
                    poi_query_parser,
                    xapian_database
                )
    except BaseException as e:
        logger.exception(e)
        response['size'] = 0
        response['status'] = 'ERROR_PARAMETERS'
    return json.dumps(response, ensure_ascii=False, encoding='utf-8')


@view_config(route_name='group_poi', renderer='string')
def group_poi(request):
    response = {}
    try:
        response['status'] = 'OK'
        group_type = request.GET.get('gt', 'city_code')
        if group_type == 'admin_code':
            admin_code_spy = xapian.ValueCountMatchSpy(1)
        elif group_type == 'prov_code':
            admin_code_spy = xapian.ValueCountMatchSpy(4)
        else:
            admin_code_spy = xapian.ValueCountMatchSpy(5)
        with contextlib.closing(get_xapian_conn()) as xapian_database:
            poi_query_parser = get_poi_query_parser()
            poi_query_parser.set_database(xapian_database)
            make_group_matches(
                request, poi_query_parser, admin_code_spy, xapian_database)
            group_result = {}
            for value in admin_code_spy.values():
                code = int(xapian.sortable_unserialise(value.term))
                group_result[code] = value.termfreq
            response['results'] = group_result
    except BaseException as e:
        logger.exception(e)
        response['results'] = []
        response['size'] = 0
        response['status'] = 'ERROR_PARAMETERS'
    return json.dumps(response, ensure_ascii=False, encoding='utf-8')


@view_config(route_name='write_poi', renderer='string')
def write_poi(request):
    response = {}
    try:
        _id = request.params.get('id', '')
        with contextlib.closing(get_postgres_conn()) as conn:
            with contextlib.closing(get_xapian_conn(False)) as xapian_database:
                with contextlib.closing(
                    conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                ) as cursor:
                    cursor.execute(QUERY_POI_SQL_TEMPLATE % _id)
                    data = cursor.fetchone()
                    poi_query_parser = get_poi_query_parser()
                    poi_query_parser.set_database(xapian_database)
                    mset = make_id_search_matches(
                        _id, poi_query_parser, xapian_database)
                    if data and not mset.empty():  # 修改数据
                        doc = mset.get_document(0)
                        builder = DocumentBuilder(data)
                        xapian_database.replace_document(
                            doc.get_docid(),
                            builder.build()
                        )
                    elif data and mset.empty():  # 增加数据
                        builder = DocumentBuilder(data)
                        xapian_database.add_document(builder.build())
                    elif not data and not mset.empty():  # 删除数据
                        doc = mset.get_document(0)
                        xapian_database.delete_document(
                            doc.get_docid()
                        )
        response['status'] = 'OK'
    except BaseException as e:
        logger.exception(e)
        response['status'] = 'ERROR_PARAMETERS'
    return json.dumps(response, ensure_ascii=False, encoding='utf-8')
