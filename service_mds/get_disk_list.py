# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_DISK_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_DISK_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_disk_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 初始化过的盘
        inited_disk = {'dev_name':[], 'ces_addr':[]}
        for _disk_info in g.disk_list.disk_infos:
            disk_info = msg_pds.DiskInfo()
            disk_info.CopyFrom(_disk_info)

            # 补充磁盘的剩余空间
            free_size = disk_info.size
            for diskpart in disk_info.diskparts:
                # 减去被lun使用的空间
                lun_info = common.GetLunInfoByDiskPart(disk_info.header.uuid, diskpart.disk_part)
                if lun_info != None:
                    free_size -= diskpart.size
                # 减去被pool使用的空间
                pool_info = common.GetPoolInfoByDiskPart(disk_info.header.uuid, diskpart.disk_part)
                if pool_info != None:
                    free_size -= diskpart.size
            disk_info.Extensions[msg_mds.ext_diskinfo_free_size] = free_size

            # 补充使用该盘的lun列表
            lun_infos = common.GetLunInfoByDiskID(disk_info.header.uuid)
            for lun_info in lun_infos:
                kv = msg_pds.SimpleKV()
                kv.value = lun_info.lun_name
                if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                    basedisk_info = common.GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
                    kv.key   = "%s.%s" % (basedisk_info.disk_id, basedisk_info.disk_part)
                    disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name].add().CopyFrom(kv)
                elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                    palcache_info = common.GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
                    kv.key   = "%s.%s" % (palcache_info.disk_id, palcache_info.disk_part)
                    disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name].add().CopyFrom(kv)
                elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                    palraw_info = common.GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
                    kv.key   = "%s.%s" % (palraw_info.disk_id, palraw_info.disk_part)
                    disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name].add().CopyFrom(kv)
                elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
                    smartcache_info = common.GetSmartCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
                    if smartcache_info.data_disk_id == disk_info.header.uuid:
                        kv.key   = "%s.%s" % (smartcache_info.data_disk_id, smartcache_info.data_disk_part)
                        disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name].add().CopyFrom(kv)
                    if smartcache_info.cache_disk_id == disk_info.header.uuid:
                        kv.key   = "%s.%s" % (smartcache_info.cache_disk_id, smartcache_info.cache_disk_part)
                        disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name_smartcache].add().CopyFrom(kv)
                elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
                    pass
                else:
                    assert(0)

            # 补充使用该盘的pool列表
            pool_infos = common.GetPoolInfoByDiskID(disk_info.header.uuid)
            for pool_info in pool_infos:
                for pool_disk_info in pool_info.pool_disk_infos:
                    if pool_disk_info.disk_id == disk_info.header.uuid:
                        kv = msg_pds.SimpleKV()
                        kv.value = pool_info.pool_name
                        kv.key   = "%s.%s" % (pool_disk_info.disk_id, pool_disk_info.disk_part)
                        disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_pool_name].add().CopyFrom(kv)

            self.response.body.Extensions[msg_mds.get_disk_list_response].disk_infos.add().CopyFrom(disk_info)
            inited_disk['dev_name'].append(disk_info.dev_name)
            if disk_info.HasField('raid_disk_info'):
                ces_addr = "%s:%s:%s" % (disk_info.raid_disk_info.ctl, disk_info.raid_disk_info.eid, disk_info.raid_disk_info.slot)
                inited_disk['ces_addr'].append(ces_addr)

        # 补充没有初始化过的盘
        for _disk_info in g.disk_list_all.disk_infos:
            disk_info = msg_pds.DiskInfo()
            disk_info.CopyFrom(_disk_info)
            if disk_info.dev_name in inited_disk['dev_name']:
                continue
            disk_info.Extensions[msg_mds.ext_diskinfo_free_size] = disk_info.size
            self.response.body.Extensions[msg_mds.get_disk_list_response].disk_infos.add().CopyFrom(disk_info)

        # 补充没有盘符的raid卡盘
        for _raid_disk_info in g.raid_disk_list_all.raid_disk_infos:
            raid_disk_info = msg_pds.RaidDiskInfo()
            raid_disk_info.CopyFrom(_raid_disk_info)
            if raid_disk_info.HasField('dev_name') and raid_disk_info.dev_name != "":
                continue
            ces_addr = "%s:%s:%s" % (raid_disk_info.ctl, raid_disk_info.eid, raid_disk_info.slot)
            if ces_addr in inited_disk['ces_addr']:
                continue
            self.response.body.Extensions[msg_mds.get_disk_list_response].raid_disk_infos.add().CopyFrom(raid_disk_info)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
