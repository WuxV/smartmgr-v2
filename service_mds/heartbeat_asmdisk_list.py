# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds


class HeartBeatASMDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_ASMDISK_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_ASMDISK_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_asmdisk_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        node_name = self.request_body.node_name
        # 更新该节点的asmdisk列表
        asmdisk_list = msg_mds.G_ASMDiskList()
        for asmdisk_info in self.request_body.asmdisk_infos:
            asmdisk_list.asmdisk_infos.add().CopyFrom(asmdisk_info)
        g.all_asmdisk_list[node_name] = asmdisk_list

        # 更新lun列表
        for lun_info in g.lun_list.lun_infos:
            # 确定lun对应的所有计算节点的asmdisk
            d = []
            offline_asmdisk_list = []
            for asmdisk_list in g.all_asmdisk_list.values():
                d.extend([asmdisk_info for asmdisk_info in asmdisk_list.asmdisk_infos if asmdisk_info.path.endswith("%s_%s" % (g.node_info.node_name,lun_info.lun_name))])
                offline_asmdisk_list.extend([asmdisk_info.asmdisk_name for asmdisk_info in asmdisk_list.asmdisk_infos if not asmdisk_info.path and asmdisk_info.mode_status == "OFFLINE"])
            
            lun_info.asm_status = "ONLINE"
            for asmdisk_info in d:
                if asmdisk_info.asmdisk_name:
                    lun_info.asm_status = "ACTIVE"
                    if asmdisk_info.mode_status == "SYNCING":
                        lun_info.asm_status = "SYNC"
                    if asmdisk_info.state == "DROPPING":
                        lun_info.asm_status = "DROPPING"
                    if asmdisk_info.state == "HUNG":
                        lun_info.asm_status = "HUNG"
                else:
                    if asmdisk_info.dskname and asmdisk_info.dskname in offline_asmdisk_list:
                        lun_info.asm_status = "INACTIVE"

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
