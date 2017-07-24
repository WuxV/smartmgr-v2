# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

PCS = "/usr/sbin/pcs"

class PcsConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.PCS_CONFIG_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.PCS_CONFIG_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.pcs_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.HasField("action"):            
           node_action = self.request_body.action
           e, res = self.node_action(node_action)
           if e:
               self.response.rc.retcode = msg_mds.RC_MDS_PCS_CONFIG_FAILED
               self.response.rc.message = "%s" % res
               self.SendResponse(self.response)
               return MS_FINISH
           self.response.rc.retcode = msg_pds.RC_SUCCESS
           self.response.rc.message = "%s" % res
           self.SendResponse(self.response)
           return MS_FINISH       

    # 关闭cluster
    def pcs_off(self):
        cmd_str = "%s cluster stop" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"pcs offline success"

    # 打开cluster
    def pcs_on(self):
        cmd_str = "%s cluster start --all" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"pcs online success"

    # 禁用stonith fench设备
    def stonith_disable(self):
        cmd_str = "%s property set stonith-enabled=false" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"stonith disable success"

    # 启用stonith fench设备
    def stonith_enable(self):
        cmd_str = "%s property set stonith-enabled=true" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"stonith enable success"

    def node_action(self, node_action):
        if node_action == "on":
            return self.pcs_on()
        elif node_action == "off":
            return self.pcs_off()
        elif node_action == "enable":
            return self.stonith_enable()
        elif node_action == "disable":
            return self.stonith_disable()
        else:
            return 1,"action not 'on/off enable/disable'"
