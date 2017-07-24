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

class PoolConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.POOL_CONFIG_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_ios.POOL_CONFIG_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.pool_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.HasField('dirty_thresh'):
            return self.SetDirtyThresh()
        if self.request_body.HasField('pool_cache_model'):
            return self.SetPoolCacheModel()
        if self.request_body.HasField('sync_level'):
            return self.SetPoolSyncLevel()

        assert(0)

    def SetPoolCacheModel(self):
        pool_name       = self.request_body.pool_info.pool_name
        is_stop_through = self.request_body.is_stop_through
        assert(self.request_body.pool_cache_model == msg_pds.POOL_CACHE_MODEL_WRITETHROUGH)

        e, res = apipal.Pool().wb2wt(pool_name, not is_stop_through)
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_CONFIG_FAILED
            self.response.rc.message = "set pool cache model failed:%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def SetDirtyThresh(self):
        g.last_modify_time = int(time.time())

        pool_name = self.request_body.pool_info.pool_name
        lower     = self.request_body.dirty_thresh.lower
        upper     = self.request_body.dirty_thresh.upper

        e, res = apipal.Pool().set_dirty_thresh(pool_name, lower, upper)
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_CONFIG_FAILED
            self.response.rc.message = "set pool dirty thresh failed:%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def SetPoolSyncLevel(self):
        g.last_modify_time = int(time.time())

        pool_name  = self.request_body.pool_info.pool_name
        sync_level = self.request_body.sync_level

        e, res = apipal.Pool().set_sync_level(pool_name, sync_level)
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_PAL_POOL_CONFIG_FAILED
            self.response.rc.message = "set pool dirty thresh failed:%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
