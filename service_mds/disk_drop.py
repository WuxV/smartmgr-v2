# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class DiskDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISK_DROP_REQUEST
    
    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.DISK_DROP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.disk_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 获取磁盘信息
        self.disk_info = common.GetDiskInfoByName(self.request_body.disk_name)
        if self.disk_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            self.response.rc.message = "Disk %s is not exist" % (self.request_body.disk_name)
            self.SendResponse(self.response)
            return MS_FINISH

        # 检查磁盘是否有被pool引用
        pool_infos = common.GetPoolInfoByDiskID(self.disk_info.header.uuid)
        if len(pool_infos) != 0:
            pool_list = ",".join([pool_info.pool_name for pool_info in pool_infos])
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_IS_USED_BY_POOL
            self.response.rc.message = "Disk %s is used by pool : %s" % (self.disk_info.disk_name, pool_list)
            self.SendResponse(self.response)
            return MS_FINISH

        # 检查磁盘是否有被lun引用
        lun_infos = common.GetLunInfoByDiskID(self.disk_info.header.uuid)
        if len(lun_infos) != 0:
            lun_list = ",".join([lun_info.lun_name for lun_info in lun_infos])
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_IS_USED_BY_LUN
            self.response.rc.message = "Disk %s is used by lun : %s" % (self.disk_info.disk_name, lun_list)
            self.SendResponse(self.response)
            return MS_FINISH

        e, _ = dbservice.srv.delete("/disk/%s" % self.disk_info.header.uuid)
        if e:
            logger.run.error("Delete disk info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
            self.response.rc.message = "Drop data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        disk_list = msg_mds.G_DiskList()
        for disk_info in filter(lambda disk_info:disk_info.header.uuid!=self.disk_info.header.uuid, g.disk_list.disk_infos):
            disk_list.disk_infos.add().CopyFrom(disk_info)
        g.disk_list = disk_list

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
