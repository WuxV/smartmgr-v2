# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetLunListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_LUN_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_LUN_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_lun_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.qos_name = ""
        if self.request_body.HasField("qos_name"):
            self.qos_name = self.request_body.qos_name
            self.qos_template_info = common.GetQosTemplateInfoByName(self.qos_name)
            if not self.qos_template_info:
                self.response.rc.retcode = msg_mds.RC_MDS_QOS_TEMPLATE_NOT_EXIST
                self.response.rc.message = "QoS '%s' is not exist" % self.qos_name
                self.SendResponse(self.response)
                return MS_FINISH
        
        self.group_name = ""
        if self.request_body.HasField("group_name"):
            self.group_name = self.request_body.group_name
            error,self.group_info = common.GetGroupInfoFromName(self.group_name)
            if error:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Not found group %s"% self.group_name
                self.SendResponse(self.response)
                return MS_FINISH


        for _lun_info in g.lun_list.lun_infos:
            # 过滤指定qos下的lun
            if self.qos_name and _lun_info.qos_template_name != self.qos_name:
                continue

            if self.group_name and self.group_name not in _lun_info.group_name:
                continue

            lun_info = msg_pds.LunInfo()
            lun_info.CopyFrom(_lun_info)

            for group in lun_info.group_info:
                error,index = common.GetIndexFromUUID(group.group_uuid)
                if not error:
                    lun_info.node_index.extend([index])
           
            if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                basedisk_info  = common.GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
                data_disk_info = common.GetDiskInfoByID(basedisk_info.disk_id)
                data_part_info = common.GetDiskPartByID(basedisk_info.disk_id, basedisk_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_size]           = data_part_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_scsiid]         = "xx"
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]      = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]  = data_part_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name] = "%sp%s" % (data_disk_info.disk_name, data_part_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state] = data_part_info.actual_state

            elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
                basedev_info  = common.GetBaseDevInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedev_id])
                lun_info.Extensions[msg_mds.ext_luninfo_size]           = basedev_info.size 
                lun_info.Extensions[msg_mds.ext_luninfo_scsiid]         = "xx"
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]      = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]  = basedev_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name] = ""

            elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
                smartcache_info  = common.GetSmartCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
                data_disk_info   = common.GetDiskInfoByID(smartcache_info.data_disk_id)
                data_part_info   = common.GetDiskPartByID(smartcache_info.data_disk_id, smartcache_info.data_disk_part)
                cache_disk_info  = common.GetDiskInfoByID(smartcache_info.cache_disk_id)
                cache_part_info  = common.GetDiskPartByID(smartcache_info.cache_disk_id, smartcache_info.cache_disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_size]            = data_part_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_cache_size]      = cache_part_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_scsiid]          = "xx"
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]       = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]   = data_part_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name]  = "%sp%s" % (data_disk_info.disk_name, data_part_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_cache_disk_name] = "%sp%s" % (cache_disk_info.disk_name, cache_part_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_cache_dev_name].append(cache_part_info.dev_name)
                lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state]  = data_part_info.actual_state
                lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state].append(cache_part_info.actual_state)

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                palcache_info  = common.GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
                data_disk_info = common.GetDiskInfoByID(palcache_info.disk_id)
                data_part_info = common.GetDiskPartByID(palcache_info.disk_id, palcache_info.disk_part)
                pool_info      = common.GetPoolInfoById(palcache_info.pool_id)
                pool_disk      = common.GetDiskInfoByID(pool_info.pool_disk_infos[0].disk_id)
                pool_part      = common.GetDiskPartByID(pool_info.pool_disk_infos[0].disk_id, pool_info.pool_disk_infos[0].disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_size]            = data_part_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_cache_size]      = pool_part.size
                lun_info.Extensions[msg_mds.ext_luninfo_scsiid]          = "xx"
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]       = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]   = data_part_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name]  = "%sp%s" % (data_disk_info.disk_name, data_part_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_cache_disk_name] = pool_info.pool_name
                lun_info.Extensions[msg_mds.ext_luninfo_cache_dev_name].append(pool_part.dev_name)
                if palcache_info.HasExtension(msg_mds.ext_palcache_export_info):
                    palcache_cache_model = palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model
                    lun_info.Extensions[msg_mds.ext_luninfo_palcache_cache_model] = palcache_cache_model
                lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state] = data_part_info.actual_state
                lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state].append(pool_part.actual_state)

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                palraw_info    = common.GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
                data_disk_info = common.GetDiskInfoByID(palraw_info.disk_id)
                data_part_info = common.GetDiskPartByID(palraw_info.disk_id, palraw_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_size]            = data_part_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_scsiid]          = "xx"
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]       = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]   = data_part_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name]  = "%sp%s" % (data_disk_info.disk_name, data_part_info.disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state] = data_part_info.actual_state

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
                palpmt_info    = common.GetPalPmtInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])
                pool_info      = common.GetPoolInfoById(palpmt_info.pool_id)
                data_part_info = common.GetDiskPartByID(pool_info.pool_disk_infos[0].disk_id, pool_info.pool_disk_infos[0].disk_part)
                lun_info.Extensions[msg_mds.ext_luninfo_size]           = palpmt_info.size
                lun_info.Extensions[msg_mds.ext_luninfo_node_name]      = g.node_info.node_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name] = pool_info.pool_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]  = data_part_info.dev_name
                lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state] = data_part_info.actual_state
            else:
                assert(0)
            self.response.body.Extensions[msg_mds.get_lun_list_response].lun_infos.add().CopyFrom(lun_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    
