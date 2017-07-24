# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class GetLunGroupListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_LUN_GROUP_LIST_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.GET_LUN_GROUP_LIST_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.get_lun_group_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        for node in g.nsnode_conf_list.nsnode_infos:
            self.response.body.Extensions[msg_mds.get_lun_group_list_response].nsnode_infos.add().CopyFrom(node)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH



