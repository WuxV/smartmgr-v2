#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

IB0="$ROOT_DIR/common/configure/ifcfg-ib0"
IB1="$ROOT_DIR/common/configure/ifcfg-ib1"
BONDIB0="$ROOT_DIR/common/configure/ifcfg-bondib0"

if [ ! -f $IB0 ]; then
    ERROR "Cann't find config file: $IB0"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $IB1 ]; then
    ERROR "Cann't find config file: $IB1"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $BONDIB0 ]; then
    ERROR "Cann't find config file: $BONDIB0"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi


INFO "Install ib config"
cp -f $IB0 /etc/sysconfig/network-scripts/
cp -f $IB1 /etc/sysconfig/network-scripts/

INFO "Install bondib config"
cp -f $BONDIB0 /etc/sysconfig/network-scripts/

IPADDR=""
INPUT_IP "IB IP"  && IPADDR=`cat $TMP_FILE`
if [ "$IPADDR" != "" ];then
    sed -i 's/IPADDR=192.168.10.1/IPADDR='$IPADDR'/g' /etc/sysconfig/network-scripts/ifcfg-bondib0
fi

OS_TYPE=`GET_OS_VERSION`
if [ $OS_TYPE == "smartstore3" ];then
    systemctl stop NetworkManager >> $CONSOLE_OUT 2>&1
    systemctl disable NetworkManager >> $CONSOLE_OUT 2>&1
fi

# 重启网卡
INFO "Restart network"
/etc/init.d/network restart >> $CONSOLE_OUT 2>&1

if [ $? -ne 0 ];then
    ERROR "Restart network failed"
	exit $REC_ERR_NETWORK_RESTART
fi

sleep 3
# 重启后必须重启smartmgr, 用于生效smartmgr的网络配置
smartmgr restart >> $CONSOLE_OUT 2>&1

rm -f $TMP_FILE_NETWORK

exit $REC_SUCCESS
