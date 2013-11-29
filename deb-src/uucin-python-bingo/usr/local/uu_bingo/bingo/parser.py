#encoding:utf-8
import xapian


#定义范围查询
mt_range = xapian.NumberValueRangeProcessor(0, 'mt:', True)  # 小分类
at_range = xapian.NumberValueRangeProcessor(1, 'ac:', True)  # 行政区划
zc_range = xapian.NumberValueRangeProcessor(2, 'zc:', True)  # 邮政编码
pc_range = xapian.NumberValueRangeProcessor(4, 'pc:', True)  # 省会编码
cc_range = xapian.NumberValueRangeProcessor(5, 'cc:', True)  # 城市编码
he_range = xapian.NumberValueRangeProcessor(6, 'he:', True)  # 热度


def get_poi_query_parser():
    poi_parser = xapian.QueryParser()
    poi_parser.add_prefix('id', 'ID')  # 唯一ID
    poi_parser.add_prefix('pn', 'PN')  # 名称
    poi_parser.add_prefix('fl', 'FL')  # 首字母
    poi_parser.add_prefix('py', 'PY')  # 拼音
    poi_parser.add_prefix('ad', 'AD')  # 地址
    poi_parser.add_prefix('tn', 'TN')  # 电话
    poi_parser.add_prefix('ot', 'OT')  # 原始分类
    poi_parser.add_prefix('br', 'BR')  # 品牌
    poi_parser.add_prefix('ar', 'AR')  # 关联道路
    poi_parser.add_prefix('ab', 'AB')  # 关联公交
    #多数字特殊处理
    poi_parser.add_prefix('pnd', 'PND')  # 名称中包含中文数字
    poi_parser.add_prefix('add', 'ADD')  # 地址中包含中文数字
    poi_parser.add_prefix('otd', 'OTD')  # 原始分类中包含中文数字
    poi_parser.add_prefix('brd', 'BRD')  # 品牌中包含中文数字
    poi_parser.add_prefix('ard', 'ARD')  # 关联道路中包含中文数字
    poi_parser.add_prefix('abd', 'ABD')  # 关联公交中包含中文数字
    #加入到parser
    poi_parser.add_valuerangeprocessor(mt_range)
    poi_parser.add_valuerangeprocessor(at_range)
    poi_parser.add_valuerangeprocessor(zc_range)
    poi_parser.add_valuerangeprocessor(pc_range)
    poi_parser.add_valuerangeprocessor(cc_range)
    poi_parser.add_valuerangeprocessor(he_range)
    return poi_parser
