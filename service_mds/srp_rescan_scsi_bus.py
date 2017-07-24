# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class SRPRescanSCSIBusMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SRP_RESCAN_SCSI_BUS_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.SRP_RESCAN_SCSI_BUS_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.srp_rescan_scsi_bus_response]

        logger.run.info("Start rescan SCSI bus")
        self.LongWork(self.rescan_scsi_bus, {})

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def rescan_scsi_bus(self, params):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        # 如果有扫描进程, 则不再扫描
        e, out = command("/usr/bin/ps -elf | grep smartstore_srp_rescan_scsi_bus.sh | grep -v grep")
        if out.find("smartstore_srp_rescan_scsi_bus") != -1:
            return  rc, None

        command("/usr/bin/smartstore_srp_rescan_scsi_bus.sh --offline")
        command("/usr/bin/smartstore_srp_rescan_scsi_bus.sh --online")

        return rc, None
