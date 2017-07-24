#!/bin/bash

DIR_ROOT=$(cd `dirname $0` && pwd)

source $DIR_ROOT/../../common/base_function.sh
source $DIR_ROOT/../../common/log_function.sh
source $DIR_ROOT/../../common/ret_code.sh

CONFIG_USER=$DIR_ROOT/../../conf/config_user
CONFIG_SYS=$DIR_ROOT/../../conf/config_sys
