# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetPalRawListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_PALRAW_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_PALRAW_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_palraw_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for palraw_info in g.palraw_list.palraw_infos:
            self.response.body.Extensions[msg_mds.get_palraw_list_response].palraw_infos.add().CopyFrom(palraw_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
