#!/bin/bash

# SUCCESS
REC_SUCCESS=0

# ERROR
REC_FAIL=1                                  # 主程序返回失败
REC_EXIT_INSTALL=2                          # 退出安装

REC_CONFIG_FILE_NOT_EXIST=3                 # 配置文件不存在
REC_CONFIG_ITEM=4                           # 配置项错误

REC_ERR_FILE_NOT_EXIST=6                    # 配置文件不存在
REC_ERR_PARAM=9                             # 参数错误
REC_ERR_NODE_INIT=10                        # 节点初始化失败

REC_ERR_SSD_SAS_PAIR=28                     # 磁盘配对错误
REC_ERR_SSD_COUNT=29                        # SSD数量错误
REC_ERR_SAS_COUNT=30                        # SAS数量错误

REC_ERR_SAS_SIZE=31                         # SAS大小不符合要求
REC_ERR_SSD_SIZE=32                         # SSD大小不符合要求
REC_ERR_PARTED_COUNT=32                     # 分区数量不正确
REC_ERR_MAKE_FLASHCACHE=33                  # 创建flashcache失败
REC_ERR_FLASHCACHE_COUNT=34                 # 创建的flashcache数量错误
REC_ERR_PARTED=35                           # 分区错误
REC_ERR_LIST_FLASHCACHE=36                  # 获取flashcache失败
REC_ERR_DM_REMOVE=37                        # cache设备删除失败

REC_ERR_MAKE_RAID0=38                       # 做raid0失败
REC_ERR_INIT_SCST_CONFIG=39                 # 初始化scst的配置文件

REC_ERR_MISS_PKGS=40                        # 缺少软件包
REC_LV_NOT_EXIST=41                         # LV不存在
REC_NOT_SUPPORT_DISK_RULE=42                # 没有找到对应磁盘的rule

REC_DD_ACTION_ERROR=43                      # dd操作失败
REC_DIR_NOT_EXIST=44                        # 目录不存在

REC_SERVICE=45                              # 服务操作失败

REC_ERR_NODE_INIT=46                        # 节点初始化失败
REC_ERR_SET_NODE_ID=47                      # 设置节点ID失败
REC_ERR_SET_NODE_NAME=48                    # 设置hostname失败
REC_ERR_GET_DISK_GROUP=49                   # 获取磁盘分组失败
REC_ERR_SET_DOMAIN=50                       # 设置domain

REC_ERR_NETWORK_RESTART=51                  # 网络重启失败
REC_ERR_SSHD_RESTART=52                     # sshd重启失败
REC_ERR_PCSD_START=53                       # sshd启动失败
REC_ERR_PCSD_ENABLE=54                      # 设置pcsd开机自启失败
REC_ERR_PASSWD_HACLUSTER=55                 # 设置hacluster用户密码错误




