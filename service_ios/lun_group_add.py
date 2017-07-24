# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import time, os
from pdsframe import *
from service_ios import g
from service_ios import common
import message.ios_pb2 as msg_ios
import message.pds_pb2 as msg_pds
from service_ios.base.apismartscsi import APISmartScsi

class LunGroupAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.LUN_GROUP_ADD_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_ios.LUN_GROUP_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.lun_group_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        node_uuid = self.request_body.node_uuid
        ibguids = self.request_body.ibguids

        apismartscsi = APISmartScsi()
        ret = apismartscsi.add_group(node_uuid,ibguids)
        if ret:
            logger.run.error("Add lun group failed:%s" % apismartscsi.errmsg)
            self.response.rc.retcode = msg_ios.RC_IOS_ADD_LUN_GROUP_FAILED
            self.response.rc.message = "Lun group add failed:%s" % apismartscsi.errmsg
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.response.rc.message = "add lun group sucsessful"
        self.SendResponse(self.response)
        return MS_FINISH


