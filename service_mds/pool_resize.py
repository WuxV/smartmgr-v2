# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, uuid
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class PoolResizeMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.POOL_RESIZE_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.POOL_RESIZE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.pool_resize_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        pool_name = self.request_body.pool_name
        self.pool_info = common.GetPoolInfoByName(pool_name)
        if self.pool_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_POOL_NOT_EXIST
            self.response.rc.message = "Pool %s not exist" % pool_name
            self.SendResponse(self.response)
            return MS_FINISH

        if self.pool_info.actual_state == False:
            self.response.rc.retcode = msg_mds.RC_MDS_POOL_NOT_AVAILABLE
            self.response.rc.message = "Pool %s is not available" % pool_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 检查指定的新容量，是否超出了目前所能扩容的最大容量
        max_size = self.pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].max_size
        pmt_size = 0
        for palpmt_info in filter(lambda palpmt_info:palpmt_info.pool_id == self.pool_info.pool_id, g.palpmt_list.palpmt_infos):
            pmt_size += palpmt_info.size
        max_size   = (max_size*512)>>30
        pmt_size   = (pmt_size*512)>>30
        max_resize = max_size-pmt_size
        if self.request_body.size > max_resize:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Pool '%s' max resize size is %sG" % (self.pool_info.pool_name, max_resize)
            self.SendResponse(self.response)
            return MS_FINISH

        self.ios_request = MakeRequest(msg_ios.POOL_RESIZE_REQUEST, self.request)
        self.ios_request.body.Extensions[msg_ios.pool_resize_request].pool_info.CopyFrom(self.pool_info)
        self.ios_request.body.Extensions[msg_ios.pool_resize_request].size = self.request_body.size

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_ResizePool)
        return MS_CONTINUE

    def Entry_ResizePool(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新pool的size
        self.pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].size = (self.request_body.size<<30)/512
        
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
