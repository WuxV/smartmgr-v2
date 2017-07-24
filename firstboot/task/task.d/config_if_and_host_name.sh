#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

IFCFG_0=""
IFCFG_NAME=""
SYS_NET="/sys/class/net"
SYS_NET_ADDR="address"
NET_CONFIG="/etc/sysconfig/network-scripts"
HOSTS="/etc/hosts"

HOST_NAME=""
NODE_ID=""

IPADDR=""
NETMASK=""
GATEWAY=""
DNS1=""

# 获取当前为running状态的网卡, redhat6.5 6.6 6.7 6.8获取方法特殊处理
OS_TYPE=`GET_OS_VERSION`
if [ "$OS_TYPE" == "redhat6" ];then
	RUNNING_LIST=`ifconfig  2>/dev/null  | grep "Link encap" | awk '{print $1}' | grep -v "ib*" | grep -v "lo"`
else
	RUNNING_LIST=`ifconfig  2>/dev/null  | grep RUNNING | awk -F ':' '{print $1}' | grep -v "ib*" | grep -v "lo"`
fi

if [ "$RUNNING_LIST" == "" ];then
    # 获取ip配置文件
    for d in `ls $SYS_NET`;do
        if [ -h "$SYS_NET/$d" ];then
            if [ -r "$SYS_NET/$d/$SYS_NET_ADDR" -a `cat $SYS_NET/$d/addr_len` == 6 ];then
                IFCFG_0=$NET_CONFIG/ifcfg-$d
                INFO "User net :$d"
                IFCFG_NAME=$d
                break
            fi
        fi
    done
else
    # 选择第一个为running状态的网卡
    RUNNING_LIST=($RUNNING_LIST)
    d=${RUNNING_LIST[0]}
    IFCFG_0=$NET_CONFIG/ifcfg-$d
    IFCFG_NAME=$d
fi

# 配置IP 
if [ -f $IFCFG_0 ];then
    IP_TMP=`cat $IFCFG_0 | grep -i ipaddr`
    if [ "$IP_TMP" != "" ];then
        sed -i "s/IPADDR\(.*\)=/IPADDR=/g" $IFCFG_0
        sed -i "s/GATEWAY\(.*\)=/GATEWAY=/g" $IFCFG_0
    fi
else
    IP_TMP=""
    echo "DEVICE=\"$IFCFG_NAME\"" >> $IFCFG_0
    echo "BOOTPROTO=\"dhcp\"" >> $IFCFG_0
    echo "NM_CONTROLLED=\"yes\"" >> $IFCFG_0
    echo "ONBOOT=\"no\"" >> $IFCFG_0
    echo "TYPE=\"Ethernet\"" >> $IFCFG_0
fi

if [ "$IP_TMP" != "" ]; then
    INFO "Skip conifg ip."
else
    while true; do
        ACTION=`MAKE_SURE_CONFIG "ip"`
        [ "$ACTION" != "" ] && break
        echo "Please input Y/N."
    done
    
    if [ "$ACTION" == "Y" ];then
        INPUT_IP "ipaddr  "  && IPADDR=`cat $TMP_FILE`
        # 限制只有输入ipaddr才可以输入后面的东西
        if [ "$IPADDR" != "" ];then
            INPUT_IP "netmask " && NETMASK=`cat $TMP_FILE`
            INPUT_IP "gateway " && GATEWAY=`cat $TMP_FILE`
            INPUT_IP "dns1    " && DNS1=`cat $TMP_FILE`
        fi
    
        DEBUG "Get input ipaddr   : "$IPADDR
        DEBUG "Get input netmask  : "$NETMASK
        DEBUG "Get input gateway  : "$GATEWAY
        DEBUG "Get input dns1     : "$DNS1
    fi
fi

rm -f $TMP_FILE

# 输入NODE_ID
while true; do
    read -p "Please input node id[N]:" INPUT
    if [ "$INPUT" == "" ]; then
        echo "E: Miss node id, input '0' to skip config!"
        continue
    fi
    if [ "$INPUT" == "0" ]; then
        break
    fi
    C=`CHECK_NODE_ID $INPUT`
    if [ "$C" -ne 0 ]; then
        echo "E: Illigal node id!"
        continue
    fi
    C=`MAKE_NODE_NAME $INPUT`
    NODE_ID=$C
    HOST_NAME="dnto"${NODE_ID}
    break;
