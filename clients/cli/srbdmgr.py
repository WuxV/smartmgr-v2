# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_srbdmgr import ViewSrbdMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

SRBD_KEY    = ['node1_srbd_netcard','node1_srbd_mask','node1_srbd_ip','node1_ipmi_ip','node1_hostname','node2_passwd','node2_hostname','node2_srbd_ip','node2_ipmi_ip']
SRBD_STATUS = ['role_status','con_status', 'disk_status']
ROLE = ['primary','secondary']
ACTION = ['disconnect', 'connect', 'on', 'off']

class SrbdMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['srbd']
        self.view = ViewSrbdMgr(self.srv)    # 注册视图类

    # srbd init 
    def cli_init(self, params = {}):
        request = MakeRequest(msg_mds.SRBD_INIT_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_init_error(request, response)
        return self.view.cli_init(request, response)

    # srbd info 
    def cli_info(self, params = {}):
        request = MakeRequest(msg_mds.GET_SRBD_INFO_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_info_error(request, response)
        return self.view.cli_info(request, response)

     # 配置srbd的信息, 包括配置节点role, on/off connect/disconnect srbd
    def cli_config(self, params = {}):
        if params.has_key('nodeid') and params.has_key('key'): 
            attr_items = None
            try:
                attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['key'].split(',')]
                for attr in attr_items:
                    a = params['nodeid'] + "_" + attr[0] 
                    if a not in SRBD_KEY:
                        return self.view.params_error("'key' parameter illegal, support %s") % SRBD_KEY
                    if attr[0] in SRBD_STATUS:
                        return self.view.params_error("'key' parameter illegal, can't config % status") % SRBD_STATUS
            except:
                return self.view.params_error("Srbd 'key' parameter illegal")
            request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
            for attr in attr_items:
                if params['nodeid'] + "_" + attr[0] in SRBD_KEY and attr[0] not in SRBD_STATUS:
                    srbd_config = msg_pds.SrbdConfig()
                    srbd_config.nodeid = str(params['nodeid'])
                    srbd_config.srbd_key = str(params['nodeid'] + "_" + attr[0])
                    srbd_config.srbd_value = attr[1]
                    request.body.Extensions[msg_mds.srbd_config_request].srbd_config.CopyFrom(srbd_config)
            response = self.send(request)

            if response.rc.retcode != 0:
                return self.view.cli_config_error(request, response)
            return self.view.cli_config(request, response)
        elif "role" in params.keys():
            if params['role'] not in ROLE: 
                return self.view.params_error("'role' parameter illegal, support %s") % ROLE
            request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
            request.body.Extensions[msg_mds.srbd_config_request].node_role = params['role']
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_config_error(request, response)
            return self.view.cli_config(request, response)
        elif "action" in params.keys():
            if params['action'] not in ACTION: 
                return self.view.params_error("'action' parameter illegal, support %s") % ACTION
            request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
            request.body.Extensions[msg_mds.srbd_config_request].node_action = params['action']
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_config_error(request, response)
            return self.view.cli_config(request, response)
        else:
            return self.view.params_error("Miss attr parameter")

    # srbd split brain recovery
    def cli_sbr(self, params = {}):
        request = MakeRequest(msg_mds.SRBD_SPLITBRAIN_RECOVERY_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_sbr_error(request, response)
        return self.view.cli_sbr(request, response)
