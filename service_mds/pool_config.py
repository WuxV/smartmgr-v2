# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class PoolConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.POOL_CONFIG_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.POOL_CONFIG_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.pool_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if not self.request_body.HasField('dirty_thresh') and not self.request_body.HasField('pool_cache_model') \
                and not self.request_body.HasField('sync_level') and not self.request_body.HasField('skip_thresh'):
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Miss config pool dirty thresh value or pool cache model or sync level or skip thresh"
            self.SendResponse(self.response)
            return MS_FINISH

        if (self.request_body.HasField('dirty_thresh') and self.request_body.HasField('pool_cache_model')) or \
                (self.request_body.HasField('dirty_thresh') and self.request_body.HasField('sync_level')) or \
                (self.request_body.HasField('pool_cache_model') and self.request_body.HasField('sync_level')):
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Not supported setting model and dirty and level at the same time"
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

        self.ios_request = MakeRequest(msg_ios.POOL_CONFIG_REQUEST, self.request)
        self.ios_request.body.Extensions[msg_ios.pool_config_request].pool_info.CopyFrom(self.pool_info)

        # dirty
        if self.request_body.HasField('dirty_thresh'):
            if self.request_body.dirty_thresh.lower > self.request_body.dirty_thresh.upper or \
                    self.request_body.dirty_thresh.lower > 100 or self.request_body.dirty_thresh.upper > 100:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Pool dirty thresh upper or lower value illegal"
                self.SendResponse(self.response)
                return MS_FINISH
            self.ios_request.body.Extensions[msg_ios.pool_config_request].dirty_thresh.CopyFrom(self.request_body.dirty_thresh)
            self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_ConfigPoolDirtyThresh)

        # model
        if self.request_body.HasField('pool_cache_model'):
            self.ios_request.body.Extensions[msg_ios.pool_config_request].pool_cache_model = self.request_body.pool_cache_model
            self.ios_request.body.Extensions[msg_ios.pool_config_request].is_stop_through  = self.request_body.is_stop_through
            self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_ConfigPoolCacheModel)

        # sync level
        if self.request_body.HasField('sync_level'):
            self.ios_request.body.Extensions[msg_ios.pool_config_request].sync_level = self.request_body.sync_level
            self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_ConfigPoolSyncLevel)

        # skip thresh
        if self.request_body.HasField('skip_thresh'):
            if self.request_body.skip_thresh > 1024:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Pool skip thresh support 0-1024"
                self.SendResponse(self.response)
                return MS_FINISH
            min_value = self.pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].sippet
            min_value = (min_value*512)>>10
            if self.request_body.skip_thresh != 0 and self.request_body.skip_thresh < min_value:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Pool '%s' min skip thresh is %sk" % (self.pool_info.pool_name, min_value)
                self.SendResponse(self.response)
                return MS_FINISH
            return self.Entry_ConfigPoolSkipThresh(self.request_body.skip_thresh)
        return MS_CONTINUE

    def Entry_ConfigPoolDirtyThresh(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        pool_info = msg_pds.PoolInfo()
        pool_info.CopyFrom(self.pool_info)
        pool_info.dirty_thresh.CopyFrom(self.request_body.dirty_thresh)

        data = pb2dict_proxy.pb2dict("pool_info", pool_info)
        e, _ = dbservice.srv.update("/pool/%s" % pool_info.pool_id, data)
        if e:
            logger.run.error("Update pool info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        self.pool_info.CopyFrom(pool_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def Entry_ConfigPoolSyncLevel(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        pool_info = msg_pds.PoolInfo()
        pool_info.CopyFrom(self.pool_info)
        pool_info.sync_level = self.request_body.sync_level

        data = pb2dict_proxy.pb2dict("pool_info", pool_info)
        e, _ = dbservice.srv.update("/pool/%s" % pool_info.pool_id, data)
        if e:
            logger.run.error("Update pool info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        self.pool_info.CopyFrom(pool_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def Entry_ConfigPoolCacheModel(self, response):
        self.response.rc.CopyFrom(response.rc)
        self.SendResponse(self.response)
        return MS_FINISH

    def Entry_ConfigPoolSkipThresh(self, skip_thresh):
        pool_info = msg_pds.PoolInfo()
        pool_info.CopyFrom(self.pool_info)
        pool_info.skip_thresh = self.request_body.skip_thresh

        data = pb2dict_proxy.pb2dict("pool_info", pool_info)
        e, _ = dbservice.srv.update("/pool/%s" % pool_info.pool_id, data)
        if e:
            logger.run.error("Update pool info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        self.pool_info.CopyFrom(pool_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
