#encoding:utf-8
import sys
import getopt
import requests
from location.geo import GeoTools

geo_helper = GeoTools()


def parse_mapper_value(data):
    try:
        params = data.split('\t')
        created_time, loc_type, lng, lat, accuracy = (
            int(params[6]),  # created_time
            params[7],  # loc_type
            float(params[8]),  # lng
            float(params[9]),  # lat
            int(params[10]),  # accuracy
        )
        if loc_type in ['uu', 'cell']:
            return None
        macs = params[14].strip().split(';')
        return macs, created_time, loc_type, lng, lat, accuracy
    except (ValueError, IndexError):
        return None


def benchmark_test_wifi(input_file, output_file):
    session = requests.Session()
    with open(input_file) as f1:
        with open(output_file, 'w') as f2:
            for line in f1:
                params = parse_mapper_value(line.strip('\n').strip())
                if not params:
                    continue
                lng1, lat1 = params[3:5]
                url = "http://127.0.0.1:7001/location/wifi?q=%s" % '|'.join(
                    [mac + ',90' for mac in params[0]])
                response = session.get(url)
                if response.status_code == 200:
                    json = response.json()
                    distance = geo_helper.distance(
                        lat1, lng1, json['lat'], json['lon'])
                    f2.write('%s\t%d\t%s\n' % (params[2], distance, url))
                else:
                    f2.write('%s\t%d\t%s\n' % (params[2], -1, url))


def benchmark_test_cell(input_file, output_file):
    pass


def print_help():
    print('-t  --type             数据的类型：ip, wifi, cell')
    print('-i  --input            输入文件的路径')
    print('-o  --output           输出文件的路径 ')
    print("-h  --help             查看帮助选项")


benchmark_method_map = {
    'wifi': benchmark_test_wifi,
    'cell': benchmark_test_cell,
}

if __name__ == '__main__':
    gen_type, _input_file, _output_file = None, None, None
    options, _ = getopt.getopt(
        sys.argv[1:],
        "t:i:o:h",
        ['type', 'input', 'output', 'help']
    )
    for key, value in options:
        if key in ('-t', '--type'):
            gen_type = value
        if key in ('-i', '--input'):
            _input_file = value
        if key in ('-o', '--output'):
            _output_file = value
    if gen_type and _input_file and _output_file:
        benchmark_method_map[gen_type](_input_file, _output_file)
    else:
        print_help()
