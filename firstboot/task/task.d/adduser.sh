#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

INFO "EXE $0"

GROUP_CONF="/etc/group"
PWD_CONF="/etc/passwd"
LIMIT_CONF="/etc/security/limits.conf"
PROFILE="/etc/profile"

NODE_ID=""
while true; do
    read -p "Please input node id [N]:" INPUT
    if [ "$INPUT" == "" ]; then
        echo "E: Miss node id"
        continue
    fi
    C=`CHECK_NODE_ID $INPUT`
    if [ "$C" -ne 0 ]; then
        echo "E: Illigal node id value!"
        continue
    fi
    NODE_ID=$INPUT
    break;
done

ORACLE_RELEASE=""
while true; do
    read -p "Please input oracle release [A.B.C.D]:" INPUT
    if [ "$INPUT" == "" ]; then
        echo "E: Miss oracle release"
        continue
    fi
    ORACLE_RELEASE=$INPUT
    break;
done

DP=""
while true; do
    read -p "Please input display [IP:A.B]" INPUT
    if [ "$INPUT" == "" ]; then
        echo "E: Miss display ip"
        continue
    fi
    C=`CHECK_DISKPLAY_IP $INPUT`
    if [ "$C" -ne 0 ]; then
        echo "E: Illigal display value!"
        continue
    fi
    DP=$INPUT
    break;
done

sys_groupadd()
{
    local group_name=$1
    local gid=$2
    grep $group_name $GROUP_CONF >/dev/null 2>&1
    if [ $? != 0 ]; then
	    /usr/sbin/groupadd -g $gid $group_name >> $CONSOLE_OUT 2>&1
	    if [ $? != 0 ]; then
	        WARNING "Failed to add group : $group_name"
	    fi
    fi
}

sys_useradd()
{
    local user_name=$1
    local init_group_name=$2
    local groups=$3
    local uid=$4
    grep $user_name $PWD_CONF >/dev/null 2>&1
    if [ $? != 0 ]; then
	    /usr/sbin/useradd -u $uid -g $init_group_name -G $groups $user_name >> $CONSOLE_OUT 2>&1
	    if [ $? != 0 ]; then
	        WARNING "Failed to add user: $user_name"
	    fi
    fi
}

sys_limit()
{
    local user_name=$1
    if [ -f $LIMIT_CONF ]; then
	    grep $user_name $LIMIT_CONF >/dev/null 2>&1
        if [ $? != 0 ]; then
	        echo "$user_name              soft    nproc   2047"	    >> $LIMIT_CONF
	        echo "$user_name              hard    nproc   16384"    >> $LIMIT_CONF
	        echo "$user_name              soft    nofile  1024"	    >> $LIMIT_CONF
	        echo "$user_name              hard    nofile  65536"    >> $LIMIT_CONF
	    fi
    fi
}

INFO "Config user and group"

if [ ! -f $PWD_CONF ]; then
    ERROR "Cann't find config file: $PWD_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

if [ ! -f $GROUP_CONF ]; then
    ERROR "Cann't find config file: $GROUP_CONF"
    exit $REC_CONFIG_FILE_NOT_EXIST
fi

sys_groupadd "oinstall" "300"
sys_groupadd "dba" "301"
sys_groupadd "oper" "302"
sys_groupadd "asmadmin" "303"
sys_groupadd "asmoper" "304"
sys_groupadd "asmdba" "305"

sys_useradd "oracle" "oinstall" "dba,asmdba,oper" "200"
sys_useradd "grid" "oinstall" "asmadmin,asmdba,asmoper,oper,dba" "201"

sys_limit "grid"
sys_limit "oracle"

if [ -f $PROFILE ]; then
    grep "oracle" $PROFILE >/dev/null 2>&1
    if [ $? != 0 ]; then
        echo "
        if [ \$USER = \"oracle\" ] || [ \$USER = \"grid\" ]; then
            if [ \$SHELL = \"/bin/ksh\" ]; then
                ulimit -p 16384
                ulimit -n 65536
            else
                ulimit -u 16384 -n 65536
            fi
        fi" >> $PROFILE
    fi
fi

INFO "Create base dir"

/bin/mkdir -p /u01/app/grid
/bin/chown -R grid:oinstall /u01/app/grid
/bin/chmod -R 775 /u01/app/grid
/bin/mkdir -p /u01/app/oraInventory/
/bin/chown -R grid:oinstall /u01/app/oraInventory/
/bin/chmod -R 775 /u01/app/oraInventory/
/bin/mkdir -p /u01/app/$ORACLE_RELEASE
/bin/chown -R grid:oinstall /u01/app/$ORACLE_RELEASE
/bin/chmod -R 775 /u01/app/$ORACLE_RELEASE
/bin/mkdir -p /u01/app/oracle
/bin/chown -R oracle:oinstall /u01/app/oracle
/bin/chmod -R 775 /u01/app/oracle

INFO "Config evn"

if [ -f "/root/.bash_profile" ]; then
    grep "grid" "/root/.bash_profile" >/dev/null
    if [ $? != 0 ]; then
        echo "export PATH=/u01/app/$ORACLE_RELEASE/grid/bin::\$PATH"  >> "/root/.bash_profile"
    fi
fi

if [ -f "/home/oracle/.bash_profile" ]; then
    grep "ORACLE" "/home/oracle/.bash_profile" >/dev/null
    if [ $? != 0 ]; then
        echo "
umask 022
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=\$ORACLE_BASE/product/$ORACLE_RELEASE
export ORACLE_SID=dbm$NODE_ID
export LD_LIBRARY_PATH=\$ORACLE_HOME/lib:/lib:/usr/lib:\$ORACLE_HOME/rdbms/lib
export PATH=\$ORACLE_HOME/bin:\$CRS_HOME/bin:/usr/bin:/usr/sbin:/usr/local/bin:\$PATH
export DISPLAY=$DP
        "  >> "/home/oracle/.bash_profile"
    fi
fi

if [ -f "/home/grid/.bash_profile" ]; then
    grep "ORACLE" "/home/grid/.bash_profile" >/dev/null
    if [ $? != 0 ]; then
        echo "
umask 022
export ORACLE_BASE=/u01/app/grid
export ORACLE_HOME=/u01/app/$ORACLE_RELEASE/grid
export ORACLE_SID=+ASM$NODE_ID
export LD_LIBRARY_PATH=\$ORACLE_HOME/lib:/lib:/usr/lib:\$ORACLE_HOME/rdbms/lib
export PATH=\$ORACLE_HOME/bin:/usr/bin:/usr/sbin:/usr/local/bin:\$PATH
export DISPLAY=$DP
        "  >> "/home/grid/.bash_profile"
    fi
fi

exit $REC_SUCCESS
