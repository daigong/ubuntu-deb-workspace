#!/bin/bash

#制作deb

echo '通过src制作deb包'

DEB_SRC_PATH=/home/ubuntu-deb-workspace/deb-src
MIRROR_PATH=/home/ubuntu-mirror/mirror/cn.uucin.ubuntu.com/ubuntu

deb_names=`ls $DEB_SRC_PATH`

cd $DEB_SRC_PATH

if [ -z "$1" ]
then
        #制作全部包
        for deb_name in $deb_names
        do
                if [ -d "$DEB_SRC_PATH/$deb_name/DEBIAN" ]
                then
                        echo "制作$deb_name deb包"
                        dpkg -b $deb_name
                        \cp "$deb_name.deb" $MIRROR_PATH/pool/main/uucin -rfv
                fi
        done
else
        #只制作一个包
        if [ -d "$DEB_SRC_PATH/$1/DEBIAN" ]
        then
                echo "制作 $1 deb 包"
                dpkg -b $1
                \cp "$1.deb" $MIRROR_PATH/pool/main/uucin -rfv
        else
                echo "$1 不是合法的deb包结构"
        fi
fi

#制作签名

cd $MIRROR_PATH

echo '制作Packages'

apt-ftparchive packages pool/main/ > dists/precise/main/binary-amd64/Packages
apt-ftparchive packages pool/main/ > dists/precise/main/binary-i386/Packages

echo '制作release'
apt-ftparchive -c dists/precise/pt.conf release dists/precise/ > dists/precise/Release

echo '制作Contents-amd64.gz'
apt-ftparchive contents pool/ | gzip -9c > dists/precise/Contents-amd64.gz

echo '制作签名，需要密码(daigong)'
rm dists/precise/Release.gpg -f

gpg -a --detach-sign -o dists/precise/Release.gpg dists/precise/Release
