# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class HeartBeatSlotListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_SLOT_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_SLOT_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_slot_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        g.slot_list.Clear()

        # 将心跳上来的所有slot更新
        for slot_info in self.request_body.slot_infos:
            g.slot_list.slot_infos.add().CopyFrom(slot_info)
    
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
