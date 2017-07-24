#!/bin/bash

SYS_BLOCK_DIR="/sys/block"
ASM_DIR=/dev/srbddisks
DEV_DIR=/dev/

ACTION=$1
DRBD_NAME="srbd1"

slogger() 
{
    #echo `date +"[%H:%M:%S]"` $1 >> /tmp/drbd-disk-map.log
    logger -i $1
}


drbd_mknod()
{
    local DEV=$1
    local DRBD_NAME=$2

    local major=`stat $DEV --print="%t"`
    if [ $? != 0 ];then
        return 4
    fi
    local minor=`stat $DEV --print="%T"`
    if [ $? != 0 ];then
        return 4
    fi
    if [ "$minor" == "" -a "$major" == "" ];then
        return 4
    fi
    if [ ! -d $ASM_DIR ];then
        mkdir -p $ASM_DIR
        chown -R grid:asmadmin $ASM_DIR
    fi
    
    if [ -b $ASM_DIR/$DRBD_NAME ];then
        check_maj_min_eq $DRBD_NAME $major $minor
        if [ $? == 0 ];then
            slogger "[drbd-disk-map]:already exist $DRBD_NAME major minor equal $major $minor and return"
            return 0
        fi
        slogger "[drbd-disk-map]:already exist"
        rm -rf $ASM_DIR/$DRBD_NAME
        if [ $? != 0 ];then
            slogger "[drbd-disk-map]:rm $ASM_DIR/$DRBD_NAME Failed"
        else
            slogger "[drbd-disk-map]:rm $ASM_DIR/$DRBD_NAME"
        fi
    fi

    mknod -m 660 $ASM_DIR/$DRBD_NAME b 0x$major 0x$minor
    if [ $? != 0 ]; then
        slogger "[drbd-disk-map]:mknod -m 660 $ASM_DIR/$DRBD_NAME b 0x$major 0x$minor Failed"
    else
        slogger "[drbd-disk-map]:mknod -m 660 $ASM_DIR/$DRBD_NAME b 0x$major 0x$minor OK"
    fi

    chown grid:asmadmin $ASM_DIR/$DRBD_NAME
    if [ $? != 0 ]; then
        slogger -i "[drbd-disk-map]:chown grid:asmadmin $ASM_DIR/$DRBD_NAME Failed"
    fi
}

check_maj_min_eq()
{
    local DRBD_NAME=$1
    local major=$2
    local minor=$3

    local major_l=`stat $ASM_DIR/$DRBD_NAME --print="%t"`
    if [ $? != 0 ];then
        return 1
    fi
    local minor_l=`stat $ASM_DIR/$DRBD_NAME --print="%T"`
    if [ $? != 0 ];then
        return 2
    fi
    if [ "$major"x  == "$major_l"x ]; then
        if [ "$minor"x == "$minor_l"x ]; then
            slogger "[drbd-disk-map]:major=$major major_l=$major_l minor=$minor  minor_l=$minor_l"
            return 0
        fi
    fi
    return 3
}
remove_drbd_disks()
{   
    local major=$1
    local minor=$2
    local list=`ls $ASM_DIR/`
    for i in $list
    do
        local major_16=`stat $ASM_DIR/$i --print="%t"`
        if [ $? != 0 ];then
            return 1
        fi
        local minor_16=`stat $ASM_DIR/$i --print="%T"`
        if [ $? != 0 ];then
            return 1
        fi
        ((major_l=16#$major_16))
        ((minor_l=16#$minor_16))

        if [ "$major"x  == "$major_l"x ]; then
            if [ "$minor"x == "$minor_l"x ]; then
                slogger "[drbd-disk-map]:major=$major major_l=$major_l minor=$minor  minor_l=$minor_l"
                slogger "[drbd-disk-map]:dir=$ASM_DIR/$i"
                rm -rf $ASM_DIR/$i
                if [ $? != 0 ];then
                    slogger "[drbd-disk-map]:rm $ASM_DIR/$i Failed"
                    return 1
                else
                    slogger "[drbd-disk-map]:rm $ASM_DIR/$i"
                    return 0
                fi

            fi

        fi
    done
}

if [ "$ACTION"x == "remove"x ]; then
    MAJOR=$2
    MINOR=$3
    slogger "[drbd-disk-map]:action=$ACTION major=$MAJOR minor=$MINOR"
    remove_drbd_disks $MAJOR $MINOR
    if [ $? != 0 ]; then
        exit 10
    fi
    exit 0
elif [ "$ACTION"x == "add"x ]; then
    DM_NAME=$2
    slogger "[drbd-disk-map]:action=$ACTION dm_name=$DM_NAME"

    if [ ! -d $SYS_BLOCK_DIR/$DM_NAME/slaves ]; then
        slogger "[drbd-disk-map]:$SYS_BLOCK_DIR/$DM_NAME/slaves not exitst"
        exit 1
    fi
    DRBD_NAME="srbd1" 
    # 使用/dev/mapper/
    drbd_mknod $DEV_DIR/$DM_NAME $DRBD_NAME
    if [ $? != 0 ]; then
        slogger "[drbd-disk-map]:mknod $DM_NAME $DRBD_NAME failed"
        exit 4
    fi
fi
exit 0
