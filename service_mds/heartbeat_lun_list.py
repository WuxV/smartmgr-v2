# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class HeartBeatLunListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_LUN_LIST_REQUEST

    LIST_LUN_EXPORT_KEYS = None

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_LUN_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_lun_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        lun_export_list = {}
        for lun_export_info in self.request_body.lun_export_infos:
            key = "%s.%s" % (lun_export_info.lun_name, lun_export_info.t10_dev_id)
            lun_export_list[key] = lun_export_info

        _lun_export_keys = lun_export_list.keys()
        _lun_export_keys.sort()

        if HeartBeatLunListMachine.LIST_LUN_EXPORT_KEYS != _lun_export_keys:
            g.srp_rescan_flag = True
        HeartBeatLunListMachine.LIST_LUN_EXPORT_KEYS =_lun_export_keys

        for lun_info in g.lun_list.lun_infos:
            key = "%s_%s.%s" % (g.node_info.node_name, lun_info.lun_name, lun_info.lun_id[:23])
            if key in lun_export_list.keys():
                if lun_info.actual_state == False:
                    logger.run.info('[NODE STATE]: change lun %s actual state to True' % lun_info.lun_id)
                lun_info.actual_state        = True
                lun_info.last_heartbeat_time = int(time.time())
                lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].CopyFrom(lun_export_list[key])

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
