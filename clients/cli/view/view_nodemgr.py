# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewNodeMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # Node add
    def cli_add(self, request, response):
        return "Success : add node success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Node drop
    def cli_drop(self, request, response):
        return "Success : drop node success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Node config
    def cli_config(self, request, response):
        return "Success : config node success"

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Node info
    def cli_info(self, request, response):
        node_info = response.body.Extensions[msg_mds.get_node_info_response].node_info
        out  = []
        out.append({"key":"Node Name", 'value':node_info.node_name})

        tbl_th  = ['Key', 'Value']
        tbl_key = ['key', 'value']
        return self.common_list(tbl_th, tbl_key, data=out)

    def cli_info_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Node list
    def cli_list(self, request, response):
        out = []
        for nsnode_info in response.body.Extensions[msg_mds.get_node_list_response].nsnode_infos:
            if nsnode_info.sys_mode != "storage":
                info = {}
                info['node_uuid']    = nsnode_info.node_uuid
                info['node_name']    = nsnode_info.node_name
                info['listen_ip']    = nsnode_info.listen_ip
                info['listen_port']  = nsnode_info.listen_port
                info['host_name']    = nsnode_info.host_name
                info['sys_mode']     = nsnode_info.sys_mode
                info['platform']     = nsnode_info.platform
                info['broadcast_ip'] = nsnode_info.broadcast_ip
                info["ibguids"]= ""
                for i in nsnode_info.ibguids:
                    info["ibguids"] += i
                    info["ibguids"] += "|"

                if nsnode_info.HasField("node_index"):
                    info["node_index"]=nsnode_info.node_index


                if nsnode_info.node_status == msg_pds.NODE_MISSING:
                    info['node_status'] = "Missing"
                
                if nsnode_info.node_status == msg_pds.NODE_CONFIGURED:
                    info['node_status'] = "Configured"
                
                if nsnode_info.node_status == msg_pds.NODE_UNCONFIGURED:
                    info['node_status'] = "Unconfigured"

                out.append(info)
       
        tbl_th  = ["Node Id",'Node Name', 'Platform', 'Mode',     'Host IP',   'Bondib IP','Node Status']
        tbl_key = ["node_index",'node_name', 'platform', 'sys_mode', 'listen_ip', 'broadcast_ip','node_status']

        if self.detail == True:
            tbl_th.extend( ["Node UUID","IB_GUID",'Host Name', ])
            tbl_key.extend(["node_uuid","ibguids",'host_name', ])

        return self.common_list(tbl_th, tbl_key, idx_key='node_name', data=out, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
