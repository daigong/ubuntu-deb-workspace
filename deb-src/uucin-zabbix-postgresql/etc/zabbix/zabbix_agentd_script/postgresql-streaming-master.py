#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
from sys import argv,stdout
def slave_count():
    command = ". /etc/profile;psql -U postgres -c 'select count(*) from pg_stat_replication;'"
    p = subprocess.Popen(command, shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    out_lines = p.stdout.readlines();
    if len(out_lines) >= 3:
        stdout.write(out_lines[2].strip())
    else:
        stdout.write('999999');


def main():
    if argv[1] == 'slave_count':
        slave_count()

if __name__ == '__main__':
    main()
