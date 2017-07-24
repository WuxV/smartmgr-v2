# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class GetNodeListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_NODE_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_NODE_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_node_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 已经配置的uuid列表
        uuids_conf = {}

        # 广播的uuid列表
        uuids_broadcast = []

        for node in g.nsnode_conf_list.nsnode_infos:
            uuids_conf[node.node_uuid] = node.node_info.node_index
        
        local_ip = g.listen_ip
        for nsnode_info in g.nsnode_list.nsnode_infos:
            if not nsnode_info.HasField("listen_ip") or not nsnode_info.HasField("broadcast_ip") or not nsnode_info.HasField("node_uuid"):
                continue

            if self.request_body.HasField('is_remove_smartmon'):
                if nsnode_info.is_smartmon == True:
                    continue

            if nsnode_info.node_uuid in uuids_conf.keys():
                nsnode_info.node_status = msg_pds.NODE_CONFIGURED
                nsnode_info.node_index = uuids_conf[nsnode_info.node_uuid]
            else:
                nsnode_info.node_status = msg_pds.NODE_UNCONFIGURED

            uuids_broadcast.append(nsnode_info.node_uuid)
            self.response.body.Extensions[msg_mds.get_node_list_response].nsnode_infos.add().CopyFrom(nsnode_info)

        for node in g.nsnode_conf_list.nsnode_infos:
            if node.node_uuid not in uuids_broadcast:
                nodeinfo = msg_pds.NSNodeInfo()
                nodeinfo.node_status = msg_pds.NODE_MISSING
                nodeinfo.node_index = node.node_info.node_index
                nodeinfo.node_name = node.node_info.node_name
                nodeinfo.listen_ip = node.node_info.listen_ip
                nodeinfo.listen_port = node.node_info.listen_port
                self.response.body.Extensions[msg_mds.get_node_list_response].nsnode_infos.add().CopyFrom(nodeinfo)
                    
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
