# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_nodemgr import ViewNodeMgr
import message.mds_pb2 as msg_mds
from pdsframe import *

class NodeMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['node']
        self.view = ViewNodeMgr(self.srv)    # 注册视图类

    def cli_info(self, params = {}):
        request = MakeRequest(msg_mds.GET_NODE_INFO_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_info_error(request, response)
        return self.view.cli_info(request, response)

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_NODE_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)

    def cli_config(self, params = {}):
        if params.has_key('attr'):
            attr_items = None
            try:
                attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['attr'].split(',')]
                for attr in attr_items:
                    if attr[0] not in ['nodename']:
                        return self.view.params_error("'attr' parameter illegal, support 'nodename'")
            except:
                return self.view.params_error("Node 'attr' parameter illegal")

            request = MakeRequest(msg_mds.NODE_CONFIG_REQUEST)
            for attr in attr_items:
                if attr[0] == 'nodename':
                    request.body.Extensions[msg_mds.node_config_request].node_name = attr[1]
            response = self.send(request)

            if response.rc.retcode != 0:
                return self.view.cli_config_error(request, response)
            return self.view.cli_config(request, response)
        elif "node_index" in params.keys() and "group_name" in params.keys():
            if "del_node" in params.keys():
                request = MakeRequest(msg_mds.GROUP_DEL_REQUEST)
                request_body = request.body.Extensions[msg_mds.group_del_request]
                request_body.group_name = params["group_name"]
                request_body.node_index = params["node_index"]

                response = self.send(request)
                if response.rc.retcode != 0:
                    return self.view.cli_drop_error(request, response)
                return self.view.cli_drop(request, response)

            else:
                request = MakeRequest(msg_mds.NODE_CONFIG_REQUEST)
                request.body.Extensions[msg_mds.node_config_request].node_index = params["node_index"]
                request.body.Extensions[msg_mds.node_config_request].group_name = params["group_name"]
                response = self.send(request)
                if response.rc.retcode != 0:
                    return self.view.cli_config_error(request, response)
                return self.view.cli_config(request, response)
        else:
            return self.view.params_error("Miss attr parameter")

    def cli_add(self, params = {}):
        if not params.has_key('node_name'):
            return self.view.params_error("Miss node name parameter")

        node_name = params["node_name"]
        request = MakeRequest(msg_mds.NODE_ADD_REQUEST)
        request.body.Extensions[msg_mds.node_add_request].node_name = node_name
        if "group_name" in params.keys():
            request.body.Extensions[msg_mds.node_add_request].group_name = params["group_name"]
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('node_index'):
            return self.view.params_error("Miss node index parameter")

        node_index = params["node_index"]
        request = MakeRequest(msg_mds.NODE_DROP_REQUEST)
        request.body.Extensions[msg_mds.node_drop_request].node_index = node_index
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)
