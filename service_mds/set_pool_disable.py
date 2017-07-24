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

class SetPoolDisableMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SET_POOL_DISABLE_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.SET_POOL_DISABLE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.set_pool_disable_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.pool_info = common.GetPoolInfoByName(self.request_body.pool_name)
        if self.pool_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_POOL_NOT_EXIST
            self.response.rc.message = "Pool %s not exist" % self.request_body.pool_name
            self.SendResponse(self.response)
            return MS_FINISH

        if self.pool_info.is_disable == True:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Pool %s already disabled" % self.request_body.pool_name
            self.SendResponse(self.response)
            return MS_FINISH

        # pool如果在线, 则不准许disable
        if self.pool_info.actual_state == True:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Not support set disable to a online pool"
            self.SendResponse(self.response)
            return MS_FINISH

        # 如果pool下有palcache是在线状态, 则不准许disable
        for palcache_info in g.palcache_list.palcache_infos:
            if palcache_info.pool_id == self.pool_info.pool_id and palcache_info.actual_state == True:
                self.response.rc.retcode = msg_mds.RC_MDS_INTERNAL_ERROR
                self.response.rc.message = "Not support set disable to this pool for exist available palcache"
                self.SendResponse(self.response)
                return MS_FINISH

        # 如果pool之前没有更新is_invalid字段, 需要先更新
        pool_info = msg_pds.PoolInfo()
        pool_info.CopyFrom(self.pool_info)

        if pool_info.is_invalid != True:
            pool_info.is_invalid = True
            data = pb2dict_proxy.pb2dict("pool_info", pool_info)
            e, _ = dbservice.srv.update("/pool/%s" % pool_info.pool_id, data)
            if e:
                logger.run.error("Update pool info faild %s:%s" % (e, _))
                self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
                self.response.rc.message = "Keep data failed"
                self.SendResponse(self.response)
                return MS_FINISH
            logger.run.info("Set pool %s to invalid" % self.request_body.pool_name)

        pool_info.is_disable = True
        self.pool_info.CopyFrom(pool_info)
        logger.run.info("Set pool %s to diable" % self.request_body.pool_name)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
