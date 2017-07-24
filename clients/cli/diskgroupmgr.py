# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_diskgroupmgr import ViewDiskgroupMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class DiskgroupMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['diskgroup']
        self.view = ViewDiskgroupMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_DISKGROUP_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)

    def cli_add(self, params = {}):
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        if not params.has_key('asmdisk_paths'):
            return self.view.params_error("Miss asmdisk path parameter")
        if params.has_key('redundancy') and params['redundancy'] not in ['external', 'normal', 'high']:
            return self.view.params_error("'redundancy' parameter illegal,support 'external'/'normal'/'high'")
        attr_items = None
        if params.has_key('attr'):
            try:
                attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['attr'].split(',')]
                for attr in attr_items:
                    if attr[0] not in ['compatible.asm', 'compatible.rdbms']:
                        return self.view.params_error("'attr' parameter illegal, support 'compatible.asm'/'compatible.rdbms'")
            except:
                return self.view.params_error("Diskgroup 'attr' parameter illegal")

        request = MakeRequest(msg_mds.DISKGROUP_ADD_REQUEST)
        request.body.Extensions[msg_mds.diskgroup_add_request].diskgroup_name = params['diskgroup_name']
        for path in params['asmdisk_paths'].split(','):
            request.body.Extensions[msg_mds.diskgroup_add_request].asmdisk_paths.append(path)
        if params.has_key('redundancy'):
            request.body.Extensions[msg_mds.diskgroup_add_request].redundancy = params['redundancy']
        if params.has_key('failgroups'):
            for failgroup in params['failgroups'].split(','):
                request.body.Extensions[msg_mds.diskgroup_add_request].failgroups.append(failgroup)
        if params.has_key('attr'):
            for attr in attr_items:
                if attr[0] == 'compatible.asm':
                    request.body.Extensions[msg_mds.diskgroup_add_request].compatible_asm = attr[1]
                if attr[0] == "compatible.rdbms":
                    request.body.Extensions[msg_mds.diskgroup_add_request].compatible_rdbms = attr[1]

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        request = MakeRequest(msg_mds.DISKGROUP_DROP_REQUEST)
        request.body.Extensions[msg_mds.diskgroup_drop_request].diskgroup_name = params['diskgroup_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_config(self, params = {}):
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        if not params.has_key('rebalance'):
            return self.view.params_error("Miss rebalance parameter")
        if not params['rebalance'].isdigit():
            return self.view.params_error("Param 'rebalance' is ilegal")
        request = MakeRequest(msg_mds.DISKGROUP_ALTER_REQUEST)
        request.body.Extensions[msg_mds.diskgroup_config_request].diskgroup_name = params['diskgroup_name']
        request.body.Extensions[msg_mds.diskgroup_config_request].rebalance_power = int(params['rebalance'])
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_config_error(request, response)
        return self.view.cli_config(request, response)

    def cli_mount(self, params = {}):
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        request = MakeRequest(msg_mds.DISKGROUP_MOUNT_REQUEST)
        request.body.Extensions[msg_mds.diskgroup_mount_request].diskgroup_name = params['diskgroup_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_mount_error(request, response)
        return self.view.cli_mount(request, response)

    def cli_umount(self, params = {}):
        if not params.has_key('diskgroup_name'):
            return self.view.params_error("Miss diskgroup name parameter")
        request = MakeRequest(msg_mds.DISKGROUP_UMOUNT_REQUEST)
        request.body.Extensions[msg_mds.diskgroup_umount_request].diskgroup_name = params['diskgroup_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_umount_error(request, response)
        return self.view.cli_umount(request, response)
