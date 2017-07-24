#!/bin/sh
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"
TMP_CONF="/opt/smartmgr/conf/service.mds.ini"
#TMP_CONF="/root/smartmgr-v2/files/conf/test/service.mds.216.ini"

SRBD_CONF="$ROOT_DIR/common/configure/global_common.conf"
SRBD_DEVICE_RULES="$ROOT_DIR/common/configure/smartstore3/91-srbdasm.rules"

DRBD_DEVICE_RULES="$ROOT_DIR/common/configure/smartstore3/93-drbd-asmdevices.rules"
DRBD_MAP_SCRIPT="$ROOT_DIR/common/configure/smartstore3/drbd-disk-map.sh"

SSHD_CONFIG="/etc/ssh/sshd_config"

node1_hostname=`/usr/bin/hostname`
node1_srbd_ip=""
node1_srbd_netcard=""

node2_hostname=""
node2_srbd_ip=""

function SET_KEY_VALUE()
{
    # 参数1是node，参数2是node对应的配置信息
    local node=$1
    local key=$2
    local value=$3
    if [ -f "$TMP_CONF" ];then
        _node=`cat $TMP_CONF | grep -i "\[${node}\]"`
        if [ "$_node"x != ""x ];then
            _key=`cat $TMP_CONF | grep -i $key`
            if [ "$_key" != "" ];then
                sed -i "s/${key}\(.*\)=\(.*\)/${key}          =${value}/g" $TMP_CONF
            else
                sed -i "/\[${node}\]/a\\${key}            =${value}" $TMP_CONF
            fi
        else
            echo -e "\n[${node}]" >> $TMP_CONF
            echo "${key}           =${value}" >> $TMP_CONF
        fi
    else
	    echo -e "\n[${node}]" >> $TMP_CONF
            echo "${key}           =${value}" >> $TMP_CONF
    fi
} 
 
function LIST_NODE()
{
    local node=$1
    if [ -f "$TMP_CONF" ];then
        value=`cat $TMP_CONF | grep -i $node | grep -v "\[$node\]" | cut -b 7- | awk -F '=' '{print $1" : "$2}'`
        if [ "$value"x != "" ];then
            echo $value    
        else
            echo "$node info lost"
        fi
    fi
}

function CONFIG_NODE1 {
    # 使用impitool工具获取ip信息时需要加载内存模块
    rpm -q ipmitool > /dev/null 2>&1
    if [ $? -eq 0 ];then
        /usr/sbin/modprobe ipmi_watchdog > /dev/null 2>&1
        /usr/sbin/modprobe ipmi_poweroff > /dev/null 2>&1
        /usr/sbin/modprobe ipmi_devintf > /dev/null 2>&1
        # 获取本机的impi的ip地址，两个节点需要单独设置
        node1_ipmi_ip=`ipmitool lan print 1 | grep "IP Address" | awk -F ':' '{if($2~/[0-9]/) print $2}'`
    fi
    
    if [ "$node1_ipmi_ip"x  != ""x ];then
        while true;do
            read -p "Do you want to use ipmi_ip($node1_ipmi_ip) [Y/N]:" choice
            case "$choice" in
                y|Y)
                    break
                    ;;
                n|N)
                    INPUT_IP "ipmi_ip " && node1_ipmi_ip=`cat $TMP_FILE`
                    break
                    ;;
                *)
                    echo ""
                    ;;
            esac
        done
    else
        INPUT_IP "ipmi_ip " && node1_ipmi_ip=`cat $TMP_FILE`
    fi
    
    # systemctl start NetworkManager
    OS_TYPE=`GET_OS_VERSION`
    if [ $OS_TYPE == "smartstore3" ];then
        systemctl start NetworkManager >> $CONSOLE_OUT 2>&1
    fi
    sleep 2
    # 获取当前为running状态的网卡
    RUNNING_LIST=`ifconfig  2>/dev/null  | grep RUNNING | awk -F ':' '{print $1}' | grep -v "ib*" | grep -v "lo"`
    RUNNING_LIST=($RUNNING_LIST)
    num=${#RUNNING_LIST[@]}
    
    while true;do
        INFO "please choose nework-card you want to set srbd network"
        a=0
        b=0
        for i in ${RUNNING_LIST[*]};do
            if [ "$i" != "${RUNNING_LIST[0]}" ];then
                echo -n "[${a}] $i "
                b=1
            fi
            ((a++))
        done
        if [ "$b"x = "0"x ];then
            ERROR "Confirm network card whether connected to the network?"
            exit 1
	fi
        read -p "[example.1]:" choice
        match=0
        for ((i=0;i<${num};i++))
        do
           if [ "$i"x = "$choice"x ];then
              node1_srbd_netcard=${RUNNING_LIST[${choice}]}
              match=1 
              break
           fi
        done
        if [ "$match"x = "1"x ];then
           break
        else
           continue
        fi
    done

    INFO "please configure $node1_srbd_netcard ip"
    INPUT_IP "${node1_srbd_netcard} srbd ip" && node1_srbd_ip=`cat $TMP_FILE`
    if [ "$node1_srbd_ip" != "" ];then
        INPUT_IP "${node1_srbd_netcard} srbd netmask " && node1_srbd_mask=`cat $TMP_FILE`
    fi
    node1_hostname=`hostname`
    SET_KEY_VALUE  "node1" "node1_hostname" $node1_hostname
    SET_KEY_VALUE  "node1" "node1_ipmi_ip" $node1_ipmi_ip
    SET_KEY_VALUE  "node1" "node1_srbd_ip" $node1_srbd_ip
    SET_KEY_VALUE  "node1" "node1_srbd_mask" $node1_srbd_mask
    SET_KEY_VALUE  "node1" "node1_srbd_netcard" $node1_srbd_netcard
}

