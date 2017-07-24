# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetSlotListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_SLOT_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_SLOT_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_slot_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        d = []
        for l in range(len(g.slot_list.slot_infos)):
            d.append((l, g.slot_list.slot_infos[l].slot_id))
        d.sort(lambda x,y:cmp(x[1],y[1]))

        for item in d:
            slot_info = g.slot_list.slot_infos[item[0]]
            self.response.body.Extensions[msg_mds.get_slot_list_response].slot_infos.add().CopyFrom(slot_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
