# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_asmdiskmgr import ViewASMDiskMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class ASMDiskMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['asmdisk']
        self.view = ViewASMDiskMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_ASMDISK_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)

    def cli_add(self, params = {}):
        if not params.has_key('asmdisk_path'):
            return self.view.params_error("Miss asmdisk path parameter")
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        if params.has_key('rebalance') and not params['rebalance'].isdigit():
            return self.view.params_error("Param 'rebalance' is ilegal")
        request = MakeRequest(msg_mds.ASMDISK_ADD_REQUEST)
        request.body.Extensions[msg_mds.asmdisk_add_request].asmdisk_path = params['asmdisk_path']
        request.body.Extensions[msg_mds.asmdisk_add_request].diskgroup_name = params['diskgroup_name']
        if params.has_key('rebalance'):
            request.body.Extensions[msg_mds.asmdisk_add_request].rebalance_power = int(params['rebalance'])
        if params.has_key('force') and params['force'] == True:
            request.body.Extensions[msg_mds.asmdisk_add_request].force = True
        if params.has_key('failgroup'):
            request.body.Extensions[msg_mds.asmdisk_add_request].failgroup = params['failgroup']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('asmdisk_name'):
            return self.view.params_error("Miss asmdisk name parameter")
        if params.has_key('rebalance') and not params['rebalance'].isdigit():
            return self.view.params_error("Param 'rebalance' is ilegal")
        request = MakeRequest(msg_mds.ASMDISK_DROP_REQUEST)
        request.body.Extensions[msg_mds.asmdisk_drop_request].asmdisk_name = params['asmdisk_name']
        if params.has_key('rebalance'):
            request.body.Extensions[msg_mds.asmdisk_drop_request].rebalance_power = int(params['rebalance'])
        if params.has_key('force') and params['force'] == True:
            request.body.Extensions[msg_mds.asmdisk_drop_request].force = True
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_online(self, params = {}):
        if not params.has_key('asmdisk_name') and not params.has_key('failgroup'):
            return self.view.params_error("Miss asmdisk/failgroup name parameter")
        if params.has_key('failgroup') and not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")

        request = MakeRequest(msg_mds.ASMDISK_ONLINE_REQUEST)
        if params.has_key('asmdisk_name'):
            request.body.Extensions[msg_mds.asmdisk_online_request].asmdisk_name = params['asmdisk_name']
        if params.has_key('failgroup'):
            request.body.Extensions[msg_mds.asmdisk_online_request].failgroup = params['failgroup']
        if params.has_key('diskgroup_name'):
            request.body.Extensions[msg_mds.asmdisk_online_request].diskgroup_name = params['diskgroup_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_online_error(request, response)
        return self.view.cli_online(request, response)

    def cli_offline(self, params = {}):
        if not params.has_key('asmdisk_name') and not params.has_key('failgroup'):
            return self.view.params_error("Miss asmdisk/failgroup name parameter")
        if params.has_key('failgroup') and not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")

        request = MakeRequest(msg_mds.ASMDISK_OFFLINE_REQUEST)
        if params.has_key('asmdisk_name'):
            request.body.Extensions[msg_mds.asmdisk_offline_request].asmdisk_name = params['asmdisk_name']
        if params.has_key('failgroup'):
            request.body.Extensions[msg_mds.asmdisk_offline_request].failgroup = params['failgroup']
        if params.has_key('diskgroup_name'):
            request.body.Extensions[msg_mds.asmdisk_offline_request].diskgroup_name = params['diskgroup_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_offline_error(request, response)
        return self.view.cli_offline(request, response)
