# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

PCS = "/usr/sbin/pcs"

class GetPcsInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_PCS_INFO_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_PCS_INFO_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_pcs_info_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        e, pcs_info = self.pcs_info()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_GET_PCS_INFO_FAILED
            self.response.rc.message = "%s" % pcs_info
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.body.Extensions[msg_mds.get_pcs_info_response].pcs_info.CopyFrom(pcs_info)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def pcs_info(self):
        pcs_info = msg_pds.PcsInfo()
        cmd_str = "%s status" % PCS
        e,out = command(cmd_str)
        if e:
            if re.search(r'(.*)cluster is not currently running(.*)',out):
                return 1,"cluster is not running"    
            return e,out
        for line in out.splitlines():
            if line.split(':')[0].strip() == "Cluster name":
                pcs_info.cluster_name = line.split(':')[1].strip()
            s = re.search(r'(.*)\(stonith:fence_ipmilan\)\:(.*)',line)
            if s:
                stonith_info = msg_pds.StonithInfo()
                stonith_info.stonith_name   = s.group(1).strip()
                stonith_info.stonith_status = s.group(2).strip()
                pcs_info.stonith_infos.add().CopyFrom(stonith_info)
            if line.split(':')[0].strip() == "Online":
                a = line.split(':')[1].split()
                if len(a) >= 4:
                    lt = []
                    lt.append(a[1])
                    lt.append(a[2])
                    for node in lt:
                        pcs_node = msg_pds.PcsNode()
                        pcs_node.node_name = node
                        pcs_node.node_status = "online"
                        pcs_info.pcs_nodes.add().CopyFrom(pcs_node)
                else:
                    pcs_node = msg_pds.PcsNode()
                    pcs_node.node_name = a[1]
                    pcs_node.node_status = "online"
                    pcs_info.pcs_nodes.add().CopyFrom(pcs_node)
            s = re.search(r'(.*): UNCLEAN(.*)',line)
            if s:
                pcs_node = msg_pds.PcsNode()
                pcs_node.node_name = s.group(1).strip().split()[1]
                pcs_node.node_status = "offline"
                pcs_info.pcs_nodes.add().CopyFrom(pcs_node)
            if line.split(':')[0].strip() == "OFFLINE":
                a = line.split(':')[1].split()
                if len(a) >= 4:
                    lt = []
                    lt.append(a[1])
                    lt.append(a[2])
                    for node in lt:
                        pcs_node = msg_pds.PcsNode()
                        pcs_node.node_name = node
                        pcs_node.node_status = "offline"
                        pcs_info.pcs_nodes.add().CopyFrom(pcs_node)
                else:
                    pcs_node = msg_pds.PcsNode()
                    pcs_node.node_name = a[1]
                    pcs_node.node_status = "offline"
                    pcs_info.pcs_nodes.add().CopyFrom(pcs_node)

            if line.split(':')[0].strip() == "corosync":
                pcs_info.corosync_status = line.split(':')[1].strip()
            if line.split(':')[0].strip() == "pacemaker":
                pcs_info.pacemaker_status = line.split(':')[1].strip()
            
        cmd_str = "%s config show" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        for line in out.splitlines():
            if line.split(':')[0].strip() == "stonith-enabled":
                pcs_info.stonith_enabled = line.split(':')[1].strip()
        return 0,pcs_info

