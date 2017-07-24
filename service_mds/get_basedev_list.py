# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetBaseDevListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_BASEDEV_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_BASEDEV_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_basedev_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for basedev_info in g.basedev_list.basedev_infos:
            self.response.body.Extensions[msg_mds.get_basedev_list_response].basedev_infos.add().CopyFrom(basedev_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
