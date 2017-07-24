# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import AsmOraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class ASMDiskOnlineMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.ASMDISK_ONLINE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.ASMDISK_ONLINE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.asmdisk_online_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.asmdisk_name = ""
        if self.request_body.HasField('asmdisk_name'):
            self.asmdisk_name = self.request_body.asmdisk_name
            self.asmdisk_info = common.GetASMDiskInfoByName(self.asmdisk_name)
            if not self.asmdisk_info or self.asmdisk_name.startswith('_DROPPED'):
                self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_NOT_EXIST
                self.response.rc.message = "ASMDisk %s not exist" % self.asmdisk_name
                self.SendResponse(self.response)
                return MS_FINISH
            if self.asmdisk_info.mode_status == "ONLINE":
                self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_ALREADY_ONLINE
                self.response.rc.message = "ASMDisk %s is already online state" % self.asmdisk_name
                self.SendResponse(self.response)
                return MS_FINISH

            self.diskgroup_info = common.GetDiskgroupInfoByID(self.asmdisk_info.diskgroup_id)
            self.diskgroup_name = self.diskgroup_info.diskgroup_name
        elif self.request_body.HasField('diskgroup_name') and self.request_body.HasField('failgroup'):
            self.diskgroup_name = self.request_body.diskgroup_name
            self.diskgroup_info = common.GetDiskgroupInfoByName(self.diskgroup_name)
            if not self.diskgroup_info:
                self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_NOT_EXIST
                self.response.rc.message = "Diskgroup %s not exist" % self.diskgroup_name
                self.SendResponse(self.response)
                return MS_FINISH

            self.failgroup = self.request_body.failgroup.upper()
            failgroup_list = [asmdisk_info.failgroup for asmdisk_info in g.asmdisk_list.asmdisk_infos if asmdisk_info.diskgroup_id == self.diskgroup_info.diskgroup_id]
            if self.failgroup not in failgroup_list:
                self.response.rc.retcode = msg_mds.RC_MDS_FAILGROUP_NOT_IN_DISKGROUP
                self.response.rc.message = "Failgroup %s not in diskgroup %s" % (self.failgroup, self.diskgroup_name)
                self.SendResponse(self.response)
                return MS_FINISH
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Miss asmdisk/diskgroup/failgroup name"
            self.SendResponse(self.response)
            return MS_FINISH

        self.LongWork(self.online_asmdisk, {})

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def online_asmdisk(self, params={}):
        rc = msg_pds.ResponseCode()

        ret, dbs = asm.get_grid_env()
        if ret:
            logger.run.error("Parse oratab env failed: %s" %dbs)
            rc.retcode = msg_mds.RC_MDS_GET_GRID_ENV_FAILED
            return rc, None

        if dbs.has_key("grid_home"):
            grid_home = dbs["grid_home"]
        else:
            logger.run.error("Can not find Oracle grid home")
            rc.retcode = msg_mds.RC_MDS_GET_GRID_ENV_FAILED
            return rc, None

        sql = AsmOraSQLPlus(grid_home)
        if self.asmdisk_name:
            ret, result = sql.online_asm_disk(self.diskgroup_name, self.asmdisk_name)
        else:
            ret, result = sql.online_asm_disk(self.diskgroup_name, failgroup=self.failgroup)
        if ret:
            logger.run.error("ASMDisk online failed: %s" % result)
            rc.retcode = msg_mds.RC_MDS_ASMDISK_ONLINE_FAILED
            return rc, None

        logger.run.info("ASMDisk %s online success" % self.asmdisk_name)
        rc.retcode = msg_pds.RC_SUCCESS
        return rc, None
