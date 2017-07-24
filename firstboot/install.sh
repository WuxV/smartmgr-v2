#!/bin/bash
trap "exit 1" 2
stty sane

# 基本目录
ROOT_DIR=$(cd `dirname $0` && pwd)
DIR_COMMON=$ROOT_DIR/common
DIR_CONF=$ROOT_DIR/conf
DIR_TASK=$ROOT_DIR/task

source $DIR_COMMON/base_function.sh
source $DIR_COMMON/log_function.sh
source $DIR_COMMON/ret_code.sh

CONFIG_USER=$DIR_CONF/config_user
CONFIG_SYS=$DIR_CONF/config_sys

# 配置文件检查
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

[ ! -d $LOG_DIR ] && mkdir -p $LOG_DIR
[ ! -f $LOG_OUT ] && touch $LOG_OUT
[ ! -f $CONSOLE_OUT ] && touch $CONSOLE_OUT

# ================================================
# STORAGE
DIR_TASK_D1=$DIR_TASK/task1.d
# ================================================
# DATABASE
DIR_TASK_D2=$DIR_TASK/task2.d
# ================================================
# MERGE
DIR_TASK_D3=$DIR_TASK/task3.d
# MERGE-E
DIR_TASK_D4=$DIR_TASK/task4.d
# ================================================

if [ $# -ne 0 -a "$1" != "-v" -a "$1" != "-f" ]; then
    echo "Usage: $0 [-v|-f]"
    echo "  -v : show version"
    echo "  -f : force run"
    exit $REC_ERR_PARAM
fi

plymouth quit

SELINUX="/etc/selinux/config"
# 修改SELINUX
if [ -f "$SELINUX" ];then
    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" $SELINUX
    /usr/sbin/setenforce 0 >> $CONSOLE_OUT 2>&1
    INFO "Change selinux to disabled"
fi

# 获取当前机器类型
SYS_MODE=`GET_PLATFORM_SYS_MODE | tr '[a-z]' '[A-Z]'`
PLATFORM=`GET_PLATFORM_PLATFORM | tr '[a-z]' '[A-Z]'`

if [ "$PLATFORM" == "" ];then
    echo "Cann't get platform info."
    exit $REC_FAIL
fi

if [ "$SYS_MODE" == "" ];then
    echo "Cann't get platform's sys mode."
    exit $REC_FAIL
fi

SHOW_VERSION
if [ "$1" == "-v" ]; then
    exit 0
fi

if [ "$1" != "-f" ]; then
    while true; do
        FLAG=`MAKE_SURE $SYS_MODE`
        [ "$FLAG" != "" ] && break
        echo "Please input Y/N."
    done
    if [ "$FLAG" == "N" ];then 
        exit $REC_EXIT_INSTALL
    fi
fi

case "$SYS_MODE" in
    "STORAGE")
        TASK_DIR=$DIR_TASK_D1
        ;;
    "DATABASE")
        TASK_DIR=$DIR_TASK_D2
        ;;
    "MERGE")
        if [[ `GET_PLATFORM_MERGE_MODE` != "" ]];then
            TASK_DIR=$DIR_TASK_D4
        else
            TASK_DIR=$DIR_TASK_D3
        fi 
        ;;
    *)
        echo "Unsupport sys mode:"$SYS_MODE
        exit $REC_ERR_PARAM
        ;;
esac

for task in $TASK_DIR/*; do
    if [ -f "$task" ];then
            $BASH $task
            ASSERT $? -eq $REC_SUCCESS
    fi
done

INFO "All action done!"
echo -e "\033[1;32m SUCCESS : All action done! \033[0m"

EXIT_WAIT
exit $REC_SUCCESS
