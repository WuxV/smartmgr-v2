# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class QosTemplateUpdateMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.QOS_TEMPLATE_UPDATE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.QOS_TEMPLATE_UPDATE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.qos_template_update_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.template_name = self.request_body.template_name
        template_info = common.GetQosTemplateInfoByName(self.template_name)

        if not template_info:
            self.response.rc.retcode = msg_mds.RC_MDS_QOS_TEMPLATE_NOT_EXIST
            self.response.rc.message = "QoS '%s' is not exist" % self.template_name
            self.SendResponse(self.response)
            return MS_FINISH

        self.template_info = msg_pds.QosTemplateInfo()
        self.template_info.CopyFrom(template_info)
        self.template_info.qos_info.read_bps = self.request_body.qos_info.read_bps or template_info.qos_info.read_bps
        self.template_info.qos_info.read_iops = self.request_body.qos_info.read_iops or template_info.qos_info.read_iops
        self.template_info.qos_info.write_bps = self.request_body.qos_info.write_bps or template_info.qos_info.write_bps
        self.template_info.qos_info.write_iops = self.request_body.qos_info.write_iops or template_info.qos_info.write_iops

        # 将QoS模板信息持久化
        data = pb2dict_proxy.pb2dict("template_info", self.template_info)
        e, _ = dbservice.srv.update("/qostemplate/%s" % self.template_info.template_id, data)
        if e:
            logger.run.error("Update template faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新内存
        template_info.CopyFrom(self.template_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
