# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import AsmOraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class ASMDiskAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.ASMDISK_ADD_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.ASMDISK_ADD_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.asmdisk_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        asmdisk_path = self.request_body.asmdisk_path
        diskgroup_name = self.request_body.diskgroup_name 
        rebalance_power = self.request_body.rebalance_power
        force = self.request_body.force
        failgroup = self.request_body.failgroup
        asmdisk_info = common.GetASMDiskInfoByPath(asmdisk_path)
        if not asmdisk_info:
            self.response.rc.retcode = msg_mds.RC_MDS_DEVICE_PATH_NOT_EXIST
            self.response.rc.message = "Path %s not found" % asmdisk_path
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
        ret, result = sql.add_asm_disk(diskgroup_name, asmdisk_path, force, failgroup)
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_ADD_FAILED
            self.response.rc.message = "ASMDisk add failed: %s" % result
            self.SendResponse(self.response)
            return MS_FINISH

        if rebalance_power:
            ret, result = sql.alter_asm_rebalance(diskgroup_name, rebalance_power)
            if ret:
                self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_REBALANCE_FAILED
                self.response.rc.message = "Alter diskgroup rebalance failed: %s" % result
                self.SendResponse(self.response)
                return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
