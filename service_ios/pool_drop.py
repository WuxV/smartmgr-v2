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

class PoolDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.POOL_DROP_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_ios.POOL_DROP_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.pool_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        g.last_modify_time = int(time.time())

        pool_info = self.request_body.pool_info

        params = {}
        params['pool_name'] = pool_info.pool_name
        params['disk_id']   = pool_info.pool_disk_infos[0].disk_id
        params['disk_part'] = pool_info.pool_disk_infos[0].disk_part
        self.LongWork(self.drop_pool, params, self.Entry_PoolDrop)
        return MS_CONTINUE

    def drop_pool(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        pool_name = str(params['pool_name'])
        disk_id   = params['disk_id']
        disk_part = params['disk_part']

        # 删除pool
        e, res = apipal.Pool().del_pool(pool_name)
        if e and res.find("not added in PAL") == -1:
            rc.retcode = msg_ios.RC_IOS_PAL_POOL_DROP_FAILED
            rc.message = "pal pool drop failed:%s" % res
            return rc, ''

        time.sleep(1)

        # 从pal中删除磁盘
        part = common.GetPartInfo(disk_id, disk_part)
        if part != None:
            e, res = apipal.Disk().del_disk(part['DEVNAME'])
            if e and res.find("not added in PAL") == -1:
                logger.run.error("Drop pal disk failed,%s:%s:%s" % (part['DEVNAME'], e, res))
        return rc, ''

    def Entry_PoolDrop(self, result):
        rc, _ = result
        self.response.rc.CopyFrom(rc)
        self.SendResponse(self.response)
        return MS_FINISH
