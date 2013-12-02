#!/usr/bin/python
# -*- coding: utf-8 -*-
#check pgpool by pcp command
import subprocess
from sys import argv,stdout
import string

def nodestatus():
    node_count_command = '. /etc/profile;pcp_node_count 10 localhost 9898 postgres postgres'
    node_count_p = subprocess.Popen(node_count_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    node_count_p.wait()
    node_count_lines = node_count_p.stdout.readlines();
    node_count = int(node_count_lines[0])
    for node_index in range(node_count):
        node_info_command = ". /etc/profile;pcp_node_info 10 localhost 9898 postgres postgres %d" % node_index
        node_info_p = subprocess.Popen(node_info_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        node_info_p.wait()
        node_info_lines = node_info_p.stdout.readlines();
        result_array =  node_info_lines[0][:-1] # like it "124.95.161.226 5432 2 0.375000"
        if result_array.split(" ")[2] not in ['1','2']:
		return "1"
    return "0"


def main():
    if argv[1] == 'nodestatus':
	try:
             print nodestatus()
        except Exception,e:
             print 9 #unknow error

if __name__ == '__main__':
    main()


#nodestatus
