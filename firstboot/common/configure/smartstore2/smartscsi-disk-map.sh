#!/bin/bash

SYS_BLOCK_DIR="/sys/block"
SMARTSCSI_VENDOR="SCST_BIO"

LOCAL_DEVICE_YES=0
LOCAL_DEVICE_NO=1

is_local_smartscsi_device()
{
    SMARTSCSI_DEVICE_DIR="/sys/kernel/scst_tgt/devices"
    local dev=$1
    if [ ! -e "$dev" ];then
        return $LOCAL_DEVICE_NO
    fi
    dev_id=$(sg_inq -p 0x83 $dev | grep "vendor specific:" |  awk '{print $3}')
    for item in $SMARTSCSI_DEVICE_DIR/*;do
        if [ -f $item/filename -a -f $item/t10_dev_id ];then
            t10_dev_id=$(head -1 $item/t10_dev_id)
            if [ "$t10_dev_id" == "$dev_id" ];then
                echo $(head -1 $item/filename)
                return $LOCAL_DEVICE_YES
            fi
        fi
    done 
    return $LOCAL_DEVICE_NO
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

DM_NAME=$1

if [ ! -d $SYS_BLOCK_DIR/$DM_NAME/slaves ]; then
    exit 1
fi

is_smartscsi_device $SYS_BLOCK_DIR/$DM_NAME
if [ $? != 0 ]; then
    exit 2
fi

is_local_smartscsi_device $SYS_BLOCK_DIR/$DM_NAME
if [ $? == $LOCAL_DEVICE_YES ];then
    exit 0
fi

SMARTSCSI_NAME=$(get_smartscsi_name $SYS_BLOCK_DIR/$DM_NAME)
if [ $? != 0 ]; then
    exit 3
else
    echo $SMARTSCSI_NAME
fi

exit 0
