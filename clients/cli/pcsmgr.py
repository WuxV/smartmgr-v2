# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_pcsmgr import ViewPcsMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

ACTION = ['on', 'off', 'enable', 'disable']
class PcsMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['pcs']
        self.view = ViewPcsMgr(self.srv)    # 注册视图类

    # pcs init 
    def cli_init(self, params = {}):
        request = MakeRequest(msg_mds.PCS_INIT_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_init_error(request, response)
        return self.view.cli_init(request, response)

    # pcs info 
    def cli_info(self, params = {}):
        request = MakeRequest(msg_mds.GET_PCS_INFO_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_info_error(request, response)
        return self.view.cli_info(request, response)

    # pcs config
    def cli_config(self, params = {}):
        if params.has_key('action'): 
            if params['action'] not in ACTION: 
                return self.view.params_error("'action' parameter illegal, support %s") % ACTION
            request = MakeRequest(msg_mds.PCS_CONFIG_REQUEST)
            request.body.Extensions[msg_mds.pcs_config_request].action = params['action']
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_config_error(request, response)
            return self.view.cli_config(request, response)
        else:
            return self.view.params_error("Miss attr parameter")

    # pcs drop stonith
    def cli_drop(self,params = {}):
        if not params.has_key('stonith_name'):
            return self.view.params_error("Miss param 'stonith'")
        request = MakeRequest(msg_mds.PCS_DROP_STONITH_REQUEST)
        request.body.Extensions[msg_mds.pcs_drop_stonith_request].stonith_name = params['stonith_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request,response)
        return self.view.cli_drop(request,response)

