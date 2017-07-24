# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class HeartBeatPoolListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_POOL_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_POOL_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_pool_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        pool_export_list = {}
        for pool_export_info in self.request_body.pool_export_infos:
            key = pool_export_info.pool_name
            pool_export_list[key] = pool_export_info

        for pool_info in g.pool_list.pool_infos:
            key = pool_info.pool_name
            if key in pool_export_list.keys():
                if pool_info.actual_state == False:
                    logger.run.info('[NODE STATE]: change pool %s actual state to True' % pool_info.pool_id)
                pool_info.actual_state        = True
                pool_info.last_heartbeat_time = int(time.time())
                pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].CopyFrom(pool_export_list[key])

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
