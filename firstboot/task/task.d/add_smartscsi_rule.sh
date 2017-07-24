#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

osv=`GET_OS_VERSION`
if [ "$osv" == "smartstore3" ];then
    SMARTSCSI="$ROOT_DIR/common/configure/smartstore3/96-smartscsi.rules"
else
    SMARTSCSI="$ROOT_DIR/common/configure/smartstore2/96-smartscsi.rules"
fi

if [ ! -f $SMARTSCSI ]; then
    ERROR "Cann't find config file: $SMARTSCSI"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -d "/etc/udev/rules.d" ]; then
    ERROR "Udev rules dir not exist"
    exit $REC_DIR_NOT_EXIST
fi

INFO "Install smartscsi timeout rules config"
cp -f $SMARTSCSI "/etc/udev/rules.d"

exit $REC_SUCCESS
