#! /etc/zabbix/zabbix_plugin.conf.d/ESzabbix/ESzabbix_env/bin/python

# Created by Aaron Mildenstein on 19 SEP 2012

from pyes import *
import sys

# Define the fail message
def zbx_fail():
    print "ZBX_NOTSUPPORTED"
    sys.exit(2)
    
returnval = None


if len(sys.argv) < 3:
    zbx_fail()

# Try to establish a connection to elasticsearch
try:
    conn = ES('localhost:9200',timeout=25,default_indices=[''])
except Exception, e:
    zbx_fail()

if sys.argv[1] == 'service':
    if sys.argv[2] == 'status':
        try:
            conn.status()
            returnval = 1
        except Exception, e:
            returnval = 0


if sys.argv[1] == 'service':
    if sys.argv[2] == 'number_of_nodes':
        try:
            nodestats = conn.cluster_health()
            returnval = nodestats[u'number_of_nodes']
        except Exception, e:
            returnval = 0

# If we somehow did not get a value here, that's a problem.  Send back the standard 
# ZBX_NOTSUPPORTED
if returnval is None:
    zbx_fail()
else:
    print returnval

# End

