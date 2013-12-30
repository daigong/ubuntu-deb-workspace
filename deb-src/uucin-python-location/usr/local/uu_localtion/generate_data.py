#encoding:utf-8
import sys
import getopt
import leveldb


def generate_ip_data(input_file, output_file):
    pass


def generate_wifi_data(input_file, output_file):
    db = leveldb.LevelDB(
        output_file,
        write_buffer_size=100000000,
        max_open_files=100000
    )
    with open(input_file) as f:
        batch = leveldb.WriteBatch()
        counter = 0
        for line in f:
            mac, body = line.strip('\n').split('\t')
            batch.Put(mac.strip("'"), body.strip("()[]").replace(' ', ''))
            counter += 1
            if counter % 10000 == 0:
                print("count: %s" % counter)
                db.Write(batch, sync=False)
                batch = leveldb.WriteBatch()
        db.Write(batch, sync=True)
    del db


def generate_cell_data(input_file, output_file):
    db = leveldb.LevelDB(
        output_file,
        write_buffer_size=100000000,
        max_open_files=100000
    )
    with open(input_file) as f:
        batch = leveldb.WriteBatch()
        counter = 0
        for line in f:
            cell, body = line.strip('\n').split('\t')
            batch.Put(cell.strip("'"), body.strip("()[]").replace(' ', ''))
            counter += 1
            if counter % 10000 == 0:
                print("count: %s" % counter)
                db.Write(batch, sync=False)
                batch = leveldb.WriteBatch()
        db.Write(batch, sync=True)
    del db


generate_method_map = {
    'ip': generate_ip_data,
    'wifi': generate_wifi_data,
    'cell': generate_cell_data,
}


def print_help():
    print('-t  --type             数据的类型：ip, wifi, cell')
    print('-i  --input            输入文件的路径')
    print('-o  --output           输出文件的路径 ')
    print("-h  --help             查看帮助选项")

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
        generate_method_map[gen_type](_input_file, _output_file)
    else:
        print_help()
