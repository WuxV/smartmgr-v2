#!/bin/bash

DEBUG_LEVEL=40
INFO_LEVEL=30
WARNING_LEVEL=20
ERROR_LEVEL=10
NULL_LEVEL=0

GET_LOG_LEVEL()
{
    if [ $# -ne 1 ]; then
        exit $REC_ERR_PARAM
    fi

    case "$1" in
        "DEBUG")
            return $DEBUG_LEVEL
            ;;
        "INFO")
            return $INFO_LEVEL
            ;;
        "WARNING")
            return $WARNING_LEVEL
            ;;
        "ERROR")
            return $ERROR_LEVEL
            ;;
        "NULL")
            return $NULL_LEVEL
            ;;
        *)
            return $DEBUG_LEVEL
            ;;
    esac
}

_save_log()
{
    case "$LOG_TYPE" in
        "FILE")
            echo [`date +"%Y-%m-%d %T"`] $@ >> $LOG_OUT
            ;;
        "STDOUT")
            echo [`date +"%Y-%m-%d %T"`] $@ 
            ;;
        "ALL")
            echo [`date +"%Y-%m-%d %T"`] $@ >> $LOG_OUT
            echo [`date +"%Y-%m-%d %T"`] $@ 
            ;;
        *)
            ;;
    esac
}

DEBUG()
{
    GET_LOG_LEVEL $LOG_LEVEL
    if [ $? -ge $DEBUG_LEVEL ];then
        _save_log "[DEBUG] $@"
    fi
}

INFO()
{
    GET_LOG_LEVEL $LOG_LEVEL
    if [ $? -ge $INFO_LEVEL ];then
        _save_log "[INFO] $@"
    fi
}

ERROR()
{
    GET_LOG_LEVEL $LOG_LEVEL
    if [ $? -ge $ERROR_LEVEL ];then
        _save_log "[ERROR] $@"
    fi
}

WARNING()
{
    GET_LOG_LEVEL $LOG_LEVEL
    if [ $? -ge $WARNING_LEVEL ];then
        _save_log "[WARNING] $@"
    fi
}
