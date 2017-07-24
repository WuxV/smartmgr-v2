#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

/sbin/modprobe ib_srp
sleep 20

ADD_TARGET_1="/sys/class/infiniband_srp/srp-mlx4_0-1/add_target"
ADD_TARGET_2="/sys/class/infiniband_srp/srp-mlx4_0-2/add_target"

if [ ! -f $ADD_TARGET_1 ]; then
    ERROR "Cann't find infiniband add target: $ADD_TARGET_1"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $ADD_TARGET_2 ]; then
    ERROR "Cann't find infiniband add target: $ADD_TARGET_2"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

/usr/sbin/ibsrpdm -c 2>> $CONSOLE_OUT  | while read target_info; do
    INFO "Add target: `echo $target_info` to $ADD_TARGET_1"
    echo "${target_info}" > $ADD_TARGET_1 2>> $CONSOLE_OUT
    if [ $? -ne 0 ];then
        WARNING "Add target error"
    fi

    INFO "Add target: `echo $target_info` to $ADD_TARGET_2"
    echo "${target_info}" > $ADD_TARGET_2 2>> $CONSOLE_OUT
    if [ $? -ne 0 ];then
        WARNING "Add target error"
    fi
done

exit $REC_SUCCESS
