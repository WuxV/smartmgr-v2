# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios

class GetDiskQualityListMachine(BaseMachine):
    __metaclass__ = MataMachine
    
    MID = msg_mds.GET_DISK_QUALITY_LIST_REQUEST
    
    def INIT(self, request):
        self.response = MakeResponse(msg_mds.GET_DISK_QUALITY_LIST_RESPONSE, request)
        self.request  = request
        self.request_body = request.body.Extensions[msg_mds.get_disk_quality_list_request]
        
        if g.is_ready == False:
        	self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
        	self.response.rc.message = "MDS service is not ready"
        	self.SendResponse(self.response)
        	return MS_FINISH
        
        ios_request = MakeRequest(msg_ios.GET_DISK_QUALITY_LIST_REQUEST, self.request)
        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, ios_request, self.Entry_GetDiskQualityList)
        return MS_CONTINUE

    def Entry_GetDiskQualityList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
       
        for disk_quality in response.body.Extensions[msg_ios.get_disk_quality_list_response].disk_quality_infos:
            self.response.body.Extensions[msg_mds.get_disk_quality_list_response].disk_quality_infos.add().CopyFrom(disk_quality)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
