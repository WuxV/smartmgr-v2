# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import AsmOraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class DiskgroupConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISKGROUP_CONFIG_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.DISKGROUP_CONFIG_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.diskgroup_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        diskgroup_name = self.request_body.diskgroup_name 
        rebalance_power = self.request_body.rebalance_power
        diskgroup_info = common.GetDiskgroupInfoByName(diskgroup_name)
        if not diskgroup_info:
            self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_NOT_EXIST
            self.response.rc.message = "Diskgroup %s not exist" % diskgroup_name
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
        ret, result = sql.alter_asm_rebalance(diskgroup_name, rebalance_power)
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_REBALANCE_FAILED
            self.response.rc.message = "Config diskgroup rebalance failed: %s" % result
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
