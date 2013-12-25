#!/bin/bash
case $1 in
    'ip_count')
        sudo netstat -antlp|grep python|grep ESTABLISHED|grep 1001|awk '{print $5}'|awk -F: '{print $1}'|sort -u|wc -l
        ;;

    'socket_count')
        sudo netstat -antlp|grep python|grep ESTABLISHED|grep 1001|awk '{print $5}'|awk -F: '{print $1}'|wc -l
        ;;
esac
