# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetNodeInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_NODE_INFO_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_NODE_INFO_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_node_info_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.response.body.Extensions[msg_mds.get_node_info_response].node_info.CopyFrom(g.node_info)
        self.SendResponse(self.response)
        return MS_FINISH
