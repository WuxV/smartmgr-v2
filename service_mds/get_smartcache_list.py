# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetSmartCacheListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_SMARTCACHE_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_SMARTCACHE_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_smartcache_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        for smartcache_info in g.smartcache_list.smartcache_infos:
            self.response.body.Extensions[msg_mds.get_smartcache_list_response].smartcache_infos.add().CopyFrom(smartcache_info)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
