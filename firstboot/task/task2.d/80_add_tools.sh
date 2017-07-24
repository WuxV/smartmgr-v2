#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

BIN_DIR="/bin/sbin"
BIN_FILE_LSSRP="$ROOT_DIR/common/configure/lssrp"

DEBUG "EXE $0"

if [ ! -d $BIN_DIR ]; then
    ERROR "$BIN_DIR dir not exist"
    exit $REC_DIR_NOT_EXIST
fi

if [ -f $BIN_FILE_LSSRP ];then
    INFO "Install lsrp"
    cp -f $BIN_FILE_LSSRP  $BIN_DIR
if 

