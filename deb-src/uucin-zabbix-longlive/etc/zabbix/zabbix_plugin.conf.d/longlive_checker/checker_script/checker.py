#!/etc/zabbix/zabbix_plugin.conf.d/longlive_checker/longlive_checker_env/bin/python
# -*- coding: utf-8 -*

import sys
if 'threading' in sys.modules:
        raise Exception('threading module loaded before patching!')

import gevent.monkey

gevent.monkey.patch_thread()

from strom.client import open as strom_open
import os
from sys import stdout
from sys import argv


URL = "rrp://127.0.0.1:1001"


WEB_URL_LIST_DIR = '/etc/zabbix/zabbix_plugin.conf.d/longlive_checker/config/'


def get_config_from_file():
    config = {}
    config_files = os.listdir(WEB_URL_LIST_DIR)
    for config_file in config_files:
            file = open("%s/%s" % ( WEB_URL_LIST_DIR, config_file ))
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

def discovery():
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


def check(check_url):
	config=get_config_from_file()
	result = "404"
	try:
		with strom_open(URL) as s:
			msg = s.get(config[check_url])
			if msg[8:11] == "200":
				result = "200"
	except Exception as e:
		pass
	stdout.write(result)


def main():
    if __name__ == '__main__':
        if len(argv) < 2:
            print 'plz input method discovery or check'
            exit(-1)
        if argv[1] == 'discovery':
            discovery()
        elif argv[1] == 'check':
            if len(argv) <= 2:
                print 'need 2 params like: web_site_code www.baidu.com'
                exit(-1)
            else:
                check(argv[2])


if __name__ == '__main__':
    main()

