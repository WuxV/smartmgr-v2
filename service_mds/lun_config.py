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

class LunConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_CONFIG_REQUEST

    def INIT(self, request):
        self.default_timeout = 120
        self.response        = MakeResponse(msg_mds.LUN_CONFIG_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 如果给组参数查询组
        if self.request_body.HasField("group_name"):
            error,group_info = common.GetGroupInfoFromName(self.request_body.group_name)
            if error:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Not found group %s"% self.request_body.group_name
                self.SendResponse(self.response)
                return MS_FINISH

            group_uuid = group_info.node_uuids
            if not group_uuid:
               self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
               self.response.rc.message = "Group %s not configure node"%self.request_body.group_name
               self.SendResponse(self.response)
               return MS_FINISH
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Not specify group name"
            self.SendResponse(self.response)
            return MS_FINISH

       
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

        if not self.request_body.del_group:
            if self.request_body.group_name in self.lun_info.group_name:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Group %s already config"%self.request_body.group_name
                self.SendResponse(self.response)
                return MS_FINISH
        else:
            if self.request_body.group_name not in self.lun_info.group_name:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Group %s not find in lun"%self.request_body.group_name
                self.SendResponse(self.response)
                return MS_FINISH

        exsist_groups=set()
        eqone_groups=set()
        if self.lun_info.group_info:
            for info in self.lun_info.group_info:
                exsist_groups.add(info.group_uuid)
                if info.group_state == 1:
                    eqone_groups.add(info.group_uuid)

        param_groups=set(group_uuid)
        self.add_groups = list(param_groups - exsist_groups) #独有的
        self.add_common_groups = list(param_groups & exsist_groups) #共有的
        self.del_groups = list(set(self.add_common_groups) & eqone_groups) #共有的且值为1
        self.del_common_groups = list(set(self.add_common_groups) - eqone_groups)#共有的且值不为1
        
        # 判断是添加配置还是删除配置
        if self.request_body.del_group:
            if not self.del_groups:
                self.response.rc.retcode = msg_pds.RC_SUCCESS
                return  self.Entry_OfflineLun(self.response,ios=False)
            return self.del_group(self.del_groups)
        else:
            if not self.add_groups:
                self.response.rc.retcode = msg_pds.RC_SUCCESS
                return  self.Entry_OnlineLun(self.response,ios=False)
            return self.add_group(self.add_groups)

    # 取消配置的组
    def del_group(self,group_uuid):
        g.srp_rescan_flag = True
        self.ios_request = MakeRequest(msg_ios.LUN_DROP_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_drop_request]
        if group_uuid:
            self.ios_request_body.group_name.extend(group_uuid)

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

        
    # 添加配置到组
    def add_group(self,group_uuid):
        g.srp_rescan_flag = True
        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        self.ios_request_body.group_name.extend(group_uuid)

        if self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            return self.OnlineLunBaseDisk()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            return self.OnlineLunSmartCache()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            return self.OnlineLunPalCache()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            return self.OnlineLunPalRaw()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            return self.OnlineLunPalPmt()
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            return self.OnlineLunBaseDev()
        else:
            assert(0)

    def OnlineLunSmartCache(self):
        smartcache_info = common.GetSmartCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].CopyFrom(smartcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def OnlineLunBaseDev(self):
        basedev_info = common.GetBaseDevInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedev_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedev].CopyFrom(basedev_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def OnlineLunBaseDisk(self):
        basedisk_info = common.GetBaseDiskInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk].CopyFrom(basedisk_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def OnlineLunPalCache(self):
        palcache_info = common.GetPalCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].CopyFrom(palcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def OnlineLunPalRaw(self):
        palraw_info = common.GetPalRawInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].CopyFrom(palraw_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def OnlineLunPalPmt(self):
        palpmt_info = common.GetPalPmtInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])

        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = True
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].CopyFrom(palpmt_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_OnlineLun)
        return MS_CONTINUE

    def Entry_OnlineLun(self, response,ios=True):
        if ios:
            if response.rc.retcode != msg_pds.RC_SUCCESS:
                self.response.rc.CopyFrom(response.rc)
                self.SendResponse(self.response)
                return MS_FINISH

        self.lun_info.config_state = True
        self.lun_info.actual_state = True
        self.lun_info.last_heartbeat_time = int(time.time())
        
        if self.add_groups:
            for k in self.add_groups:
                info = self.lun_info.group_info.add()
                info.group_uuid = k
                info.group_state = 1
        if self.add_common_groups:
            for info in self.lun_info.group_info:
                if info.group_uuid in self.add_common_groups:
                    info.group_state += 1
        self.lun_info.group_name.extend([self.request_body.group_name])

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

    def Entry_OfflineLun(self, response, ios=True):
        if ios:
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
        
        
        lun_info = msg_pds.LunInfo()
        lun_info.CopyFrom(self.lun_info)
        if self.del_groups:
            for info in lun_info.group_info:
                group = msg_pds.GroupInfo()
                if info.group_uuid in self.del_groups:
                    self.lun_info.group_info.remove(info)
        
        if self.del_common_groups:
            for info in self.lun_info.group_info:
                if info.group_uuid in self.del_common_groups:
                    info.group_state -= 1
        
        if not ios:
            if len(self.lun_info.group_info) == 0:
                self.lun_info.config_state = False
                self.lun_info.ClearExtension(msg_mds.ext_luninfo_lun_export_info)
            else:
                self.lun_info.config_state = True

        self.lun_info.group_name.remove(self.request_body.group_name)
           
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
