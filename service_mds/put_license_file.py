# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class PutLicenseFileMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.PUT_LICENSE_FILE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.PUT_LICENSE_FILE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.put_license_file_request]

        e, res = License().put_license_file(self.request_body.license_base64)
        if e!=0:
            logger.run.error("Put license file failed:%s" % res)
            self.response.rc.retcode = msg_mds.RC_MDS_PUT_LICENSE_FAILED
            self.SendResponse(self.response)
            return MS_FINISH

        g.license = common.load_license()
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
