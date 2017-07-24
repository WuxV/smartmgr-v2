# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class QosTemplateDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.QOS_TEMPLATE_DROP_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.QOS_TEMPLATE_DROP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.qos_template_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.template_name = self.request_body.template_name
        self.template_info = common.GetQosTemplateInfoByName(self.template_name)

        if not self.template_info:
            self.response.rc.retcode = msg_mds.RC_MDS_QOS_TEMPLATE_NOT_EXIST
            self.response.rc.message = "QoS '%s' is not exist" % self.template_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 如有lun关联，则返回
        for lun_info in g.lun_list.lun_infos:
            if lun_info.qos_template_id == self.template_info.template_id:
                self.response.rc.retcode = msg_mds.RC_MDS_LUN_ALEADY_LINKED_TEMPLATE
                self.response.rc.message = "QoS template '%s' was linked with lun" % self.template_name
                self.SendResponse(self.response)
                return MS_FINISH

        # 删除该模板
        e, _ = dbservice.srv.delete("/qostemplate/%s" % self.template_info.template_id)
        if e:
            logger.run.error("Delete template info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_DELETE_QOS_TEMPLATE_FAILED
            self.response.rc.message = "Drop template '%s' failed" % self.template_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 从内存中删除该QoS模板
        template_list = msg_mds.G_QosTemplateList()
        for template_info in filter(lambda template_info:template_info.template_name!=self.template_name,g.qos_template_list.qos_template_infos):
            template_list.qos_template_infos.add().CopyFrom(template_info)
        g.qos_template_list = template_list

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
