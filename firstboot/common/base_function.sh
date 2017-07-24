#!/bin/bash

LOAD_CONFIG()
{
    if [ $# -ne 2 ];then
        echo "ERROR in param"
        exit $REC_ERR_PARAM
    fi

    if [ ! -f $1 ]; then
        echo "Config file '$1' not exist"
        exit $REC_CONFIG_FILE_NOT_EXIST
    fi

    if [ ! -f $2 ]; then
        echo "Config file '$2' not exist"
        exit $REC_CONFIG_FILE_NOT_EXIST
    fi

    if [ ! -x $1 ]; then
        chmod a+x $1
    fi

    if [ ! -x $2 ]; then
        chmod a+x $2
    fi

    source $1
    source $2
}

SHOW_VERSION() {
    echo ""
    echo "#=====================================#"
    echo "#         SmartMgr-FirstBoot          #"
    echo "#=====================================#"
}

EXIT_WAIT()
{
    echo ""
    echo "FirstBoot will be exit in 30 seconds"
    read -t 30 -s -p "Please type \"Enter\" key to exit immediately!"
    echo ""
}

ASSERT()
{
    if [ $# -ne 3 ];then
        echo "ERROR in assert param"
        exit $REC_ERR_PARAM
    fi

    if [ ! "$1" $2 "$3" ];then
        echo -e "\033[1;31m ERROR : Check install log and console log \033[0m"

        EXIT_WAIT
        exit $REC_FAIL
    fi
}

MAKE_SURE()
{
    if [ $# -ne 1 ];then
        echo "ERROR in param"
        exit $REC_ERR_PARAM
    fi
    read -p "You will init $1, Are you sure? (Y/N): " INPUT

    case "$INPUT" in
        y|Y)
            echo "Y"
            ;;
        n|N)
            echo "N"
            ;;
        *)
            echo ""
            ;;
    esac
}

MAKE_SURE_CONFIG()
{
    read -p "Do you want config $1? (Y/N):" INPUT

    case "$INPUT" in
        y|Y)
            echo "Y"
            ;;
        n|N)
            echo "N"
            ;;
        *)
            echo ""
            ;;
    esac
}

GET_OS_VERSION()
{
    OS_INFO=`cat /etc/system-release`
    OS_V=""
    if [ "`echo $OS_INFO | grep -i centos`" != "" ];then
        OS_V="centos"
    elif [ "`echo $OS_INFO | grep -i \"SmartStore release 3\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"SmartStore release 2\"`" != "" ];then
        OS_V="smartstore2"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 7.2\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"Oracle Linux Server release 7.0\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"Oracle Linux Server release 7.2\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"Oracle Linux Server release 6.6\"`" != "" ];then
        OS_V="smartstore2"
    elif [ "`echo $OS_INFO | grep -i \"CentOS Linux release 7.0.1406\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"CentOS Linux release 7.2.1511\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 7.2\"`" != "" ];then
        OS_V="smartstore3"
    elif [ "`echo $OS_INFO | grep -i \"Oracle Linux Server release 6.5\"`" != "" ];then
        OS_V="smartstore2"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 6.5\"`" != "" ];then
        OS_V="redhat6"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 6.6\"`" != "" ];then
        OS_V="redhat6"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 6.7\"`" != "" ];then
        OS_V="redhat6"
    elif [ "`echo $OS_INFO | grep -i \"Red Hat Enterprise Linux Server release 6.8\"`" != "" ];then
        OS_V="redhat6"
    elif [ "`echo $OS_INFO | grep -i \"CentOS release 6.3\"`" != "" ];then
        OS_V="smartstore2"
    else
        OS_V="unknow"
    fi

    echo $OS_V
}

CHECK_HOST_NAME() {
    host_name=$1
    len=${#host_name}
    stat=1
    if [ $len -ge 32 ];then
        echo $stat
        return
    fi
    result=`echo "$host_name" | grep "^[0-9a-zA-Z\.-]*$"`
    if [ "$result" != "" ];then
        stat=0
    fi
    echo $stat
}

INPUT_IP() {
    TYPE=$1
    VALUE=""
    while true; do
        read -p "Please input $TYPE:" INPUT
        if [ "$INPUT" == "" ]; then
            echo "E: Miss ip address, input '0' to skip config $TYPE!"
            continue
        fi
        if [ "$INPUT" == "0" ]; then
            break
        fi
        C=`CHECK_IP $INPUT`
        if [ "$C" -ne 0 ]; then
            echo "E: Illigal $TYPE value!"
            continue
        fi
        VALUE=$INPUT
        break;
    done
    echo $VALUE > $TMP_FILE
}

INPUT_DOMAIN() {
    TYPE=$1
    VALUE=""
    while true; do
        read -p "Please input $TYPE:" INPUT
        C=`CHECK_DOMAIN $INPUT`
        if [ "$C" -ne 0 ]; then
            echo "E: Illigal $TYPE value!"
            continue
        fi
        VALUE=$INPUT
        break;
    done
    echo $VALUE > $TMP_FILE
}

CHECK_DOMAIN() {
    local  input=$1
    local  stat=1

    if [[ $input =~ ^[0-9a-zA-Z_-]{1,16}$ ]]; then
        stat="0"
    fi
    echo $stat
}

CHECK_NODE_ID() {
    local  input=$1
    local  stat=1

    if [[ $input =~ ^[0-9]{1,3}$ ]]; then
        stat="0"
    fi
    echo $stat
}

MAKE_NODE_NAME(){
    local  input=$1
    # 获取当前机器类型
    SYS_MODE=`GET_PLATFORM_SYS_MODE | tr '[a-z]' '[A-Z]'`
    if [ "$SYS_MODE" == "" ];then
        echo "Cann't get platform's sys mode."
        exit $REC_FAIL
    fi
    
    case "$SYS_MODE" in
    "STORAGE")
        printf "su%03d" $input
        ;;
    "DATABASE")
        printf "du%03d" $input
        ;;
    "MERGE")
        printf "hu%03d" $input
        ;;
    *)
        echo "Unsupport sys mode:"$SYS_MODE
        exit $REC_ERR_PARAM
        ;;
    esac
}

CHECK_DISKPLAY_IP() {
    local  input=$1
    local  stat=1

    if [[ $input =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,2}\.[0-9]{1,2}$ ]]; then
        OIFS=$IFS
        IFS=':'
        tmp=($ip)
        ipaddr=${tmp[0]}
        dpaddr=${tmp[1]}
        IFS='.'
        ip=($ipaddr)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 \
        && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    echo $stat
}

CHECK_IP() {
    local  ip=$1
    local  stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 \
        && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    echo $stat
}

# 获取平台信息参数
GET_PLATFORM_INFO_ATTR()
{
    if [ -f $PLATFORM_INFO ]; then
        echo `cat $PLATFORM_INFO | grep -i ^$1 | awk '{print $2}'`
	    return
    else
        echo ""
	    return
    fi
}

# 获取产品平台
GET_PLATFORM_PLATFORM()
{
    echo `GET_PLATFORM_INFO_ATTR "platform"`
}

# 获取产品信息类型
GET_PLATFORM_SYS_MODE()
{
    echo `GET_PLATFORM_INFO_ATTR "sys_mode"`
}

# 获取产品信息类型
GET_PLATFORM_MERGE_MODE()
{
    echo `GET_PLATFORM_INFO_ATTR "merge_mode"`
}
