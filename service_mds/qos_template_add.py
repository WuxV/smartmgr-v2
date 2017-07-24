# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class QosTemplateAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.QOS_TEMPLATE_ADD_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.QOS_TEMPLATE_ADD_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.qos_template_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.template_name = self.request_body.template_name
        self.template_info = common.GetQosTemplateInfoByName(self.template_name)
        if self.template_info:
            self.response.rc.retcode = msg_mds.RC_MDS_QOS_TEMPLATE_ALREADY_ADDED
            self.response.rc.message = "QoS '%s' is already added" % self.template_name
            self.SendResponse(self.response)
            return MS_FINISH

        template_info = msg_pds.QosTemplateInfo()
        template_info.template_name = self.template_name
        template_info.template_id = str(uuid.uuid1())
        template_info.qos_info.read_bps = self.request_body.qos_info.read_bps
        template_info.qos_info.read_iops = self.request_body.qos_info.read_iops
        template_info.qos_info.write_bps = self.request_body.qos_info.write_bps
        template_info.qos_info.write_iops = self.request_body.qos_info.write_iops
        # 将QoS模板信息持久化
        data = pb2dict_proxy.pb2dict("template_info", template_info)
        e, _ = dbservice.srv.create("/qostemplate/%s" % template_info.template_id, data)
        if e:
            logger.run.error("Add template faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新QoS模板列表
        g.qos_template_list.qos_template_infos.add().CopyFrom(template_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
