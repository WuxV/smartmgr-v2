# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
from service_ios.base.raid.megaraid import MegaRaid
from service_ios.base.raid.sas2raid import SAS2Raid
from service_ios.base.raid.hpsaraid import HPSARaid

class DiskLedMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.DISK_LED_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_ios.DISK_LED_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.disk_led_request]

        e = 0
        if self.request_body.raid_type == msg_pds.RAID_TYPE_MEGARAID:
            e, res = MegaRaid().led(self.request_body.ces_addr, self.request_body.is_on)
        elif self.request_body.raid_type == msg_pds.RAID_TYPE_SAS2RAID:
            e, res = SAS2Raid().led(self.request_body.ces_addr, self.request_body.is_on)
        elif self.request_body.raid_type == msg_pds.RAID_TYPE_HPSARAID:
            e, res = HPSARaid().led(self.request_body.ces_addr, self.request_body.is_on)
        else:
            assert(0)

        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_DISK_LED_FAILD
            self.response.rc.message = "Disk led failed :%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
