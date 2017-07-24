# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios

class GetDiskInfoMachine(BaseMachine):
    __metaclass__ = MataMachine
    
    MID = msg_mds.GET_DISK_QUALITY_INFO_REQUEST
    
    def INIT(self, request):
        self.response = MakeResponse(msg_mds.GET_DISK_QUALITY_INFO_RESPONSE, request)
        self.request  = request
        self.request_body = request.body.Extensions[msg_mds.get_disk_quality_info_request]

        if g.is_ready == False:
        	self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
        	self.response.rc.message = "MDS service is not ready"
        	self.SendResponse(self.response)
        	return MS_FINISH

        if not self.request_body.HasField('t_time'):
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_QUALITY_INFO_NO_TIME
            self.response.rc.message = "missing requires 'time' argument"
            self.SendResponse(self.response)
            return MS_FINISH

        self.t_time = self.request_body.t_time

        ios_request = MakeRequest(msg_ios.GET_DISK_QUALITY_INFO_REQUEST, self.request)
        ios_request.body.Extensions[msg_ios.get_disk_quality_info_request].t_time = self.t_time
        # 已初始化的磁盘列表
        for diskinfo in g.disk_list.disk_infos:
            ios_request.body.Extensions[msg_ios.get_disk_quality_info_request].disk_infos.add().CopyFrom(diskinfo)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, ios_request, self.Entry_GetDiskQualityInfo)
        return MS_CONTINUE

    def Entry_GetDiskQualityInfo(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
       
        disk_quality = response.body.Extensions[msg_ios.get_disk_quality_info_response].disk_quality_info
        self.response.body.Extensions[msg_mds.get_disk_quality_info_response].disk_quality_info.CopyFrom(disk_quality) 
        
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
