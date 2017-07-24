# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewGrpMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # group list
    def cli_list(self, request, response):
        out    = []
        for group_info in response.body.Extensions[msg_mds.get_group_list_response].groups:
            info = {}
            info["group_name"] = group_info.group_name
            if group_info.nsnode_infos:
                info["node_name"] = "|"
                for node in group_info.nsnode_infos:
                    info["node_name"] = info["node_name"] + node.node_info.node_index + "|"
            out.append(info)

        tbl_th  = ['Group Name',"Node Name"]
        tbl_key = ['group_name',"node_name"]
        return self.common_list(tbl_th, tbl_key, idx_key='group_name', data=out, count=True)

            
    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun add
    def cli_add(self, request, response):
        return "Success : add lun group success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # group drop
    def cli_drop(self, request, response):
        return "Success : drop lun group success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

