#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

NTP_CONF="/etc/ntp.conf"

while true; do
    ACTION=`MAKE_SURE_CONFIG "NTP service"`
    [ "$ACTION" != "" ] && break
    echo "Please input Y/N."
done

if [ "$ACTION" == "Y" ];then
    if [ ! -e $NTP_CONF ]; then
        WARNING "Missing ntp config : $NTP_CONF"
        exit $REC_SUCCESS
    fi
    
    INFO "Update NTP config"
    
    IPADDR=""
    INPUT_IP "ntp ip"  && IPADDR=`cat $TMP_FILE`
    if [ "$IPADDR" != "" ];then
        sed -i 's/server 0.centos.pool.ntp.org/server '$IPADDR'/g' $NTP_CONF >> $CONSOLE_OUT 2>&1
    
        OS_TYPE=`GET_OS_VERSION`
        if [ "$OS_TYPE" == "smartstore3" ];then
            systemctl start  ntpd.service >> $CONSOLE_OUT 2>&1
            systemctl enable ntpd.service >> $CONSOLE_OUT 2>&1
        else
            service ntpd start >> $CONSOLE_OUT 2>&1
            chkconfig ntpd on >> $CONSOLE_OUT 2>&1
        fi
    fi
else
    OS_TYPE=`GET_OS_VERSION`
    if [ "$OS_TYPE" == "smartstore3" ];then
        systemctl stop  ntpd.service >> $CONSOLE_OUT 2>&1
        systemctl disable ntpd.service >> $CONSOLE_OUT 2>&1
    else
        service ntpd stop >> $CONSOLE_OUT 2>&1
        chkconfig ntpd off >> $CONSOLE_OUT 2>&1
    fi
fi

exit $REC_SUCCESS
