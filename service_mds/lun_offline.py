# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class LunOfflineMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_OFFLINE_REQUEST

    def INIT(self, request):
        self.default_timeout = 60
        self.response        = MakeResponse(msg_mds.LUN_OFFLINE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_offline_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        self.offline_node = None
        if self.request_body.group_uuid:
            self.offline_node = self.request_body.group_uuid
        
        items = self.request_body.lun_name.split("_")
        if len(items) != 2 or items[0] != g.node_info.node_name:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH
        lun_name = items[1]

        lun_info = common.GetLunInfoByName(lun_name)
        if lun_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun %s not exist" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        self.lun_info = msg_pds.LunInfo()
        self.lun_info.CopyFrom(lun_info)
        
        if not lun_info.config_state and not self.offline_node:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_ALREADY_OFFLINE
            self.response.rc.message = "Lun %s already offline state" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        # 如果是faulty状态，并且在asm中，则不能offline
        lun_faulty = self.check_lun_state_faulty(self.lun_info)
        if lun_faulty and lun_info.asm_status != "ONLINE":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_USED_IN_ASM
            self.response.rc.message = "Lun '%s' is used in asm" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        # 在offline之前 需要计算节点将磁盘offline掉
        self.database_node_list = [node_info for node_info in g.nsnode_list.nsnode_infos if node_info.sys_mode != "storage"]
        if lun_info.asm_status == "ACTIVE":
            self.mds_database_request = MakeRequest(msg_mds.ASMDISK_OFFLINE_REQUEST)
            asmdisk_info = common.GetASMDiskInfoByLunName(self.request_body.lun_name)
            self.mds_database_request.body.Extensions[msg_mds.asmdisk_offline_request].asmdisk_name = asmdisk_info.asmdisk_name

            # 先向第一个计算节点发送请求
            self.request_num = 1
            return self.send_asm_request()
        else:
            return self.Entry_LunOffline(None)

    def check_lun_state_faulty(self, lun_info):
        if lun_info.config_state == True and lun_info.actual_state == True:
            if lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].io_error != 0:
                return True

            if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                basedisk_info  = common.GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
                data_part_info = common.GetDiskPartByID(basedisk_info.disk_id, basedisk_info.disk_part)
                data_actual_state = data_part_info.actual_state

            elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
                data_actual_state = True

            elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
                smartcache_info  = common.GetSmartCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
                data_part_info   = common.GetDiskPartByID(smartcache_info.data_disk_id, smartcache_info.data_disk_part)
                cache_part_info  = common.GetDiskPartByID(smartcache_info.cache_disk_id, smartcache_info.cache_disk_part)
                data_actual_state = data_part_info.actual_state
                lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state].append(cache_part_info.actual_state)

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                palcache_info  = common.GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
                data_part_info = common.GetDiskPartByID(palcache_info.disk_id, palcache_info.disk_part)
                pool_info      = common.GetPoolInfoById(palcache_info.pool_id)
                pool_part      = common.GetDiskPartByID(pool_info.pool_disk_infos[0].disk_id, pool_info.pool_disk_infos[0].disk_part)
                data_actual_state = data_part_info.actual_state
                lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state].append(pool_part.actual_state)

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                palraw_info    = common.GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
                data_part_info = common.GetDiskPartByID(palraw_info.disk_id, palraw_info.disk_part)
                data_actual_state = data_part_info.actual_state

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
                palpmt_info    = common.GetPalPmtInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])
                pool_info      = common.GetPoolInfoById(palpmt_info.pool_id)
                data_part_info = common.GetDiskPartByID(pool_info.pool_disk_infos[0].disk_id, pool_info.pool_disk_infos[0].disk_part)
                data_actual_state = data_part_info.actual_state
            else:
                assert(0)
                
            if data_actual_state == False or False in lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state]:
                return True

        return False

    def send_asm_request(self):
        node_info = self.database_node_list[self.request_num-1]
        self.SendRequest(node_info.listen_ip, node_info.listen_port, self.mds_database_request, self.Entry_LunOffline)
        return MS_CONTINUE

    def Entry_LunOffline(self, response):
        if response and response.rc.retcode != msg_pds.RC_SUCCESS:
            # 向另外的计算节点发送请求，全部失败才返回
            if self.request_num < len(self.database_node_list):
                self.request_num += 1
                return self.send_asm_request()
            else:
                self.response.rc.CopyFrom(response.rc)
                self.SendResponse(self.response)
                return MS_FINISH

        g.srp_rescan_flag = True
        self.ios_request = MakeRequest(msg_ios.LUN_DROP_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_drop_request]
       
        if not self.offline_node:
            group_uuid = []
            for group in self.lun_info.group_info:
                    group_uuid.append(group.group_uuid)
            if group_uuid:
                self.ios_request_body.group_name.extend(group_uuid)
        else:
            for group in self.lun_info.group_info:
                if group.group_uuid == self.offline_node:
                    self.lun_info.group_info.remove(group)
            self.ios_request_body.group_name.extend([self.offline_node])

        if self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            return self.OfflineLunBaseDisk()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            return self.OfflineLunSmartCache()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            return self.OfflineLunPalCache()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            return self.OfflineLunPalRaw()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            return self.OfflineLunPalPmt()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            return self.OfflineLunBaseDev()
        else:
            assert(0)

    def OfflineLunSmartCache(self):
        smartcache_info = common.GetSmartCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].CopyFrom(smartcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def OfflineLunBaseDev(self):
        basedev_info = common.GetBaseDevInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedev_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedev].CopyFrom(basedev_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def OfflineLunBaseDisk(self):
        basedisk_info = common.GetBaseDiskInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedisk].CopyFrom(basedisk_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def OfflineLunPalCache(self):
        palcache_info = common.GetPalCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palcache].CopyFrom(palcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def OfflineLunPalRaw(self):
        palraw_info = common.GetPalRawInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palraw].CopyFrom(palraw_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def OfflineLunPalPmt(self):
        palpmt_info = common.GetPalPmtInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palpmt].CopyFrom(palpmt_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OfflineLun)
        return MS_CONTINUE

    def Entry_OfflineLun(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        num = int(response.body.Extensions[msg_ios.lun_drop_response].exist_lun)
        logger.run.info("After do action offline lun export num [%s]"%num)
        if num:
            self.lun_info.config_state = True
        else:
            self.lun_info.config_state = False
            self.lun_info.ClearExtension(msg_mds.ext_luninfo_lun_export_info)
       
        data = pb2dict_proxy.pb2dict("lun_info", self.lun_info)
        e, _ = dbservice.srv.update("/lun/%s" % self.lun_info.lun_id, data)
        if e:
            logger.run.error("Update lun info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        lun_info = common.GetLunInfoByName(self.lun_info.lun_name)
        lun_info.CopyFrom(self.lun_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
