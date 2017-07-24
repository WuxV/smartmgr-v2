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

class LunOnlineMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_ONLINE_REQUEST

    def INIT(self, request):
        self.default_timeout = 120
        self.response        = MakeResponse(msg_mds.LUN_ONLINE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_online_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        online_node = None
        if self.request_body.group_uuid:
            online_node = self.request_body.group_uuid

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

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        
        if self.lun_info.config_state and not online_node:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_ALREADY_ONLINE
            self.response.rc.message = "Lun %s already online state" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        if not online_node:
            group_uuid = []
            for group in self.lun_info.group_info:
                group_uuid.append(group.group_uuid)
            if group_uuid:
                self.ios_request_body.group_name.extend(group_uuid)
            else:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Lun %s not configure group" % (self.request_body.lun_name)
                self.SendResponse(self.response)
                return MS_FINISH
        else:
            info = self.lun_info.group_info.add()
            info.group_uuid = online_node
            info.group_state = 1
            self.ios_request_body.group_name.extend([online_node])

        g.srp_rescan_flag = True
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

    def Entry_OnlineLun(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        self.lun_info.config_state = True
        self.lun_info.actual_state = True
        self.lun_info.last_heartbeat_time = int(time.time())

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
