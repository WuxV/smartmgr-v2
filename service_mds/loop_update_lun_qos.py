# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import re
import time
import pyudev
import socket
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds.base.apicgroup import APICGroup
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

VENDOR_ID = "SCST_BIO"

class LoopUpdateLunQosMachine(BaseMachine):
    __metaclass__ = MataMachine

    # 更新间隔时间
    LOOP_TIME = 10

    def INIT(self):
        if g.platform['sys_mode'] == "storage":
            return MS_FINISH

        # 获取各存储节点的所有lun和qos信息
        for node_info in g.nsnode_list.nsnode_infos:
            if node_info.sys_mode != "database":
                self.node_name = node_info.node_name
                mds_storage_request = MakeRequest(msg_mds.GET_LUN_QOS_LIST_REQUEST)
                self.SendRequest(node_info.listen_ip, node_info.listen_port, mds_storage_request, self.Entry_LoopUpdateLunQos)

        return MS_CONTINUE

    def get_mpath_devices(self):
        e, out = command("/sbin/multipath -ll")
        if e == -2:
            return e, out
        txt = out.splitlines()

        mpdevs = {}
        devreg = ur"^(\S+)\s+\((\S+)\)\s+(dm-\d+)\s+(\S+),(\S+)\s*$"
        pthreg = ur"\s+\|-\s+(\d+:\d+:\d+:\d+)\s+(\S+)\s+(\S+:\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$"
        pthreg1 = ur"\s+\`-\s+(\d+:\d+:\d+:\d+)\s+(\S+)\s+(\S+:\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$"
        for k in range(len(txt)):
            result = re.search(devreg, txt[k])
            if result:
                if not result.group(4) == "SCST_BIO":
                    continue
                product_id = os.path.join('/dev', result.group(3))    # attach_lun
                mpdevs[product_id] = []
            else:
                result = re.search(pthreg, txt[k])
                if not result:
                    result = re.search(pthreg1, txt[k])
                if not result:
                    continue
                if product_id:
                    mpdevs[product_id].append(result.group(3))         # major:minor

        return (0, mpdevs)

    def set_lun_qos(self, qos_info, maj_mins):
        params = {}
        params['read_bps_device']   = 1024 * qos_info.read_bps
        params['read_iops_device']  = qos_info.read_iops
        params['write_bps_device']  = 1024 * qos_info.write_bps
        params['write_iops_device'] = qos_info.write_iops
        for maj_min in maj_mins:
            e, res = APICGroup().set_qos(maj_min, params)
            if e:
                logger.run.error("Set qos failed %s %s" % (maj_min, params))

        return MS_FINISH

    def drop_lun_qos(self, maj_mins):
        for maj_min in maj_mins:
            e, res = APICGroup().drop_qos(maj_min)
            if e:
                logger.run.error("Drop qos failed %s" % (maj_min))

        return MS_FINISH

    def Entry_LoopUpdateLunQos(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error(response.rc.message)
            return MS_FINISH
        
        lun_qos_infos = response.body.Extensions[msg_mds.get_lun_qos_list_response].lun_qos_infos

        # 获取所有的多路径设备
        ret, mpdevs = self.get_mpath_devices()
        if ret:
            logger.run.error("Get mpath devices list filed: %s" % mpdevs)
            return MS_FINISH
        for mpdev in mpdevs:
            e, out = command("sg_inq -p 0x83 %s | grep \"vendor specific:\" |  awk '{print $3}'" % mpdev)
            if e == -2:
                logger.run.error("Command sg_inq failed")
                return MS_FINISH
            for lun_qos_info in lun_qos_infos:
                if out == lun_qos_info.lun_id[0:23]:
                    if lun_qos_info.qos_info:
                        self.set_lun_qos(lun_qos_info.qos_info, mpdevs[mpdev])
                    else:
                        self.drop_lun_qos(mpdevs[mpdev])

        return MS_FINISH
