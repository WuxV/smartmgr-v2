#!/bin/sh

# 使用expect设置交互式命令
DRBDADM="/usr/sbin/drbdadm"
if [ -f $DRBDADM ];then
    expect -c "
    set timeout 50
    spawn $DRBDADM create-md r0
    expect {
            \"need to type 'yes' to confirm\" {send \"yes\r\"}
    }
    expect eof
    exit 0
    "
else
   echo "can't find /usr/sbin/drbdadm"
   exit 1 
fi
