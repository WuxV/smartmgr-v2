# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_groupmgr import ViewGrpMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class GrpMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['group']
        self.view = ViewGrpMgr(self.srv)    # 注册视图类

    def cli_add(self, params = {}):
        if not params.has_key("group_name"):
            return self.view.params_error("Miss lun group name parameter")

        request = MakeRequest(msg_mds.GROUP_ADD_REQUEST)
        request_body = request.body.Extensions[msg_mds.group_add_request]
        request_body.group_name = params["group_name"]

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key("group_name"):
            return self.view.params_error("Miss lun group name parameter")
     
        request = MakeRequest(msg_mds.GROUP_DROP_REQUEST)
        request_body = request.body.Extensions[msg_mds.group_drop_request]
        request_body.group_name = params["group_name"]

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_GROUP_LIST_REQUEST)
        request_body = request.body.Extensions[msg_mds.get_group_list_request]
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)

    def cli_del(self, params = {}):
        if not params.has_key("group_name"):
            return self.view.params_error("Miss lun group name parameter")
        
        if not params.has_key("node_index"):
            return self.view.params_error("Miss lun node index parameter")

        request = MakeRequest(msg_mds.GROUP_DEL_REQUEST)
        request_body = request.body.Extensions[msg_mds.group_del_request]
        request_body.group_name = params["group_name"]
        request_body.node_index = params["node_index"]

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)


