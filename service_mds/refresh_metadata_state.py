# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

# 磁盘状态超时
DISK_STATE_TIME_OUT = 15
# LUN状态超时
LUN_STATE_TIME_OUT  = 15
# POOL状态超时
POOL_STATE_TIME_OUT  = 15
# PALCACHE状态超时
PALCACHE_STATE_TIME_OUT  = 15
# PALRAW状态超时
PALRAW_STATE_TIME_OUT  = 15
# PALPMT状态超时
PALPMT_STATE_TIME_OUT  = 15
# 全量磁盘超时
TMP_DISK_STATE_TIME_OUT = 15
# 全量raid超时
TMP_RAIDDISK_STATE_TIME_OUT = 15

class RefreshMetadataMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME  = 3
    START_TIME = 0

    def INIT(self):
        # 服务刚起来的时候, 不进行资源状态刷新, 解决服务刚起来的时候, 还没有接收到首次心跳
        if RefreshMetadataMachine.START_TIME < 10:
            RefreshMetadataMachine.START_TIME += RefreshMetadataMachine.LOOP_TIME
            return MS_FINISH

        if g.is_ready == False:
            return MS_FINISH

        now_time = int(time.time())

        # 刷新磁盘状态
        for disk_info in g.disk_list.disk_infos:
            if now_time - disk_info.last_heartbeat_time > DISK_STATE_TIME_OUT:
                if disk_info.actual_state == True:
                    logger.run.warning('[DISK STATE]: change disk :%s actual state to False' % disk_info.header.uuid)
                disk_info.actual_state = False
                disk_info.dev_name     = ""
                disk_info.ClearField("raid_disk_info")
            # 刷新分区状态
            for diskpart in disk_info.diskparts:
                if now_time - diskpart.last_heartbeat_time > DISK_STATE_TIME_OUT:
                    if diskpart.actual_state == True:
                        logger.run.warning('[PART STATE]: change part %s:%s actual state to False' % (disk_info.header.uuid, diskpart.disk_part))
                    diskpart.actual_state = False
                    diskpart.dev_name    = ""

        # 刷新Lun状态
        for lun_info in g.lun_list.lun_infos:
            if now_time - lun_info.last_heartbeat_time > LUN_STATE_TIME_OUT:
                if lun_info.actual_state == True:
                    logger.run.warning('[LUN STATE]: change lun :%s actual state to False' % lun_info.lun_id)
                lun_info.actual_state = False
                lun_info.ClearExtension(msg_mds.ext_luninfo_lun_export_info)

        # 刷新Pool状态
        for pool_info in g.pool_list.pool_infos:
            if now_time - pool_info.last_heartbeat_time > POOL_STATE_TIME_OUT:
                if pool_info.actual_state == True:
                    logger.run.warning('[POOL STATE]: change pool :%s actual state to False' % pool_info.pool_id)
                pool_info.actual_state = False
                pool_info.ClearExtension(msg_mds.ext_poolinfo_pool_export_info)

        # 刷新PalCache状态
        for palcache_info in g.palcache_list.palcache_infos:
            if now_time - palcache_info.last_heartbeat_time > PALCACHE_STATE_TIME_OUT:
                if palcache_info.actual_state == True:
                    logger.run.warning('[PALCACHE STATE]: change palcache :%s actual state to False' % palcache_info.palcache_id)
                palcache_info.actual_state = False
                palcache_info.ClearExtension(msg_mds.ext_palcache_export_info)

        # 刷新PalRaw状态
        for palraw_info in g.palraw_list.palraw_infos:
            if now_time - palraw_info.last_heartbeat_time > PALRAW_STATE_TIME_OUT:
                if palraw_info.actual_state == True:
                    logger.run.warning('[PALRAW STATE]: change palraw :%s actual state to False' % palraw_info.palraw_id)
                palraw_info.actual_state = False
                palraw_info.ClearExtension(msg_mds.ext_palraw_export_info)

        # 刷新PalPmt状态
        for palpmt_info in g.palpmt_list.palpmt_infos:
            if now_time - palpmt_info.last_heartbeat_time > PALPMT_STATE_TIME_OUT:
                if palpmt_info.actual_state == True:
                    logger.run.warning('[PALPMT STATE]: change palpmt :%s actual state to False' % palpmt_info.palpmt_id)
                palpmt_info.actual_state = False
                palpmt_info.ClearExtension(msg_mds.ext_palpmt_export_info)

        # 剔除全量磁盘列表中超时的磁盘
        disk_list_all = msg_mds.G_DiskList()
        for disk_info in filter(lambda disk_info:now_time - disk_info.last_heartbeat_time <= TMP_DISK_STATE_TIME_OUT, g.disk_list_all.disk_infos):
            disk_list_all.disk_infos.add().CopyFrom(disk_info)
        g.disk_list_all = disk_list_all

        # 剔除全量raid列表中超时的raid盘
        raid_disk_list_all = msg_mds.G_RaidDiskList()
        for raid_disk_info in g.raid_disk_list_all.raid_disk_infos:
            if now_time - raid_disk_info.last_heartbeat_time > TMP_RAIDDISK_STATE_TIME_OUT:
                continue
            raid_disk_list_all.raid_disk_infos.add().CopyFrom(raid_disk_info)
        g.raid_disk_list_all = raid_disk_list_all

        return MS_FINISH
