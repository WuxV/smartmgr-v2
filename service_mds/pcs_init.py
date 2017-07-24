# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

PCS = "/usr/sbin/pcs"
COROSYNC_CONF = "/etc/corosync/corosync.conf"

class PcsInitMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.PCS_INIT_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.PCS_INIT_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.pcs_init_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        e,res = self.pcs_init()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_PCS_INIT_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH       

    # 读取配置文件中的内容,配置pcs需要4个参数,node1_name,node1_impi_ip ,node2_name,node2_impi_ip,配置pcs的资源文件，
    def pcs_init(self):
        node1_name    = config.safe_get('node1', 'node1_hostname')
        node2_ipmi_ip = config.safe_get('node2', 'node2_ipmi_ip')
        try:
            node2_name    = config.safe_get('node2', 'node2_hostname')
        except:
            node2_srbd_ip = config.safe_get('node2', 'node2_srbd_ip')
            e, res = common.config_nodename(node2_srbd_ip)
            if e:
                return e, res
            else:
                node2_name    = config.safe_get('node2', 'node2_hostname')

        node1_name_priv = str(node1_name + "-priv")
        node2_name_priv = str(node2_name + "-priv")
        if not os.path.exists(COROSYNC_CONF):
            cmd_str = "%s cluster auth %s %s -u hacluster -p root123" % (PCS, node1_name_priv, node2_name_priv)
            e,out = command(cmd_str)
            if e:
                return e,out
            cmd_str = "%s cluster setup --start --name srbd_cluster %s %s --force" % (PCS, node1_name_priv, node2_name_priv)
            e,out = command(cmd_str)
            if e:
                return e,out
            cmd_str = "%s cluster enable --all" % PCS
            e,out = command(cmd_str)
            if e:
                return e,out
        cmd_str = "%s property set stonith-enabled=true" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out

        e, stonith_infos = common.stonith_info()
        if e:
            return e, stonith_infos
        found = 0
        stonith_name = "%s_fence" % node1_name 
        for stonith_info in stonith_infos:
            if str(stonith_name) == str(stonith_info['stonith_name']):
                found = 1
                break
        if found == 1:
            return 1, "%s stonith already exists" % stonith_name

        # 创建stonith设备
        # pcs stonith create dntohu002_fence fence_ipmilan ipaddr=172.16.9.207 passwd=root123  login=root action=reboot pcmk_host_list=dntohu001
        cmd_str = "pcs stonith create %s fence_ipmilan ipaddr=\"%s\" passwd=\"root123\"  login=\"root\"  \
        action=\"reboot\" pcmk_host_list=%s "% (stonith_name, node2_ipmi_ip, node2_name_priv)
        e,out = command(cmd_str)
        if e:
            return e,out

        return 0,"pcs init success"
