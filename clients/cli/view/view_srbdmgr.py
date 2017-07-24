# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewSrbdMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # srbd init
    def cli_init(self, request, response):
        return "Success : srbd init success"

    def cli_init_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # srbd info
    def cli_info(self, request, response):
        out  = []
        for srbd_info in response.body.Extensions[msg_mds.get_srbd_info_response].srbd_infos:
            info = {}
            info["role_status"]        = srbd_info.role_status or "--"
            info["con_status"]         = srbd_info.con_status  or "--"
            info["disk_status"]        = srbd_info.disk_status or "--"
            info['node_srbd_name']     =  srbd_info.node_srbd_name or "--"   
            info['node_srbd_ip']       =  srbd_info.node_srbd_ip or "--" 
            info['node_srbd_netmask']  =  srbd_info.node_srbd_netmask or "--"
            info['node_ipmi_ip']       =  srbd_info.node_ipmi_ip or "--"    
            info['node_srbd_netcard']  =  srbd_info.node_srbd_netcard or "--"
            info['node_type']          =  srbd_info.node_type or "--" 
            out.append(info)

        tbl_th  = ['Node' , 'Node Name' , 'Srbd Network', 'Netmask','Ipmi Network','Netcard','Role', 'Connect Status', 'Disk status']
        tbl_key = ['node_type','node_srbd_name','node_srbd_ip','node_srbd_netmask','node_ipmi_ip','node_srbd_netcard','role_status', 'con_status', 'disk_status']

        return self.common_list(tbl_th, tbl_key, idx_key='srbd_info', data=out, count=True)

    def cli_info_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Srbd config
    def cli_config(self, request, response):
        message = response.rc.message
        return "Success : %s" % message

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # srbd split brain recovery
    def cli_sbr(self, request, response):
        return "Success : srbd split brain recovery success"

    def cli_sbr_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
