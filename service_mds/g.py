# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from pdsframe import *
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

listen_ip   = config.safe_get('network', 'listen-ip')
listen_port = config.safe_get_int('network', 'listen-port')

# srbd的配置文件的路径
#srbd_conf = "../files/conf/test/service.mds.216.ini"
srbd_conf = "/opt/smartmgr/conf/service.mds.ini"

# license信息
license  = None

# 平台信息
platform = None

# 是否需要触发刷新标记
srp_rescan_flag = True

# 判断是否是smartmon节点
is_smartmon = False

# 记录集群中smartmon的ip和第二个存储备份文件的ip
smartmon_ip       = None
second_storage_ip = None
second_storage_ip_file = "/var/backup/second_ip"

# 备份文件的位置
bak_dir        = "/var/backup/file_bak"
second_bak_dir = "/var/backup/second_file_bak"

# 广播版本号
broadcast_version = 2

# IB卡信息
ibguids = None

# ios 服务信息
ios_service = msg_pds.NSNodeInfo()
ios_service.listen_ip   = config.safe_get('network', 'listen-ip')
ios_service.listen_port = config.safe_get_int('network', 'ios-listen-port')

node_uuid = config.safe_get("system","node_uuid")
node_info = msg_pds.NodeInfo()

# 服务状态
is_ready = False

# 磁盘列表(通过心跳全部上报的)
disk_list_all = msg_mds.G_DiskList()

# Raid磁盘列表(通过心跳全部上报的)
raid_disk_list_all = msg_mds.G_RaidDiskList()

# 磁盘列表(初始化化过的)
disk_list = msg_mds.G_DiskList()

# 存储池列表
pool_list = msg_mds.G_PoolList()

# lun列表
lun_list = msg_mds.G_LunList()

# SmartCache列表
smartcache_list = msg_mds.G_SmartCacheList()

# BaseDisk列表
basedisk_list = msg_mds.G_BaseDiskList()

# BaseDev列表
basedev_list = msg_mds.G_BaseDevList()

# palcache列表
palcache_list = msg_mds.G_PalCacheList()

# palraw列表
palraw_list = msg_mds.G_PalRawList()

# palpmt列表
palpmt_list = msg_mds.G_PalPmtList()

# 节点列表, 通过广播发现
nsnode_list = msg_mds.G_NSNodeList() 

# 已配置节点列表
nsnode_conf_list = msg_mds.G_NSNodeConfList() 

# 组列表
group_list = msg_mds.G_GroupConfList() 

# QoS模板列表
qos_template_list = msg_mds.G_QosTemplateList()

# 所有计算节点的asm disk列表,key是节点名称
all_asmdisk_list = {}

# asm disk列表
asmdisk_list = msg_mds.G_ASMDiskList()

# asm diskgroup列表
diskgroup_list = msg_mds.G_DiskgroupList()

# slot列表
slot_list = msg_mds.G_SlotList()
