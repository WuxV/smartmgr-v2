#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

osv=`GET_OS_VERSION`
if [ "$osv" == "smartstore3" ];then
    ASM_DEVICE_RULES="$ROOT_DIR/common/configure/smartstore3/99-oracle-asmdevices.rules"
    SMARTSCSI_MAP_SCRIPT="$ROOT_DIR/common/configure/smartstore3/smartscsi-disk-map.sh"
else
    ASM_DEVICE_RULES="$ROOT_DIR/common/configure/smartstore2/99-oracle-asmdevices.rules"
    SMARTSCSI_MAP_SCRIPT="$ROOT_DIR/common/configure/smartstore2/smartscsi-disk-map.sh"
fi

if [ ! -f $ASM_DEVICE_RULES ]; then
    ERROR "Cann't find config file: $ASM_DEVICE_RULES"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $SMARTSCSI_MAP_SCRIPT ]; then
    ERROR "Cann't find config file: $SMARTSCSI_MAP_SCRIPT"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -d "/etc/udev/rules.d" ]; then
    ERROR "Udev rules dir not exist"
    exit $REC_DIR_NOT_EXIST
fi

if [ ! -d "/etc/asm_dev_map" ]; then
    mkdir -p "/etc/asm_dev_map"
fi

INFO "Install oracle rules config"
cp -f $ASM_DEVICE_RULES "/etc/udev/rules.d"

INFO "Install smartscsi disk map"
cp -f $SMARTSCSI_MAP_SCRIPT "/etc/asm_dev_map"

INFO "Start udev"
OS_TYPE=`GET_OS_VERSION`
if [ $OS_TYPE == "smartstore3" ];then
    systemctl restart systemd-udev-trigger.service 2>&1
else
    /sbin/start_udev >> $CONSOLE_OUT 2>&1
fi

exit $REC_SUCCESS
