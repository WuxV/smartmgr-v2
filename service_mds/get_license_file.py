# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetLicenseFileMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_LICENSE_FILE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_LICENSE_FILE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_license_file_request]

        e, license_base64 = License().get_license_file()
        if e!=0:
            logger.run.error("Get license file failed:%s" % license_base64)
            self.response.rc.retcode = msg_pds.RC_MDS_GET_LICENSE_FAILED
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.response.body.Extensions[msg_mds.get_license_file_response].license_base64 = license_base64
        self.SendResponse(self.response)
        return MS_FINISH
