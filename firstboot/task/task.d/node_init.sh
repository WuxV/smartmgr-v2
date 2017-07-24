#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

INFO "Start init node"
Volname=`lvscan | awk '/lvvote/{print $2}' | awk -F '/' '{print $3}'`
if [ "$Volname" ==  ""x ]; then
    ERROR "can't find lvvote"
    exit $REC_ERR_NODE_INIT
else   
   str=`/usr/local/bin/smartmgrcli lun add -n /dev/mapper/${Volname}-lvvote`
   echo $str >> $CONSOLE_OUT
   if [[ $str =~ "Error" ]];then
       if [[ $str =~ "already exist" ]]; then
           INFO "Init node success"
       else
           ERROR "Error in node init"
           exit $REC_ERR_NODE_INIT
       fi
   else
       INFO "Init node success"
   fi
fi

exit $REC_SUCCESS
