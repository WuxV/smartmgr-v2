# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewPcsMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # pcs init
    def cli_init(self, request, response):
        return "Success : pcs init success"

    def cli_init_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # pcs info
    def cli_info(self, request, response):
        out = []
        pcs_info = response.body.Extensions[msg_mds.get_pcs_info_response].pcs_info
        out += [{"name":"Cluster Name","value":pcs_info.cluster_name}]
        out += [{"name":"Corosync Status","value":pcs_info.corosync_status}]
        out += [{"name":"Pacemaker Status","value":pcs_info.pacemaker_status}]
        out += [{"name":"Stonith Enabled","value":pcs_info.stonith_enabled}]
        out += [{"name":"Node Status", "value":"%-15s %s" % ("node name","status")}]
        for pcs_node in pcs_info.pcs_nodes:
            out += [{"name":"","value":"%-15s %s" % (pcs_node.node_name, pcs_node.node_status)}] 
        out += [{"name":"Stonith", "value":"%-15s %s" % ("stonith id","status")}]
        for stonith_info in pcs_info.stonith_infos:
           out += [{"name":"","value":"%-15s %s" % (stonith_info.stonith_name, stonith_info.stonith_status)}] 

        tbl_th  = ['Keys', 'Values']
        tbl_key = ['name',  'value']
        return self.common_list(tbl_th, tbl_key, idx_key='pcs_info', data=out, count=True)

    def cli_info_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pcs config
    def cli_config(self, request, response):
        message = response.rc.message
        return "Success : %s" % message

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pcs drop
    def cli_drop(self, request, response):
        return "Success : drop stonith success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

