# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds


class LunActiveMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_ACTIVE_REQUEST

    def INIT(self, request):
        self.default_timeout = 20
        self.response        = MakeResponse(msg_mds.LUN_ACTIVE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_active_request]

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
        self.lun_name = items[1]

        self.lun_info = common.GetLunInfoByName(self.lun_name)
        if self.lun_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun %s not exist" % (self.request_body.lun_name)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.lun_info.asm_status == "ACTIVE":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_ACTIVE_NOT_ALLOWED
            self.response.rc.message = "Lun %s already active state" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        if self.lun_info.config_state == True and self.lun_info.asm_status == "ONLINE":
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_ACTIVE_NOT_ALLOWED
            self.response.rc.message = "Lun %s not in asm group, please add to group first!" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        self.database_node_list = [node_info for node_info in g.nsnode_list.nsnode_infos if node_info.sys_mode != "storage"]
        if self.lun_info.asm_status == "INACTIVE":
            self.mds_database_request = MakeRequest(msg_mds.ASMDISK_ONLINE_REQUEST)
            asmdisk_info = common.GetASMDiskInfoByLunName(self.request_body.lun_name)
            self.mds_database_request.body.Extensions[msg_mds.asmdisk_online_request].asmdisk_name = asmdisk_info.dskname

            # 先向第一个计算节点发送请求
            self.request_num = 1
            return self.send_asm_request()
        elif self.lun_info.config_state == False:
            self.LongWork(self.online_lun, {})

            self.response.rc.retcode = msg_pds.RC_SUCCESS
            self.SendResponse(self.response)
            return MS_FINISH
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Lun active only support lun state is inactive or offline"
            self.SendResponse(self.response)
            return MS_FINISH

    def send_asm_request(self):
        node_info = self.database_node_list[self.request_num-1]
        self.SendRequest(node_info.listen_ip, node_info.listen_port, self.mds_database_request, self.Entry_LunActive)
        return MS_CONTINUE

    def online_lun(self, params={}):
        mds_request = MakeRequest(msg_mds.LUN_ONLINE_REQUEST)
        mds_request.body.Extensions[msg_mds.lun_online_request].lun_name = self.request_body.lun_name
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_LunOnline)

        return MS_CONTINUE

    def Entry_LunOnline(self, response):
        rc = msg_pds.ResponseCode()
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error(response.rc.message)
            rc.retcode = response.rc.retcode
            return rc, None

        self.LongWork(self.active_lun, {})

        rc.retcode = msg_pds.RC_SUCCESS
        return rc, None

    def active_lun(self, params={}):
        rc = msg_pds.ResponseCode()

        time.sleep(5)
        lun_info = common.GetLunInfoByName(self.lun_name)
        if lun_info.asm_status != "INACTIVE":
            logger.run.error("[Lun Active] lun %s online success, but active failed! because it not in asm group." % self.request_body.lun_name)
            rc.retcode = msg_mds.RC_MDS_LUN_ACTIVE_NOT_ALLOWED
            return rc, None

        self.mds_database_request = MakeRequest(msg_mds.ASMDISK_ONLINE_REQUEST)
        asmdisk_info = common.GetASMDiskInfoByLunName(self.request_body.lun_name)
        self.mds_database_request.body.Extensions[msg_mds.asmdisk_online_request].asmdisk_name = asmdisk_info.dskname

        # 先向第一个计算节点发送请求
        self.request_num = 1
        return self.send_asm_request()

    def Entry_LunActive(self, response):   
        rc = msg_pds.ResponseCode()
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            # 向另外的计算节点发送请求，全部失败才返回
            if self.request_num < len(self.database_node_list):
                self.request_num += 1
                return self.send_asm_request()
            else:
                if self.lun_info.asm_status == "OFFLINE":
                    logger.run.error(response.rc.message)
                    rc.retcode = response.rc.retcode
                    return rc, None
                else:
                    self.response.rc.CopyFrom(response.rc)
                    self.SendResponse(self.response)
                    return MS_FINISH
        else:
            # 有一个请求成功则直接返回
            if self.lun_info.asm_status == "OFFLINE":
                logger.run.info("Lun %s active success" % self.request_body.lun_name)
                rc.retcode = msg_pds.RC_SUCCESS
                return rc, None

            self.response.rc.retcode = msg_pds.RC_SUCCESS
            self.SendResponse(self.response)
            return MS_FINISH
