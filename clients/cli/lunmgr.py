# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_lunmgr import ViewLunMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class LunMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['lun']
        self.view = ViewLunMgr(self.srv)    # 注册视图类

    def cli_add(self, params = {}):
        is_pmt = False
        if params.has_key("pool_name") and params.has_key("size"):
            if params.has_key("data_disk_name") or params.has_key("cache_disk_name") or params.has_key("basedisk"):
                return self.view.params_error("Create pmt lun only support params 'pool' and 'size'")
            if not params['size'][-1] in ['g', 'G']:
                return self.view.params_error("Please use size unit by 'G'")
            if not str(params['size'][:-1]).isdigit() or int(params['size'][:-1]) == 0:
                return self.view.params_error("Param 'new size' is not legal")
            is_pmt = True

        if is_pmt == False:
            if not params.has_key('data_disk_name'):
                return self.view.params_error("Miss disk name parameter")
            if params.has_key('cache_disk_name') and params.has_key('pool_name'):
                return self.view.params_error("Only support one cache model, disk cache or pool cache")

        request = MakeRequest(msg_mds.LUN_ADD_REQUEST)
        request_body = request.body.Extensions[msg_mds.lun_add_request]
        if is_pmt == True:
            request_body.lun_type = msg_pds.LUN_TYPE_PALPMT
            request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].pool_name  = params['pool_name']
            request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].size       = int(params['size'][:-1])
        if is_pmt == False and params.has_key('cache_disk_name'):
            request_body.lun_type = msg_pds.LUN_TYPE_SMARTCACHE
            request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].data_disk_name  = params['data_disk_name']
            request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].cache_disk_name = params['cache_disk_name']
        if is_pmt == False and params.has_key('pool_name'):
            request_body.lun_type = msg_pds.LUN_TYPE_PALCACHE
            request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].data_disk_name = params['data_disk_name']
            request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].pool_name      = params['pool_name']
        if is_pmt == False and not params.has_key('pool_name') and not params.has_key('cache_disk_name'):
            if params['data_disk_name'].startswith("/dev/mapper/") and params['data_disk_name'].find("lvvote") != -1:
                request_body.lun_type = msg_pds.LUN_TYPE_BASEDEV
                request_body.Extensions[msg_mds.ext_lunaddrequest_basedev].dev_name = params['data_disk_name']
            else:
                if params.has_key('basedisk') and params['basedisk'] == True:
                    request_body.lun_type = msg_pds.LUN_TYPE_BASEDISK
                    request_body.Extensions[msg_mds.ext_lunaddrequest_basedisk].data_disk_name = params['data_disk_name']
                else:
                    request_body.lun_type = msg_pds.LUN_TYPE_PALRAW
                    request_body.Extensions[msg_mds.ext_lunaddrequest_palraw].data_disk_name = params['data_disk_name']
        if params.has_key("group_name"):
            request.body.Extensions[msg_mds.lun_add_request].group_name = str(params['group_name'])
        else:
            return self.view.params_error("Miss lun group")

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        if params.has_key('rebalance') and not params['rebalance'].isdigit():
            return self.view.params_error("Param 'rebalance' is ilegal")
        request = MakeRequest(msg_mds.LUN_DROP_REQUEST)
        request.body.Extensions[msg_mds.lun_drop_request].lun_name = params['lun_name']
        if params.has_key('rebalance'):
            request.body.Extensions[msg_mds.lun_drop_request].rebalance_power = int(params['rebalance'])
        if params.has_key('force') and params['force'] == True:
            request.body.Extensions[msg_mds.lun_drop_request].force = True
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_LUN_LIST_REQUEST)
        if params.has_key('qos_name'):
            request.body.Extensions[msg_mds.get_lun_list_request].qos_name = params['qos_name']

        if params.has_key('group_name'):
            request.body.Extensions[msg_mds.get_lun_list_request].group_name = params['group_name']

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        if params.has_key('node'):
            return self.view.cli_list_node(request, response)
        else:
            return self.view.cli_list(request, response)

    def cli_online(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        request = MakeRequest(msg_mds.LUN_ONLINE_REQUEST)
        request.body.Extensions[msg_mds.lun_online_request].lun_name = params['lun_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_online_error(request, response)
        return self.view.cli_online(request, response)

    def cli_offline(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        request = MakeRequest(msg_mds.LUN_OFFLINE_REQUEST)
        request.body.Extensions[msg_mds.lun_offline_request].lun_name = params['lun_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_offline_error(request, response)
        return self.view.cli_offline(request, response)

    def cli_config(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        if not params.has_key("group_name"):
            return self.view.params_error("Miss group name parameter")

        request = MakeRequest(msg_mds.LUN_CONFIG_REQUEST)
        request.body.Extensions[msg_mds.lun_config_request].lun_name = params['lun_name']
        if params.has_key("group_name"):
            request.body.Extensions[msg_mds.lun_config_request].group_name = str(params['group_name'])

        if params.has_key('del_group') and params['del_group'] == True:
            request.body.Extensions[msg_mds.lun_config_request].del_group = True

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_config_error(request, response)
        return self.view.cli_config(request, response)

    def cli_active(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        if params.has_key('rebalance') and not params['rebalance'].isdigit():
            return self.view.params_error("Param 'rebalance' is ilegal")
        request = MakeRequest(msg_mds.LUN_ACTIVE_REQUEST)
        request.body.Extensions[msg_mds.lun_active_request].lun_name = params['lun_name']
        if params.has_key('rebalance'):
            request.body.Extensions[msg_mds.lun_active_request].rebalance_power = int(params['rebalance'])
        if params.has_key('force') and params['force'] == True:
            request.body.Extensions[msg_mds.lun_active_request].force = True
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_active_error(request, response)
        return self.view.cli_active(request, response)

    def cli_inactive(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun name parameter")
        request = MakeRequest(msg_mds.LUN_INACTIVE_REQUEST)
        request.body.Extensions[msg_mds.lun_inactive_request].lun_name = params['lun_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_inactive_error(request, response)
        return self.view.cli_inactive(request, response)
