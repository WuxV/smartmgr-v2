# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetQosTemplateListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_QOS_TEMPLATE_LIST_REQUEST

    def INIT(self, request):
        self.response = MakeResponse(msg_mds.GET_QOS_TEMPLATE_LIST_RESPONSE, request)
        self.request  = request

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for _template_info in g.qos_template_list.qos_template_infos:
            self.response.body.Extensions[msg_mds.get_qos_template_list_response].qos_template_infos.add().CopyFrom(_template_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
