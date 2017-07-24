# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

SRBDADM = "/usr/sbin/drbdadm"
SRBDDISK = "/dev/srbd1"

class SrbdSplitBrainRecoveryMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SRBD_SPLITBRAIN_RECOVERY_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.SRBD_SPLITBRAIN_RECOVERY_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.srbd_splitbrain_recovery_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        e,res = self.srbd_splitbrain_recovery()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_SRBD_SPLITBRAIN_RECOVERY_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH       

    def srbd_splitbrain_recovery(self):
        # umount srbd1
        e, out = common._umount()
        if e:
            return e, out

        # 断开srbd连接
        cmd_str = "%s disconnect r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'.*(unknown connection).*',out):
                pass
            else:
                return e,out
        # 设置node节点为secondary
        cmd_str = "%s secondary r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            return e,out
        # 放弃该节点数据，重新从primary同步过来
        cmd_str = "%s -- --discard-my-data connect r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"splitbrain_recovery srbd success"
