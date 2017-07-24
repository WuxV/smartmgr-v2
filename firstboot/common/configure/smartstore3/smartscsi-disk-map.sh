#!/bin/bash

SYS_BLOCK_DIR="/sys/block"
SMARTSCSI_VENDOR="SCST_BIO"
ASM_DIR=/dev/asmdisks
DEV_DIR=/dev/

LOCAL_DEVICE_YES=0
LOCAL_DEVICE_NO=1

ACTION=$1

is_local_smartscsi_device()
{
    SYS_MODE=$(cat /boot/installer/platform  | grep SYS_MODE | tr '[A-Z]' '[a-z]' | awk '{print $2}')
    if [ "$SYS_MODE" != "merge" ];then
        return $LOCAL_DEVICE_NO
    fi

    SMARTSCSI_DEVICE_DIR="/sys/kernel/scst_tgt/devices"
    local dev=$1
    dev_id=$(sg_inq -p 0x83 $dev | grep "vendor specific:" |  awk '{print $3}')
    t10_ids=$(smartmgrcli lun list --json | grep lun_id | cut -d \" -f 4 | cut -d - -f 1-4)

    [ "$dev_id" == "" ]  && return $LOCAL_DEVICE_YES
    [ "$t10_ids" == "" ] && return $LOCAL_DEVICE_YES

    if [[ $t10_ids =~ $dev_id ]];then
        return $LOCAL_DEVICE_YES
    fi
    return $LOCAL_DEVICE_NO
}

slogger() 
{
    # user.notice
    logger -i -p user.$1 "[smartscsi-disk-map]:$2"
}

is_smartscsi_device()
{
    local dm_path=$1
    local symbol=""
    local scsi_path=""
    local vendor_path=""
    local vendor=""
    local item=""

    for item in $dm_path/slaves/*
    do
        symbol=$(readlink $item)
        scsi_path=${symbol%/block/*}
        vendor_path="$dm_path/slaves/$scsi_path/vendor"
        if [ -e $vendor_path ]; then
            vendor=$(cat $vendor_path)
            if [ "$vendor"x != "$SMARTSCSI_VENDOR"x ]; then
                return 1
            fi
        else
            return 2
        fi
    done

    if [ "$vendor"x == ""x ]; then
        return 3
    fi
    return 0
}

get_smartscsi_name()
{
    local dm_path=$1
    local symbol=""
    local scsi_path=""
    local model_path=""
    local model=""
    local model_tmp=""
    local item=""

    for item in $dm_path/slaves/*
    do
        symbol=$(readlink $item)
        scsi_path=${symbol%/block/*}
        model_path="$dm_path/slaves/$scsi_path/model"
        if [ -e $model_path ]; then
            model_tmp=$(cat $model_path)
            if [ "$model_tmp" == ""x ]; then
                return 1
            fi
            if [ "$model"x == ""x ]; then
                model=$model_tmp
            else
                if [ "$model_tmp"x != "$model"x ]; then
                    return 2
                fi
            fi
        else
            return 3
        fi
    done

    if [ "$model"x == ""x ]; then
        return 4
    else
        echo $model
    fi

    return 0
}

get_mpath_alias()
{
    if [ -e $SYS_BLOCK_DIR/$1/dm/name ]; then
        cat $SYS_BLOCK_DIR/$1/dm/name
    else
        slogger "warning" "unknown mpath alias for $1"
    fi
}

smartscsi_mknod()
{
    local DEV=$1
    local SMARTSCSI_NAME=$2

    local major=`stat $DEV --print="%t"`
    if [ $? -ne 0 ];then
        return 4
    fi
    local minor=`stat $DEV --print="%T"`
    if [ $? -ne 0 ];then
        return 4
    fi
    if [ "$minor"x == ""x -a "$major"x == ""x ];then
        return 4
    fi
    if [ ! -d $ASM_DIR ];then
        mkdir -p $ASM_DIR
        chown -R grid:asmadmin $ASM_DIR
    fi
    
    if [ -b $ASM_DIR/$SMARTSCSI_NAME ];then
        check_maj_min_eq $SMARTSCSI_NAME $major $minor
        if [ $? -eq 0 ];then
            slogger "debug" "already exist $SMARTSCSI_NAME major minor equal $major $minor and return"
            return 1
        fi
        slogger "warning" "$ASM_DIR/$SMARTSCSI_NAME already exist but different from $major:$minor"
        rm -rf $ASM_DIR/$SMARTSCSI_NAME
        if [ $? -ne 0 ];then
            slogger "err" "rm $ASM_DIR/$SMARTSCSI_NAME Failed"
            return 5
        else
            slogger "debug" "rm $ASM_DIR/$SMARTSCSI_NAME"
        fi

    fi

    mknod -m 660 $ASM_DIR/$SMARTSCSI_NAME b 0x$major 0x$minor
    if [ $? -ne 0 ]; then
        slogger "err" "mknod -m 660 $ASM_DIR/$SMARTSCSI_NAME b 0x$major 0x$minor Failed"
        return 6
    else
        slogger "debug" "mknod -m 660 $ASM_DIR/$SMARTSCSI_NAME b 0x$major 0x$minor OK"
    fi

    chown grid:asmadmin $ASM_DIR/$SMARTSCSI_NAME
    if [ $? -ne 0 ]; then
        slogger "err" "chown grid:asmadmin $ASM_DIR/$SMARTSCSI_NAME Failed"
        return 7
    fi
}

check_maj_min_eq()
{
    local SMARTSCSI_NAME=$1
    local major=$2
    local minor=$3

    local major_l=`stat $ASM_DIR/$SMARTSCSI_NAME --print="%t"`
    if [ $? -ne 0 ];then
        return 1
    fi
    local minor_l=`stat $ASM_DIR/$SMARTSCSI_NAME --print="%T"`
    if [ $? -ne 0 ];then
        return 2
    fi
    if [ "$major"x  == "$major_l"x ]; then
        if [ "$minor"x == "$minor_l"x ]; then
            slogger "debug" "major=$major major_l=$major_l minor=$minor  minor_l=$minor_l"
            return 0
        fi
    fi
    return 3
}

remove_asm_disks()
{   
    local major=$1
    local minor=$2
    local list=`ls $ASM_DIR/`
    for i in $list
    do
        local major_16=`stat $ASM_DIR/$i --print="%t"`
        if [ $? -ne 0 ];then
            return 1
        fi
        local minor_16=`stat $ASM_DIR/$i --print="%T"`
        if [ $? -ne 0 ];then
            return 1
        fi
        ((major_l=16#$major_16))
        ((minor_l=16#$minor_16))

        if [ "$major"x  == "$major_l"x ]; then
            if [ "$minor"x == "$minor_l"x ]; then
                slogger "debug" "major=$major major_l=$major_l minor=$minor  minor_l=$minor_l"
                slogger "debug" "dir=$ASM_DIR/$i"
                rm -rf $ASM_DIR/$i
                if [ $? -ne 0 ];then
                    slogger "err" "remove $ASM_DIR/$i Failed"
                    return 1
                else
                    slogger "notice" "remove $ASM_DIR/$i"
                    return 0
                fi
            fi
        fi
    done

}

if [ "$ACTION"x == "remove"x ]; then
    MAJOR=$2
    MINOR=$3
    slogger "debug" "action=$ACTION major=$MAJOR minor=$MINOR"
    remove_asm_disks $MAJOR $MINOR
    if [ $? -ne 0 ]; then
        exit 10
    fi
    exit 0
elif [ "$ACTION"x == "add"x ]; then
    DM_NAME=$2
    slogger "debug" "action=$ACTION dm_name=$DM_NAME"

    if [ ! -d $SYS_BLOCK_DIR/$DM_NAME/slaves ]; then
        slogger "err" "$SYS_BLOCK_DIR/$DM_NAME/slaves not exitst"
        exit 1
    fi

    is_smartscsi_device $SYS_BLOCK_DIR/$DM_NAME
    if [ $? -ne 0 ]; then
        slogger "err" "$SYS_BLOCK_DIR/$DM_NAME is not smartscsi_device"
        exit 2
    fi
    
    SMARTSCSI_NAME=$(get_smartscsi_name $SYS_BLOCK_DIR/$DM_NAME)
    if [ $? -ne 0 ]; then
        exit 3
    fi

    is_local_smartscsi_device $DEV_DIR/$DM_NAME

    # 使用/dev/mapper/
    if [ $? == $LOCAL_DEVICE_NO ];then
        MPATH_ALIAS=$(get_mpath_alias $DM_NAME)
        smartscsi_mknod $DEV_DIR/$DM_NAME $SMARTSCSI_NAME
        if [ $? -eq 0 ]; then
            slogger "notice" "mapped $SMARTSCSI_NAME to $DM_NAME[$MPATH_ALIAS]"
        elif [ $? -eq 1 ]; then
            slogger "debug" "exists mapping of $SMARTSCSI_NAME to $DM_NAME[$MPATH_ALIAS]"
        else
            slogger "err" "smartscsi_mknod $SMARTSCSI_NAME for $DM_NAME[$MPATH_ALIAS] failed"
            exit 4
        fi
    else
        slogger "debug" "skip mknod for local device $DM_NAME"
    fi
else
    slogger "err" "not support action"
fi

exit 0
