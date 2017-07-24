# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class UnlinkQosTemplateMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.UNLINK_QOS_TEMPLATE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.UNLINK_QOS_TEMPLATE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.unlink_qos_template_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        items = self.request_body.lun_name.split("_")
        if len(items) != 2 or items[0] != g.node_info.node_name:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH
        self.lun_name = items[1]
    
        # 获取lun信息
        lun_info = common.GetLunInfoByName(self.lun_name)
        if lun_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        if lun_info.qos_template_id == "":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_LINKED
            self.response.rc.message = "Lun '%s' is not linked qos template" % self.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        self.lun_info = msg_pds.LunInfo()
        self.lun_info.CopyFrom(lun_info)

        self.lun_info.qos_template_id = ""
        self.lun_info.qos_template_name = ""
        # 将lun配置信息持久化
        data = pb2dict_proxy.pb2dict("lun_info",self.lun_info)
        e, _ = dbservice.srv.update("/lun/%s" % self.lun_info.lun_id, data)
        if e:
            logger.run.error("Update lun info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新lun列表
        lun_info.CopyFrom(self.lun_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