done

# 修改NODE_ID/HOSTNAME
if [ "$HOST_NAME" != "" ];then
    INFO "Change NodeId to $NODE_ID"
    INFO "Change HostName to $HOST_NAME"

    # 设置node id
    /usr/local/bin/smartmgrcli node config -a nodename=$NODE_ID >> $CONSOLE_OUT 2>&1
    if [ $? -ne 0 ];then
        ERROR "Error in set node id"
        exit $REC_ERR_SET_NODE_ID
    else
        INFO "Set node id success"
    fi

    # 设置hostname
    OS_TYPE=`GET_OS_VERSION`
    if [ "$OS_TYPE" == "smartstore3" ];then
		/usr/bin/hostnamectl set-hostname $HOST_NAME
	    /usr/bin/hostname $HOST_NAME
    else
	    sed -i "s/HOSTNAME=\(.*\)/HOSTNAME=$HOST_NAME/g" /etc/sysconfig/network	
        hostname $HOST_NAME
    fi

else
    INFO "Skip config NodeId"
    INFO "Skip config HostName"
fi

# 修改IP地址
if [ "$IPADDR" != "" ];then
    # 修改对应的配置文件
    INFO "Updata ifcfg-eth0"
    sed -i "s/ONBOOT=\"no\"/ONBOOT=\"yes\"/g" $IFCFG_0
    sed -i "s/BOOTPROTO=\"dhcp\"/BOOTPROTO=\"static\"/g" $IFCFG_0
    [ "$IPADDR"  != "" ] && echo "IPADDR=\"$IPADDR\""   >> $IFCFG_0 
    [ "$NETMASK" != "" ] && echo "NETMASK=\"$NETMASK\"" >> $IFCFG_0
    [ "$GATEWAY" != "" ] && echo "GATEWAY=\"$GATEWAY\"" >> $IFCFG_0
    [ "$DNS1"    != "" ] && echo "DNS1=\"$DNS1\""       >> $IFCFG_0

    # 创建重启网卡标记,用于完成所有task时,重启网络,准许用户登陆
    touch $TMP_FILE_NETWORK

    # 将Mac地址，写回到对应的配置文件
    INFO "Update hwaddr"
    for d in `ls $SYS_NET`;do
        if [ -h "$SYS_NET/$d" ];then
            if [ -r "$SYS_NET/$d/$SYS_NET_ADDR" -a -f "$NET_CONFIG/ifcfg-$d" ];then
                INFO "Update $d hwaddr"
                hw=`cat "$SYS_NET/$d/$SYS_NET_ADDR"`
                echo "HWADDR=\"$hw\"" >> "$NET_CONFIG/ifcfg-$d"
            fi
        fi
    done
fi

# 修改/etc/hosts
if [ "$IPADDR" != "" -a "$HOST_NAME" != "" ];then
    INFO "Update /etc/hosts"
    echo "127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4" > $HOSTS
    echo "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6" >> $HOSTS
    echo $IPADDR"   "$HOST_NAME >> $HOSTS
fi

# 修改smartmgr的配置的文件
# 重新获取ip地址
IPADDR=`cat $IFCFG_0 | grep -i ipaddr | awk -F '=' '{print $2}' | tr -d '"'`
if [ "$IPADDR" != "" ];then
    sed -i s/"listen-ip\(.*\)"/"listen-ip               = $IPADDR"/g /opt/smartmgr/conf/service.*.ini
fi

INFO "Stop iptables"

OS_TYPE=`GET_OS_VERSION`
if [ "$OS_TYPE" == "smartstore3" ];then
    systemctl stop firewalld.service >> $CONSOLE_OUT 2>&1
    systemctl disable firewalld.service >> $CONSOLE_OUT 2>&1
else
    service iptables stop >> $CONSOLE_OUT 2>&1
    chkconfig iptables off >> $CONSOLE_OUT 2>&1
fi

exit $REC_SUCCESS
