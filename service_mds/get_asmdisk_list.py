# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import OraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetASMDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_ASMDISK_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_ASMDISK_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_asmdisk_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.ip          = g.listen_ip
        self.port        = config.safe_get('oracle', 'port')
        self.uid         = config.safe_get('oracle', 'user')
        self.passwd      = config.safe_get('oracle', 'password')
        self.servicename = config.safe_get('oracle', 'servicename')
        sql = OraSQLPlus(self.servicename, self.ip, self.port, self.uid, self.passwd)
        ret, disk_list = sql.list_asm_disks()
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_GET_ASM_DISK_LIST_FAILED
            self.response.rc.message = "Get asm disklist failed: %s" % disk_list
            self.SendResponse(self.response)
            return MS_FINISH

        for disk in disk_list:
            asmdisk_info = msg_pds.ASMDiskInfo()
            asmdisk_info.asmdisk_name = disk["name"] or ""
            asmdisk_info.asmdisk_id   = str(disk["disk_number"])
            asmdisk_info.diskgroup_id = str(disk["group_number"])
            asmdisk_info.state        = disk["state"]
            asmdisk_info.mode_status  = disk["mode_status"]
            asmdisk_info.path         = disk["path"] or ""
            asmdisk_info.failgroup    = disk["failgroup"] or ""
            asmdisk_info.total_mb     = int(disk["total_mb"])
            asmdisk_info.free_mb      = int(disk["free_mb"])

            self.response.body.Extensions[msg_mds.get_asmdisk_list_response].asmdisk_infos.add().CopyFrom(asmdisk_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
