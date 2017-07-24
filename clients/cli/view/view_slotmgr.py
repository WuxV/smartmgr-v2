# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewSlotMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # slot list
    def cli_list(self, request, response):
        out    = []
        for slot_info in response.body.Extensions[msg_mds.get_slot_list_response].slot_infos:
            info = {}
            info["slot_id"]     = slot_info.slot_id
            info["bus_address"] = slot_info.bus_address
            info["dev_name"]    = slot_info.dev_name or "--"

            out.append(info)

        tbl_th  = ['Slot ID', 'Bus Address', 'Dev Name']
        tbl_key = ['slot_id', 'bus_address', 'dev_name']

        return self.common_list(tbl_th, tbl_key, idx_key='slot_id', data=out, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
