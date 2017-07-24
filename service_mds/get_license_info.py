# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetLicenseInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_LICENSE_INFO_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_LICENSE_INFO_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_license_info_request]

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        for k, v in g.license.items():
            kv = self.response.body.Extensions[msg_mds.get_license_info_response].kvs.add()
            kv.key   = str(k)
            kv.value = str(v)
        self.SendResponse(self.response)
        return MS_FINISH
