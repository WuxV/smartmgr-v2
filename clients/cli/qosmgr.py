# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_qosmgr import ViewQosMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class QosMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['qos']
        self.view = ViewQosMgr(self.srv)    # 注册视图类

    def cli_add(self, params = {}):
        if not params.has_key('qos_name'):
            return self.view.params_error("Miss qos 'name' parameter")
        if not params.has_key('items'):
            return self.view.params_error("Miss qos 'items' parameter")

        try:
            qos_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['items'].split(',')]
        except:
            return self.view.params_error("QoS 'items' parameter illegal, e.g. read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100")

        for items in qos_items:
            if items[0] not in ['read-bps', 'read-iops', 'write-bps', 'write-iops']:
                return self.view.params_error("QoS 'items' parameter not support '%s'" % items[0])
            if not str(items[1]).isdigit() or int(items[1]) > 1000000000:
                return self.view.params_error("Param '%s' is not legal" % items[0])

        request = MakeRequest(msg_mds.QOS_TEMPLATE_ADD_REQUEST)
        request.body.Extensions[msg_mds.qos_template_add_request].template_name = params['qos_name']

        for items in qos_items:
            if   items[0] == "read-bps":
                request.body.Extensions[msg_mds.qos_template_add_request].qos_info.read_bps   = int(items[1])
            elif items[0] == "read-iops":
                request.body.Extensions[msg_mds.qos_template_add_request].qos_info.read_iops  = int(items[1])
            elif items[0] == "write-bps":
                request.body.Extensions[msg_mds.qos_template_add_request].qos_info.write_bps  = int(items[1])
            elif items[0] == "write-iops":
                request.body.Extensions[msg_mds.qos_template_add_request].qos_info.write_iops = int(items[1])

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        else:
            return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('qos_name'):
            return self.view.params_error("Miss qos 'name' parameter")

        request = MakeRequest(msg_mds.QOS_TEMPLATE_DROP_REQUEST)
        request.body.Extensions[msg_mds.qos_template_drop_request].template_name = params['qos_name']

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        else:
            return self.view.cli_drop(request, response)

    def cli_update(self, params = {}):
        if not params.has_key('qos_name'):
            return self.view.params_error("Miss qos 'name' parameter")
        if not params.has_key('items'):
            return self.view.params_error("Miss qos 'items' parameter")

        try:
            qos_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['items'].split(',')]
        except:
            return self.view.params_error("QoS 'items' parameter illegal, e.g. read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100")

        for items in qos_items:
            if items[0] not in ['read-bps', 'read-iops', 'write-bps', 'write-iops']:
                return self.view.params_error("QoS 'items' parameter not support '%s'" % items[0])
            if not str(items[1]).isdigit() or int(items[1]) > 1000000000:
                return self.view.params_error("Param '%s' is not legal" % items[0])

        request = MakeRequest(msg_mds.QOS_TEMPLATE_UPDATE_REQUEST)
        request.body.Extensions[msg_mds.qos_template_update_request].template_name = params['qos_name']

        for items in qos_items:
            if   items[0] == "read-bps":
                request.body.Extensions[msg_mds.qos_template_update_request].qos_info.read_bps   = int(items[1])
            elif items[0] == "read-iops":
                request.body.Extensions[msg_mds.qos_template_update_request].qos_info.read_iops  = int(items[1])
            elif items[0] == "write-bps":
                request.body.Extensions[msg_mds.qos_template_update_request].qos_info.write_bps  = int(items[1])
            elif items[0] == "write-iops":
                request.body.Extensions[msg_mds.qos_template_update_request].qos_info.write_iops = int(items[1])

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_update_error(request, response)
        else:
            return self.view.cli_update(request, response)

    def cli_link(self, params = {}):
        if not params.has_key('qos_name'):
            return self.view.params_error("Miss qos 'name' parameter")
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss 'lun' parameter")

        request = MakeRequest(msg_mds.LINK_QOS_TEMPLATE_REQUEST)
        request.body.Extensions[msg_mds.link_qos_template_request].template_name = params['qos_name']
        request.body.Extensions[msg_mds.link_qos_template_request].lun_name = params['lun_name']

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_link_error(request, response)
        else:
            return self.view.cli_link(request, response)

    def cli_unlink(self, params = {}):
        if not params.has_key('lun_name'):
            return self.view.params_error("Miss lun 'lun' parameter")

        request = MakeRequest(msg_mds.UNLINK_QOS_TEMPLATE_REQUEST)
        request.body.Extensions[msg_mds.unlink_qos_template_request].lun_name = params['lun_name']

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_unlink_error(request, response)
        else:
            return self.view.cli_unlink(request, response)

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_QOS_TEMPLATE_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)
