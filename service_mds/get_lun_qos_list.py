# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetLunQosListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_LUN_QOS_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_LUN_QOS_LIST_RESPONSE, request)
        self.request      = request

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for lun_info in g.lun_list.lun_infos:
            lun_qos_info = msg_pds.LunQoSInfo()
            lun_qos_info.lun_id = lun_info.lun_id
            if lun_info.qos_template_id:
                template_info = common.GetQosTemplateInfoById(lun_info.qos_template_id)
                lun_qos_info.qos_info.CopyFrom(template_info.qos_info)
            self.response.body.Extensions[msg_mds.get_lun_qos_list_response].lun_qos_infos.add().CopyFrom(lun_qos_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
