# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetDiskInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_DISK_INFO_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_DISK_INFO_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_disk_info_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        disk_info = None
        for _disk_info in g.disk_list.disk_infos:
            if _disk_info.disk_name == self.request_body.node_disk_name:
                disk_info = _disk_info
                break
        if disk_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            self.response.rc.message = "can't find disk %s" % self.request_body.node_disk_name
            self.SendResponse(self.response)
            return MS_FINISH
        
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
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
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
        self.response.body.Extensions[msg_mds.get_disk_info_response].disk_info.CopyFrom(disk_info)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
