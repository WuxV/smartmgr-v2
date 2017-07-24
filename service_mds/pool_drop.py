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

class PoolDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.POOL_DROP_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.POOL_DROP_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.pool_drop_request]

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

        # 检查pool是否有被lun引用
        lun_infos = common.GetLunInfoByPoolID(self.pool_info.pool_id)
        if len(lun_infos) != 0:
            lun_list = ",".join([lun_info.lun_name for lun_info in lun_infos])
            self.response.rc.retcode = msg_mds.RC_MDS_POOL_IS_USED_BY_LUN
            self.response.rc.message = "Pool %s is used by lun : %s" % (self.pool_info.pool_name, lun_list)
            self.SendResponse(self.response)
            return MS_FINISH

        self.ios_request = MakeRequest(msg_ios.POOL_DROP_REQUEST, self.request)
        self.ios_request.body.Extensions[msg_ios.pool_drop_request].pool_info.CopyFrom(self.pool_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_DropPool)
        return MS_CONTINUE

    def Entry_DropPool(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        e, _ = dbservice.srv.delete("/pool/%s" % self.pool_info.pool_id)
        if e:
            logger.run.error("Delete pool info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
            self.response.rc.message = "Drop data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        pool_list = msg_mds.G_PoolList()
        for pool_info in filter(lambda pool_info:pool_info.pool_id!=self.pool_info.pool_id,g.pool_list.pool_infos):
            pool_list.pool_infos.add().CopyFrom(pool_info)
        g.pool_list = pool_list

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
