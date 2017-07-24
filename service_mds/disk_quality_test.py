# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class DiskQualityTestMachine(BaseMachine):
    __metaclass__ = MataMachine
    
    MID = msg_mds.DISK_QUALITY_TEST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.DISK_QUALITY_TEST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.disk_quality_test_request]
        
        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if not self.request_body.force:
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_QUALITY_TEST_NO_FORCE
            self.response.rc.message = "IO quality test will affect the front-end business, use [-f] to start quality test!"
            self.SendResponse(self.response)
            return MS_FINISH

        ios_request = MakeRequest(msg_ios.DISK_QUALITY_TEST_REQUEST, self.request)
        for diskinfo in g.disk_list.disk_infos:
            ios_request.body.Extensions[msg_ios.disk_quality_test_request].disk_infos.add().CopyFrom(diskinfo) 

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, ios_request, self.Entry_DiskQualityTest)
        return MS_CONTINUE

    def Entry_DiskQualityTest(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.response.rc.message = "Success : disk quality test task has been accepted!" 
        self.SendResponse(self.response)
        return MS_FINISH
