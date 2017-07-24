#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

# 获取当前机器类型
SYS_MODE=`GET_PLATFORM_SYS_MODE | tr '[a-z]' '[A-Z]'`
if [ "$SYS_MODE" == "" ];then
    echo "Cann't get platform's sys mode."
    exit $REC_FAIL
fi

if [ $SYS_MODE != "STORAGE" ];then
    SRP_DAEMON_CONF="$ROOT_DIR/common/configure/srp_daemon.conf"
    if [ ! -f $SRP_DAEMON_CONF ]; then
        ERROR "Cann't find config file: $SRP_DAEMON_CONF"
        exit $REC_CONFIG_FILE_NOT_EXIST
    fi
    
    INFO "Update srp daemon config"
    cp -f $SRP_DAEMON_CONF "/etc/"
    
    OPENIB_CONF="/etc/infiniband/openib.conf"
    if [ ! -f $OPENIB_CONF ]; then
        ERROR "Cann't find config file: $OPENIB_CONF"
        exit $REC_CONFIG_FILE_NOT_EXIST
    fi
    
    INFO "Update openib config"
    sed -i 's/SRP_LOAD=no/SRP_LOAD=yes/g' $OPENIB_CONF
    sed -i 's/RDS_LOAD=no/RDS_LOAD=yes/g' $OPENIB_CONF
    sed -i 's/SRPHA_ENABLE=no/SRPHA_ENABLE=yes/g' $OPENIB_CONF
    sed -i 's/SRP_DAEMON_ENABLE=no/SRP_DAEMON_ENABLE=yes/g' $OPENIB_CONF
fi

if [ -f "/etc/init.d/smartscsi" ];then
    INFO "Stop smartscsi"
	/etc/init.d/smartscsi stop >> $CONSOLE_OUT 2>&1
	if [ $? -ne 0 ]; then
	    ERROR "Stop smartscsi error"
	fi
fi

if [ $SYS_MODE != "STORAGE" ];then
	if [ -f "/etc/init.d/srpd" ];then
        INFO "Stop srpd"
        /etc/init.d/srpd stop >> $CONSOLE_OUT 2>&1
	fi
fi

if [ -f "/etc/init.d/openibd" ];then
    INFO "Restart openibd"
    /etc/init.d/openibd restart >> $CONSOLE_OUT 2>&1
    if [ $? -ne 0 ]; then
        ERROR "Restart openibd error"
        exit $REC_SERVICE
    fi
fi

if [ $SYS_MODE != "STORAGE" ];then
	if [ -f "/etc/init.d/srpd" ];then
        INFO "start srpd"
        /etc/init.d/srpd start >> $CONSOLE_OUT 2>&1
	fi
fi

if [ -f "/etc/init.d/smartscsi" ];then
    INFO "Start smartscsi"
    /etc/init.d/smartscsi start >> $CONSOLE_OUT 2>&1
    if [ $? -ne 0 ]; then
        ERROR "Start smartscsi error"
        exit $REC_SERVICE
    fi
fi

sleep 20

exit $REC_SUCCESS