function CONFIG_NODE2 {
    # 开始输入第二节点的信息，srbd_ip ipmi_ip hostname 
    INFO "Begin configure the second node infomation"
    
    INPUT_IP "srbd ip" && node2_srbd_ip=`cat $TMP_FILE`
    INPUT_IP "ipmi ip" && node2_ipmi_ip=`cat $TMP_FILE`
    read -p "Please input root passwd :" node2_passwd
    
    SET_KEY_VALUE  "node2" "node2_ipmi_ip" $node2_ipmi_ip
    SET_KEY_VALUE  "node2" "node2_srbd_ip" $node2_srbd_ip
    SET_KEY_VALUE  "node2" "node2_passwd" $node2_passwd
} 

CONFIG_NODE1
while true;do
    LIST_NODE node1 
    read -p "Do you want to modify the above information ? (Y/N):" INPUT
    case "$INPUT" in
        y|Y)
            CONFIG_NODE1 
            ;;
        n|N)
            break
            ;;
        *)
            echo ""
            ;;
    esac
done

CONFIG_NODE2
while true;do
    LIST_NODE node2 
    read -p "Do you want to modify the above information ? (Y/N):" INPUT
    case "$INPUT" in
        y|Y)
            CONFIG_NODE2
            ;;
        n|N)
            break
            ;;
        *)
            echo ""
            ;;
    esac
done

# srbd rules文件拷贝
if [ ! -f $SRBD_DEVICE_RULES ]; then
    ERROR "Cann't find config file: $SRBD_DEVICE_RULES"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $DRBD_DEVICE_RULES ]; then
    ERROR "Cann't find config file: $DRBD_DEVICE_RULES"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $DRBD_MAP_SCRIPT ]; then
    ERROR "Cann't find config file: $DRBD_MAP_SCRIPT"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -d "/etc/udev/rules.d" ]; then
    ERROR "Udev rules dir not exist"
    exit $REC_DIR_NOT_EXIST
fi

if [ ! -d "/etc/asm_dev_map" ]; then
    mkdir -p "/etc/asm_dev_map"
fi

INFO "Install srbd rules config"
cp -f $SRBD_DEVICE_RULES "/etc/udev/rules.d"
cp -f $DRBD_DEVICE_RULES "/etc/udev/rules.d"
cp -f $DRBD_MAP_SCRIPT "/etc/asm_dev_map"

# srbd配置文件拷贝
if [ ! -f $SRBD_CONF ];then
    ERROR "Cann't find config file: $SRBD_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

INFO "Install srbd config"
cp -f $SRBD_CONF "/etc/drbd.d/"

# 创建.ssh文件夹
mkdir -p /root/.ssh/

#配置sshd_config文件,
if [ -f $SSHD_CONFIG ]; then
    sed -i "s/^#PermitRootLogin/PermitRootLogin/g" $SSHD_CONFIG
    sed -i "s/^#RSAAuthentication/RSAAuthentication/g" $SSHD_CONFIG
    sed -i "s/^#PubkeyAuthentication/PubkeyAuthentication/g" $SSHD_CONFIG
    sed -i "s/^#StrictModes yes/StrictModes no/g" $SSHD_CONFIG
fi

# 写入lvvote设配数据，防止初始化drbd元数据失败
lvvote=`lvscan | awk '/lvvote/{print $2}' | sed 's/^.//;s/.$//'`
if [ "$lvvote"x != ""x ];then
    dd if=/dev/zero of=${lvvote} bs=1M count=100
fi

# 重启sshd pacemaker服务
OS_TYPE=`GET_OS_VERSION`
if [ "$OS_TYPE" == "smartstore3" ];then
    systemctl restart sshd.service >> $CONSOLE_OUT 2>&1
    systemctl restart pacemaker >> $CONSOLE_OUT 2>&1
else
    service sshd restart >> $CONSOLE_OUT 2>&1
    service pacemaker restart >> $CONSOLE_OUT 2>&1
fi

# pcs配置：密码配置及pcs服务启动,默认pcs，corosync,packmaker集群软件已经安装
# 配置hacluster用户密码,默认密码是root123
echo "root123" | passwd --stdin hacluster
if [ $? -ne 0 ]; then
    ERROR "set hacluster passwd failed"
    exit $REC_ERR_PASSWD_HACLUSTER
fi

# 设置srbd模块的启动加载
srbd_modules="/etc/sysconfig/modules/srbd.modules"
echo "/sbin/modprobe drbd" > $srbd_modules
chmod 755 $srbd_modules

# 启动pcsd服务
INFO "Start pcsd"
OS_TYPE=`GET_OS_VERSION`
if [ "$OS_TYPE" == "smartstore3" ];then
    systemctl start pcsd.service >> $CONSOLE_OUT 2>&1
    systemctl enable  pcsd.service >> $CONSOLE_OUT 2>&1
    systemctl enable  drbd.service >> $CONSOLE_OUT 2>&1
    systemctl enable corosync.service >> $CONSOLE_OUT 2>&1
    systemctl enable pacemaker.service >> $CONSOLE_OUT 2>&1
else
    service pcsd start >> $CONSOLE_OUT 2>&1
    chkconfig pcsd on >> $CONSOLE_OUT 2>&1
    chkconfig drbd on >> $CONSOLE_OUT 2>&1
    chkconfig corosync on >> $CONSOLE_OUT 2>&1
    chkconfig pacemaker on >> $CONSOLE_OUT 2>&1
fi

INFO "Config srbd finish"
exit $REC_SUCCESS
