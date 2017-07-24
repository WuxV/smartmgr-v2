# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

# 最长需要2小时更新
MAX_UPDATE_TIME = 2*3600

class LoopCheckSRPRescanFlagMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME        = 5
    LAST_RESCAN_TIME = 0

    def INIT(self):
        if int(time.time()) - LoopCheckSRPRescanFlagMachine.LAST_RESCAN_TIME > MAX_UPDATE_TIME:
            g.srp_rescan_flag = True

        if g.srp_rescan_flag == False:
            return MS_FINISH
        
        for nsnode_info in filter(lambda nsnode_info:nsnode_info.sys_mode != "storage", g.nsnode_list.nsnode_infos):
            if not nsnode_info.HasField("listen_ip") or not nsnode_info.HasField("broadcast_ip"):
                continue
            logger.run.info("Send rescan srp request to :%s" % nsnode_info.listen_ip)
            self.LongWork(self.send_srp_rescan, nsnode_info)

        LoopCheckSRPRescanFlagMachine.LAST_RESCAN_TIME = int(time.time())
        g.srp_rescan_flag = False
        return MS_FINISH

    def send_srp_rescan(self, params):
        nsnode_info = params
        mds_request = MakeRequest(msg_mds.SRP_RESCAN_SCSI_BUS_REQUEST)
        self.SendRequest(nsnode_info.listen_ip, nsnode_info.listen_port, mds_request, self.Entry_SendSRPRescan)
        return MS_CONTINUE

    def Entry_SendSRPRescan(self, result):
        return MS_FINISH
