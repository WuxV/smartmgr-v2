# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from pdsframe import *
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios

# 平台信息
platform = None

# 服务状态
is_ready = False

# 最后更新时间
last_modify_time = 0

# 需要进行健康检查的磁盘列表
todo_check_disk = []

# 健康检查的磁盘列表结果
cache_disk_list_healthy = {}

# mds 服务信息
mds_service = msg_pds.NSNodeInfo()
mds_service.listen_ip   = config.safe_get('network', 'listen-ip')
mds_service.listen_port = config.safe_get_int('network', 'mds-listen-port')
