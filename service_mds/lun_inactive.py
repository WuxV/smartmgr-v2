# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class LunInactiveMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_INACTIVE_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.LUN_INACTIVE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_inactive_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        items = self.request_body.lun_name.split("_")
        if len(items) != 2 or items[0] != g.node_info.node_name:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH
        lun_name = items[1]

        lun_info = common.GetLunInfoByName(lun_name)
        if lun_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun %s not exist" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        if lun_info.asm_status == "INACTIVE":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_INACTIVE_NOT_ALLOWED
            self.response.rc.message = "Lun %s already inactive state" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        if lun_info.asm_status != "ACTIVE":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_INACTIVE_NOT_ALLOWED
            self.response.rc.message = "Lun %s not active state, please active first!" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        self.database_node_list = [node_info for node_info in g.nsnode_list.nsnode_infos if node_info.sys_mode != "storage"]
        self.mds_database_request = MakeRequest(msg_mds.ASMDISK_OFFLINE_REQUEST)
        asmdisk_info = common.GetASMDiskInfoByLunName(self.request_body.lun_name)
        self.mds_database_request.body.Extensions[msg_mds.asmdisk_offline_request].asmdisk_name = asmdisk_info.asmdisk_name

        # 先向第一个计算节点发送请求
        self.request_num = 1
        return self.send_asm_request()

    def send_asm_request(self):
        node_info = self.database_node_list[self.request_num-1]
        self.SendRequest(node_info.listen_ip, node_info.listen_port, self.mds_database_request, self.Entry_LunInactive)
        return MS_CONTINUE

    def Entry_LunInactive(self, response):   
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            # 向另外的计算节点发送请求，全部失败才返回
            if self.request_num < len(self.database_node_list):
                self.request_num += 1
                return self.send_asm_request()
            else:
                self.response.rc.CopyFrom(response.rc)
                self.SendResponse(self.response)
                return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
