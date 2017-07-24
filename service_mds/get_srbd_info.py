# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

SRBDADM = "/usr/sbin/drbdadm"

class GetSrbdInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GET_SRBD_INFO_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.GET_SRBD_INFO_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.get_srbd_info_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        e,res = self.srbd_info()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH

        for srbd_info in res:
            self.response.body.Extensions[msg_mds.get_srbd_info_response].srbd_infos.add().CopyFrom(srbd_info)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    # 获取srbd conf信息和srbd状态信息
    def srbd_info(self):
        srbd_infos = []
        srbd_status = {} 
        try:
            node2_name  = config.safe_get('node2', 'node2_hostname')
            srbd_status['node2_name'] = node2_name
        except:
            pass 
        cmd_str = "%s status r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            pass 
        else:
            for line in out.splitlines():
                out = re.search(r'(r0 role:)(.*)', line)
                if out:
                    srbd_status['node1_role'] = out.group(2).strip().split()[0]
                out = re.search(r'(  disk:)(.*)',line)
                if out:
                    srbd_status['node1_disk'] = out.group(2).strip().split()[0]
                if srbd_status.has_key('node2_name'):
                    out = re.search(node2_name + " role:(.*)",line)
                    if out:
                        srbd_status['node2_role'] = out.group(1).split()[0]
                    out = re.search(node2_name + " connection:(.*)",line)
                    if out:
                        srbd_status['node2_con'] = out.group(1).split()[0]

                out = re.search(r'.*(replication:)(.*)',line)
                if out:
                    srbd_status['node1_con'] = out.group(2).strip().split()[0]
                out = re.search(r'.*(peer-disk:)(.*)',line)
                if out:
                    srbd_status['node2_disk'] = out.group(2).strip().split()[0]

	    if not srbd_status.has_key('node1_disk') or not srbd_status.has_key('node2_disk'):
                cmd_str = "%s dstate r0" % SRBDADM
                e,out = command(cmd_str)
                if e:
                    pass
                else:
                    a = out.split('/')
                    if len(a) == 2:
                        srbd_status['node1_disk'] = out.split('/')[0]
                        srbd_status['node2_disk'] = out.split('/')[1]
                    else:
                        srbd_status['node1_disk'] = out.split('/')[0]
                        srbd_status['node2_disk'] = "DUnknown"
                       
	    if not srbd_status.has_key('node1_con'):
                cmd_str = "%s cstate r0" % SRBDADM
                e,out = command(cmd_str)
                if e:
                    pass
                else:
                    srbd_status['node1_con'] = out.strip()
        
        if not os.path.exists(g.srbd_conf):
            return 1,"%s not found" % g.srbd_conf
        srbd_info = msg_pds.SrbdInfo()
        if srbd_status.has_key('node1_role'):
            srbd_info.role_status   = srbd_status['node1_role']
        if srbd_status.has_key('node1_con'):
            srbd_info.con_status   = srbd_status['node1_con']
        if srbd_status.has_key('node1_disk'):
            srbd_info.disk_status   = srbd_status['node1_disk']
        srbd_info.node_type         = "node1"
        srbd_info.node_srbd_ip      = config.safe_get('node1', 'node1_srbd_ip')
        srbd_info.node_srbd_name    = config.safe_get('node1', 'node1_hostname')
        srbd_info.node_srbd_netmask = config.safe_get('node1', 'node1_srbd_mask')
        srbd_info.node_srbd_netcard = config.safe_get('node1', 'node1_srbd_netcard')
        srbd_info.node_ipmi_ip      = config.safe_get('node1', 'node1_ipmi_ip')
        srbd_infos.append(srbd_info)

        srbd_info = msg_pds.SrbdInfo()
        if srbd_status.has_key('node2_role'):
            srbd_info.role_status   = srbd_status['node2_role']
        if srbd_status.has_key('node2_con'):
            srbd_info.con_status   = srbd_status['node2_con']
        if srbd_status.has_key('node2_disk'):
            srbd_info.disk_status   = srbd_status['node2_disk']
        if srbd_status.has_key('node2_name'):
            srbd_info.node_srbd_name   = srbd_status['node2_name']
        srbd_info.node_type         = "node2"
        srbd_info.node_srbd_ip      = config.safe_get('node2', 'node2_srbd_ip')
        srbd_info.node_ipmi_ip      = config.safe_get('node2', 'node2_ipmi_ip')
        srbd_infos.append(srbd_info)

        return 0,srbd_infos

