# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from base import asm
from base.asm import OraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class GetDiskgroupListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_DISKGROUP_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_DISKGROUP_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_diskgroup_list_request]

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
        ret, diskgroup_list = sql.list_asm_group()
        if ret:
            self.response.rc.retcode = msg_mds.RC_MDS_GET_ASM_DISKGROUP_LIST_FAILED
            self.response.rc.message = "Get asm diskgroup list failed: %s" % diskgroup_list
            self.SendResponse(self.response)
            return MS_FINISH

        for dg in diskgroup_list:
            diskgroup_info = msg_pds.DiskgroupInfo()
            diskgroup_info.diskgroup_name = dg["name"]
            diskgroup_info.diskgroup_id   = str(dg["group_number"])
            diskgroup_info.type           = dg["type"] or ""
            diskgroup_info.state          = dg["state"]
            diskgroup_info.offline_disks  = int(dg["offline_disks"])
            diskgroup_info.total_mb       = int(dg["total_mb"])
            diskgroup_info.free_mb        = int(dg["free_mb"])
            diskgroup_info.usable_file_mb = int(dg["usable_file_mb"])

            self.response.body.Extensions[msg_mds.get_diskgroup_list_response].diskgroup_infos.add().CopyFrom(diskgroup_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
