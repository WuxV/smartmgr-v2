# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import AsmOraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class DiskgroupUmountMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISKGROUP_UMOUNT_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.DISKGROUP_UMOUNT_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.diskgroup_umount_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        diskgroup_name = self.request_body.diskgroup_name 
        diskgroup_info = common.GetDiskgroupInfoByName(diskgroup_name)
        if not diskgroup_info:
            self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_NOT_EXIST
            self.response.rc.message = "Diskgroup %s not exist" % diskgroup_name
            self.SendResponse(self.response)
            return MS_FINISH
        if diskgroup_info.state == "DISMOUNTED":
            self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_ALREADY_UMOUNTED
            self.response.rc.message = "Diskgroup %s is not mounted" % diskgroup_name
            self.SendResponse(self.response)
            return MS_FINISH

        ret, dbs = asm.get_grid_env()
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_GET_GRID_ENV_FAILED
            self.response.rc.message = "Parse oratab env failed: %s" %dbs
            self.SendResponse(self.response)
            return MS_FINISH

        if dbs.has_key("grid_home"):
            grid_home = dbs["grid_home"]
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_GET_GRID_ENV_FAILED
            self.response.rc.message = "Can not find Oracle grid home"
            self.SendResponse(self.response)
            return MS_FINISH

        sql = AsmOraSQLPlus(grid_home)
        ret, result = sql.umount_asm_group(diskgroup_name)
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_UMOUNT_FAILED
            self.response.rc.message = "Umount asm diskgroup failed: %s" % result
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
