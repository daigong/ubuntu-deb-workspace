#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import stdout
from sys import argv
import subprocess

# stdout.write("1")
# stdout.write("2")

#WEB_URL_LIST_TXT = '/home/daigong/web_site_checker_url_list.conf'
WEB_URL_LIST_TXT = '/etc/zabbix/other_plugin_conf/web_site_checker_url_list.conf'


def get_config_from_file():
    config = {}
    file = open(WEB_URL_LIST_TXT)
    try:
        lines = file.readlines()
        for i in range(0, len(lines)):
            line = lines[i]
            if line.startswith('#'):
                continue
            else:

                # file_demo: key=http://baidu.com/value?asd=123&asdasd=4321

                first_eq_index = line.find('=')
                key = line[:first_eq_index].strip()
                value = line[first_eq_index + 1:-1].strip()
                config[key] = value
    finally:
        file.close()

    return config


def web_site_discovery():
    stdout.write('{"data":[')
    config = get_config_from_file()
    keys_list = config.keys()
    for i in range(0, len(keys_list)):
        if i != len(keys_list) - 1:
            stdout.write('{')
            stdout.write('"{#SITENAME}":"%s"},' % keys_list[i])
        else:
            stdout.write('{')
            stdout.write('"{#SITENAME}":"%s"}]}' % keys_list[i])


def web_site_code(key):
    config = get_config_from_file()
    url = config[key]
    curl_command = \
        '/usr/bin/curl -o /dev/null -s -w %%{http_code}  --connect-timeout 2 "%s"' % url
    p = subprocess.Popen(curl_command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 等待command结束

    p.wait()
    code = p.stdout.readline()
    if code == "000":
        code = "404"
    stdout.write(code)


#    exit(int(p.returncode))

def main():
    if __name__ == '__main__':
        if len(argv) < 2:
            print 'plz input method web_site_discovery or web_site_code'
            exit(-1)
        if argv[1] == 'web_site_discovery':
            web_site_discovery()
        elif argv[1] == 'web_site_code':
            if len(argv) <= 2:
                print 'web_site_code need 2 params like: web_site_code www.baidu.com'
                exit(-1)
            else:
                web_site_code(argv[2])


if __name__ == '__main__':
    main()
