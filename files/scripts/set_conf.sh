#!/bin/sh

#srbd的节点资源文件
SRBD_R0="/etc/drbd.d/r0.res"
SRBD_R0_BAK="/etc/drbd.d/r0.res_bak"

NET_CONFIG="/etc/sysconfig/network-scripts"

TMP_CONF="/opt/smartmgr/conf/service.mds.ini"
#TMP_CONF="/root/smartmgr-v2/files/conf/test/service.mds.216.ini"

# corosync的配置文件
COROSYNC_CONF="/etc/systemd/system/multi-user.target.wants/corosync.service"

# 配置/etc/systemd/system/multi-user.target.wants/corosync.service文件
# 需要在默认的配置文件中新添加两项配置，Requires=network.target After=network.target
if [ -f $COROSYNC_CONF ]; then
    grep -q "Requires=network.target" $COROSYNC_CONF
    if [ $? -ne 0 ]; then
        sed -i '/\[Unit\]/a\Requires=network.target\nAfter=network.target' $COROSYNC_CONF
    fi
fi

function SET_HOSTS() {
    hostname=$1
    host_ip=$2
    HOSTS_FILE="/etc/hosts"
    if [ -f $HOSTS_FILE ];then
        IP_TMP=`cat $HOSTS_FILE | grep -i $hostname`
        if [ "$IP_TMP" != "" ]; then
            ht=`echo $IP_TMP | awk '{print $1}'`
#            if [ "$ht" != "$host_ip" ];then
#                eval sed -i "s/$ht/$host_ip/g" $HOSTS_FILE
#            fi
        else
            echo "$host_ip    $hostname" >> $HOSTS_FILE
        fi
    fi
}

# node1_name,node1_ip,node2_name,node2_ip表示本机和对端ip，hostname信息
node1_ip=$1
node1_mask=$2
node1_name=$3
node1_srbd_netcard=$4
node2_ip=$5
node2_passwd=$6

# 配置配置srbd网络
SRBD_CARD_IFCFG=$NET_CONFIG/ifcfg-${node1_srbd_netcard}
if [ -f $SRBD_CARD_IFCFG ];then
    IP_TMP=`cat $SRBD_CARD_IFCFG | grep -i IPADDR`
    if [ "$IP_TMP" != "" ];then
        sed -i "s/IPADDR\(.*\)=\(.*\)/IPADDR=$node1_ip/i" $SRBD_CARD_IFCFG
        sed -i "s/NETMASK\(.*\)=\(.*\)/NETMASK=$node1_mask/i" $SRBD_CARD_IFCFG
        sed -i "s/ONBOOT\(.*\)=\(.*\)/ONBOOT=yes/i" $SRBD_CARD_IFCFG
        sed -i "s/BOOTPROTO\(.*\)=\(.*\)/BOOTPROTO=static/i" $SRBD_CARD_IFCFG
    else
        echo "IPADDR=$node1_ip" >> $SRBD_CARD_IFCFG
        echo "NETMASK=$node1_mask" >> $SRBD_CARD_IFCFG
        sed -i "s/ONBOOT\(.*\)=\(.*\)/ONBOOT=yes/i" $SRBD_CARD_IFCFG
        sed -i "s/BOOTPROTO\(.*\)=\(.*\)/BOOTPROTO=static/i" $SRBD_CARD_IFCFG
    fi
else
    echo "DEVICE=$node1_srbd_netcard" >> $SRBD_CARD_IFCFG
    echo "BOOTPROTO=static" >> $SRBD_CARD_IFCFG
    echo "NM_CONTROLLED=yes" >> $SRBD_CARD_IFCFG
    echo "ONBOOT=yes" >> $SRBD_CARD_IFCFG
    echo "TYPE=Ethernet" >> $SRBD_CARD_IFCFG
    echo "IPADDR=$node1_ip" >> $SRBD_CARD_IFCFG
    echo "NETMASK=$node1_mask" >> $SRBD_CARD_IFCFG
fi

# 配置网卡后要重启
service network restart >> /dev/null 2>&1 
if [ $? -ne 0 ];then
    echo "restart network failed"
    exit 1
fi

# 判断是否能ping通对方，ping 100秒
c1=$(/bin/ping $node2_ip -c 1|grep "bytes from"|wc -l)
for i in {1..100}
do
    if [[ $c1 -gt 0 ]];then
        break
    else
        sleep 1
        continue
    fi
done

if [[ $i -ge 100 ]];then
    echo "Check to see connected to $IP?"
    exit 1
fi 

# 设置互信，访问对端，需要对端的用户和密码
id_rsa="/root/.ssh/id_rsa"
AUTHORIZED_KEYS="/root/.ssh/authorized_keys"
if [ ! -f $id_rsa ];then
    ssh-keygen -q -t rsa  -N "" -f $id_rsa > /dev/null 2>&1
fi
    
KNOW_HOSTS="/root/.ssh/known_hosts"
if [ -f $KNOW_HOSTS ];then
    sed -i "s/$node2_ip//g" $KNOW_HOSTS 
fi

cat ${id_rsa}.pub >> $AUTHORIZED_KEYS
expect -c "
spawn scp $AUTHORIZED_KEYS root@${node2_ip}:${AUTHORIZED_KEYS}
expect {
        \"*assword\" {set timeout 300; send \"${node2_passwd}\r\";}
        \"yes/no\" {send \"yes\r\"; exp_continue;}
        \"*lost connection\" {send \"exit\r\"}
}
expect eof
exit 0
"

# 到对端获取hostname
node2_name=`ssh $node2_ip hostname`
if [ $? -ne 0 ];then
    echo "Unable to communicate with ${node2_ip}"
    exit 1
fi

expect -c "
spawn ssh $node2_name
expect {
        \"yes/no\" {send \"yes\r\"; exp_continue;}
}
expect eof
exit 0 
"

# 配置node1,node2在hosts的信息
if [ "$node2_name" != "" -a "$node2_ip" != "" -a "$node1_name" != "" -a "$node1_ip" != "" ];then
    SET_HOSTS $node1_name $node1_ip
    SET_HOSTS $node2_name $node2_ip
    SET_HOSTS ${node1_name}-priv $node1_ip
    SET_HOSTS ${node2_name}-priv $node2_ip
else
    echo "cant't set hosts,node1,node2 miss drdb ip or node_name"
    exit 1
fi

# 查询lvvote路径，并配置r0.res资源文件
lvvote=`lvscan | awk '/lvvote/{print $2}' | sed 's/^.//;s/.$//'`
if [ "$lvvote" = "" ]; then
    echo "can't find lvvote device"
    exit 1
fi

if [ -f $SRBD_R0 ];then
    mv $SRBD_R0 $SRBD_R0_BAK
fi

if [ ! -f "$SRBD_R0" ];then
    echo "resource r0 {     
  on ${node1_name}{    
    device    /dev/drbd1;    
    disk      ${lvvote};   
    address   ${node1_ip}:7789;   
    meta-disk internal; 
  } 
  on ${node2_name}{
    device    /dev/drbd1;
    disk      ${lvvote};
    address   ${node2_ip}:7789;
    meta-disk internal;
  }
}
  " >> $SRBD_R0
fi

exit 0

