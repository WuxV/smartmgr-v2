# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import AsmOraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class ASMDiskOfflineMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.ASMDISK_OFFLINE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.ASMDISK_OFFLINE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.asmdisk_offline_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        asmdisk_name = ""
        if self.request_body.HasField('asmdisk_name'):
            asmdisk_name = self.request_body.asmdisk_name
            asmdisk_info = common.GetASMDiskInfoByName(asmdisk_name)
            if not asmdisk_info:
                self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_NOT_EXIST
                self.response.rc.message = "ASMDisk %s not exist" % asmdisk_name
                self.SendResponse(self.response)
                return MS_FINISH
            if asmdisk_info.mode_status == "OFFLINE":
                self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_ALREADY_OFFLINE
                self.response.rc.message = "ASMDisk %s is already offline state" % asmdisk_name
                self.SendResponse(self.response)
                return MS_FINISH
            diskgroup_info = common.GetDiskgroupInfoByID(asmdisk_info.diskgroup_id)
            diskgroup_name = diskgroup_info.diskgroup_name
        elif self.request_body.HasField('diskgroup_name') and self.request_body.HasField('failgroup'):
            diskgroup_name = self.request_body.diskgroup_name
            diskgroup_info = common.GetDiskgroupInfoByName(diskgroup_name)
            if not diskgroup_info:
                self.response.rc.retcode = msg_mds.RC_MDS_DISKGROUP_NOT_EXIST
                self.response.rc.message = "Diskgroup %s not exist" % diskgroup_name
                self.SendResponse(self.response)
                return MS_FINISH

            failgroup = self.request_body.failgroup.upper()
            failgroup_list = [asmdisk_info.failgroup for asmdisk_info in g.asmdisk_list.asmdisk_infos if asmdisk_info.diskgroup_id == diskgroup_info.diskgroup_id]
            if failgroup not in failgroup_list:
                self.response.rc.retcode = msg_mds.RC_MDS_FAILGROUP_NOT_IN_DISKGROUP
                self.response.rc.message = "Failgroup %s not in diskgroup %s" % (failgroup, diskgroup_name)
                self.SendResponse(self.response)
                return MS_FINISH
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Miss asmdisk/diskgroup/failgroup name"
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
        if asmdisk_name:
            ret, result = sql.offline_asm_disk(diskgroup_name, asmdisk_name)
        else:
            ret, result = sql.offline_asm_disk(diskgroup_name, failgroup=failgroup)
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_ASMDISK_ONLINE_FAILED
            self.response.rc.message = "ASMDisk offline failed: %s" % result
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
