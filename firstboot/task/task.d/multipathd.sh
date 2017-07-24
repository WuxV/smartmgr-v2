#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

MULTIPATH_CONF="$ROOT_DIR/common/configure/multipath.conf"

if [ ! -f $MULTIPATH_CONF ]; then
    ERROR "Cann't find config file: $OPENIB_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

INFO "Install multipath config"
cp -f $MULTIPATH_CONF "/etc/"

INFO "Start multipath"

OS_TYPE=`GET_OS_VERSION`

if [ $OS_TYPE == "smartstore3" ];then
    systemctl start  multipathd.service 2>&1
    systemctl enable multipathd.service 2>&1
else
    service multipathd start >> $CONSOLE_OUT 2>&1
    chkconfig multipathd on >> $CONSOLE_OUT 2>&1
fi

sleep 30

exit $REC_SUCCESS
