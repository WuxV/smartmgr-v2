#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

SYSCTL_CONF="$ROOT_DIR/common/configure/sysctl.conf"

if [ ! -f $SYSCTL_CONF ]; then
    ERROR "Cann't find config file: $OPENIB_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

INFO "Install sysctl config"
cp -f $SYSCTL_CONF "/etc/"

exit 0
