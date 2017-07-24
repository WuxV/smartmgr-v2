# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class DiskLedMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISK_LED_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.DISK_LED_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.disk_led_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        raid_disk = []
        for rdisk in g.raid_disk_list_all.raid_disk_infos:
            if "%s:%s:%s" % (rdisk.ctl, rdisk.eid, rdisk.slot) == self.request_body.ces_addr:
                raid_disk.append(rdisk)
        if len(raid_disk) == 0:
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            self.response.rc.message = "Disk %s not exist" % self.request_body.ces_addr
            self.SendResponse(self.response)
            return MS_FINISH

        ios_request = MakeRequest(msg_ios.DISK_LED_REQUEST, self.request)
        ios_request.body.Extensions[msg_ios.disk_led_request].ces_addr  = self.request_body.ces_addr
        ios_request.body.Extensions[msg_ios.disk_led_request].is_on     = self.request_body.is_on
        ios_request.body.Extensions[msg_ios.disk_led_request].raid_type = raid_disk[0].raid_type
        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, ios_request, self.Entry_DiskLed)
        return MS_CONTINUE

    def Entry_DiskLed(self, response):
        self.response.rc.CopyFrom(response.rc)
        self.SendResponse(self.response)
        return MS_FINISH
