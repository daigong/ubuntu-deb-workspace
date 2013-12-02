#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
from sys import argv,stdout
import string
import datetime

def slave_differ_time():
    '''
    slave and master time differ sec
    '''
    command = '. /etc/profile;psql -U postgres -c "select pg_last_xact_replay_timestamp();"'
    p = subprocess.Popen(command, shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    out_lines = p.stdout.readlines();
    if len(out_lines) >= 3:
        try:
                last_replay_time = out_lines[2]
                #处理字符串
                last_replay_time = last_replay_time.strip()
                index_of_dot = last_replay_time.rfind(".")
                last_replay_time = last_replay_time[:index_of_dot]
                #处理over
                replay_time = datetime.datetime.strptime(last_replay_time,"%Y-%m-%d %H:%M:%S")
                now = datetime.datetime.today()
                result_sec = (now-replay_time).total_seconds()
                stdout.write(str(abs(result_sec)))
        except Exception,e:
                stdout.write('999999')
    else:
        stdout.write('999999');

def main():
    if argv[1] == 'slave_differ_time':
        slave_differ_time()

if __name__ == '__main__':
    main()


#datetime.datetime.strptime(a,"%Y-%m-%d %H:%M:%S")

