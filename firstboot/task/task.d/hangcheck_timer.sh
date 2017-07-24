#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

HANGCHECK_MODULES="$ROOT_DIR/common/configure/hangcheck-timer.modules"
HANGCHECK_CONF="$ROOT_DIR/common/configure/hangcheck-timer.conf"

if [ ! -f $HANGCHECK_CONF ]; then
    ERROR "Cann't find config file: $HANGCHECK_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $HANGCHECK_MODULES ]; then
    ERROR "Cann't find config file: $HANGCHECK_MODULES"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

INFO "Install hangcheck timer config"
cp -f $HANGCHECK_CONF "/etc/modprobe.d"

INFO "Install hangcheck timer modules"
cp -f $HANGCHECK_MODULES "/etc/sysconfig/modules"

exit $REC_SUCCESS
