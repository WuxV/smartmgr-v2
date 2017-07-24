#!/bin/bash
ROOT_DIR=$(cd `dirname $0` && pwd)"/../.."
source $ROOT_DIR/common/common.sh
LOAD_CONFIG $CONFIG_USER $CONFIG_SYS

DEBUG "EXE $0"

PROFILE="/etc/profile"
BASHRC="/etc/bashrc"

ORACLE="/etc/odbcinst.ini"

osv=`GET_OS_VERSION`

if [ "$osv" == "smartstore3" ];then
    smartmon_trapper="$ROOT_DIR/common/configure/smartstore3/smartmon-trapper.service"
    system_lib="/usr/lib/systemd/system/"
else
    smartmon_trapper="$ROOT_DIR/common/configure/smartstore2/smartmon-trapper"
    system_lib="/etc/init.d/"
fi

if [ "$osv" == "smartstore3" ];then
    if [ "$smartmon_trapper"x != ""x ];then
        if [ -f $system_lib/smartmon-trapper.service ];then
            rm -rf $system_lib/smartmon-trapper.service
        fi
        cp $smartmon_trapper $system_lib
       systemctl daemon-reload
    fi
else
    if [ "$smartmon_trapper"x != ""x ];then
        if [ -f $system_lib/smartmon-trapper ];then
            rm -rf $system_lib/smartmon-trapper
        fi
        cp $smartmon_trapper $system_lib
        chkconfig smartmon-trapper on
    fi
fi

if [ ! -e $BASHRC ]; then
    WARNING "Missing $BASHRC config"
    if [ ! -e $PROFILE ];then
        WARNING "Missing $PROFILE config"
    else
        echo "export PATH=$PATH:/usr/lib/oracle/12.1/client64/bin/" >> $PROFILE
        echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/oracle/12.1/client64/lib/" >> $PROFILE
    fi

else
    echo "export PATH=$PATH:/usr/lib/oracle/12.1/client64/bin/" >> $BASHRC
    echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/oracle/12.1/client64/lib/" >> $BASHRC
fi

if [ ! -e $ORACLE ];then
    WARNING "Missing $ORACLE config"
else
    echo "[Oracle]" >> $ORACLE
    echo "Description = ODBC for Oracle" >> $ORACLE
    echo "Driver = /usr/lib/oracle/12.1/client64/lib/libsqora.so.12.1" >> $ORACLE
    echo "Setup =" >> $ORACLE
    echo "FileUsage = 1" >> $ORACLE
fi

smartmgr restart
if [ "$osv" == "smartstore3" ];then
    systemctl restart smartmon-agent
    systemctl restart smartmon-trapper
else
    /etc/init.d/smartmon-agent restart
    /etc/init.d/smartmon-trapper restart
fi
