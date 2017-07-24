#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

BONDING_CONF="$ROOT_DIR/common/configure/bonding.conf"

if [ ! -f $BONDING_CONF ]; then
    ERROR "Cann't find config file: $BONDING_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

INFO "Update booding config"
cp -f $BONDING_CONF "/etc/modprobe.d"

exit $REC_SUCCESS
