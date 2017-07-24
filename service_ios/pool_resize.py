# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
from service_ios import g
from service_ios import common
from service_ios.base.apidisk import APIDisk
from service_ios.base import apipal

class PoolResizeMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.POOL_RESIZE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_ios.POOL_RESIZE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_ios.pool_resize_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 首先检查pool的状态是否是正在迁移
        e, pool = apipal.Pool().get_by_name(self.request_body.pool_info.pool_name)
        if e:
            logger.run.error("Can't find pool by name:%s" % self.request_body.pool_info.pool_name)
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_RESIZE_FAILED
            self.response.rc.message = "pal pool resize failed:%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        if apipal.testBit(pool.state(), apipal.POOL_STATE_MIGRATING):
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_IS_MIGRATING
            self.response.rc.message = "pal pool is migrating, not support resize"
            self.SendResponse(self.response)
            return MS_FINISH

        e, res = apipal.Pool().resize_pool(self.request_body.pool_info.pool_name, self.request_body.size)
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_RESIZE_FAILED
            self.response.rc.message = "pal pool resize failed:%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
