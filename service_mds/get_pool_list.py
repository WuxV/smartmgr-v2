# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetPoolListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_POOL_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_POOL_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_pool_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for _pool_info in g.pool_list.pool_infos:
            pool_info = msg_pds.PoolInfo()
            pool_info.CopyFrom(_pool_info)

            # 补充磁盘的实时信息
            for pool_disk_info in pool_info.pool_disk_infos:
                disk_info = common.GetDiskInfoByID(pool_disk_info.disk_id)
                diskpart  = common.GetDiskPartByID(pool_disk_info.disk_id, pool_disk_info.disk_part)
                pool_disk_info.Extensions[msg_mds.ext_pool_disk_info_dev_name]  = diskpart.dev_name
                pool_disk_info.Extensions[msg_mds.ext_pool_disk_info_disk_name] = "%sp%s" % (disk_info.disk_name, pool_disk_info.disk_part)
                pool_disk_info.Extensions[msg_mds.ext_pool_disk_info_size]      = diskpart.size

            # 补充pool cache mode
            count = {'wb':0, 'wt':0, 'un':0}
            for palcache_info in g.palcache_list.palcache_infos:
                if palcache_info.pool_id != pool_info.pool_id:
                    continue
                if not palcache_info.HasExtension(msg_mds.ext_palcache_export_info):
                    continue
                if palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model==msg_pds.PALCACHE_CACHE_MODEL_UNKNOWN:
                    count['un'] += 1
                if palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model==msg_pds.PALCACHE_CACHE_MODEL_WRITEBACK:
                    count['wb'] += 1
                if palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model==msg_pds.PALCACHE_CACHE_MODEL_WRITETHROUGH:
                    count['wt'] += 1
            if count['wb'] == 0 and count['wt'] != 0:
                pool_info.Extensions[msg_mds.ext_poolinfo_pool_cache_model] = msg_pds.POOL_CACHE_MODEL_WRITETHROUGH
            elif count['wb'] != 0 and count['wt'] == 0:
                pool_info.Extensions[msg_mds.ext_poolinfo_pool_cache_model] = msg_pds.POOL_CACHE_MODEL_WRITEBACK
            elif count['wb'] != 0 and count['wt'] != 0:
                pool_info.Extensions[msg_mds.ext_poolinfo_pool_cache_model] = msg_pds.POOL_CACHE_MODEL_MIX

            # 补充使用该pool的lun的总容量
            pmt_size = 0
            for palpmt_info in g.palpmt_list.palpmt_infos:
                if palpmt_info.pool_id == pool_info.pool_id:
                    pmt_size += palpmt_info.size
            pool_info.Extensions[msg_mds.ext_poolinfo_pool_pmt_size] = pmt_size

            self.response.body.Extensions[msg_mds.get_pool_list_response].pool_infos.add().CopyFrom(pool_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
