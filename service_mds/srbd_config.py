# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import re
from pdsframe import *
from pdsframe.common import dbclient
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

SRBDADM = "/usr/sbin/drbdadm"

class SrbdConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SRBD_CONFIG_REQUEST
    
    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.SRBD_CONFIG_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.srbd_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.HasField("node_role"):            
            node_role = self.request_body.node_role
            e, res = self.set_role(node_role)
            if e:
                self.response.rc.retcode = msg_mds.RC_MDS_SRBD_CONFIG_FAILED
                self.response.rc.message = "%s" % res
                self.SendResponse(self.response)
                return MS_FINISH
            self.response.rc.retcode = msg_pds.RC_SUCCESS
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH       

        elif self.request_body.HasField("node_action"):            
             node_action = self.request_body.node_action
             e, res = self.node_action(node_action)
             if e:
                 self.response.rc.retcode = msg_mds.RC_MDS_SRBD_CONFIG_FAILED
                 self.response.rc.message = "%s" % res
                 self.SendResponse(self.response)
                 return MS_FINISH
             self.response.rc.retcode = msg_pds.RC_SUCCESS
             self.response.rc.message = "%s" % res
             self.SendResponse(self.response)
             return MS_FINISH       

        elif self.request_body.HasField("srbd_config"):
            srbd_config = self.request_body.srbd_config
            try:
                config.safe_set(srbd_config.nodeid,srbd_config.srbd_key,srbd_config.srbd_value) 
            except Exception as e:
                self.response.rc.retcode = msg_mds.RC_MDS_SRBD_CONFIG_FAILED
                self.response.rc.message = "config set failed"
                self.SendResponse(self.response)
                return MS_FINISH
            e, res = common.write_config(config, g.srbd_conf) 
            if e:
                self.response.rc.retcode = msg_mds.RC_MDS_SRBD_CONFIG_FAILED
                self.response.rc.message = "%s" % res
                self.SendResponse(self.response)
            self.response.rc.retcode = msg_pds.RC_SUCCESS
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH       

    # 设置srbd角色信息 primary/secondary
    def set_role(self, node_role):
        if node_role == "primary":
            cmd_str = "%s primary --force r0" % SRBDADM
            e,out = command(cmd_str)
            if e:
                 return e,out
            return 0, "set %s role success" % node_role
        elif node_role == "secondary":
            cmd_str = "%s secondary r0" % SRBDADM
            e,out = command(cmd_str)
            if e:
                 return e,out
            return 0, "set %s role success" % node_role
        else:
             return 1, "%s parameter failed" % node_role

   # 打开srbd服务
    def srbd_online(self):
        cmd_str = "%s up r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'(.*)Device(.*)is configured(.*)',out):
                return 1,"srbd is already online"
            else:
                return e,out
        return 0,"srbd online success"

    # 关闭srbd时，需要检查是否挂载资源
    def srbd_offline(self):
        e, out = common._umount()
        if e:
            return e, out
        cmd_str = "%s down r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'.*(unknown connection).*',out):
                pass
            else:
                return e,out
        return 0,"srbd offline success"

    # 断开srbd连接时，需要检查是否挂载资源
    def srbd_disconnect(self):
        e, out = common._umount()
        if e:
            return e,out
        cmd_str = "%s disconnect r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'.*(unknown connection).*',out):
                pass
            else:
                return e,out
        return 0,"srbd disconnect success"

    # 连接srbd资源
    def srbd_connect(self):
        cmd_str = "%s connect r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'.*(Failure).*(Local address\(port\) already in use).*',out):
                pass
            else:
                return e,out
        return 0,"srbd connnect success"

    def node_action(self, node_action):
        if node_action == "on":
            return self.srbd_online()
        elif node_action == "off":
            return self.srbd_offline()
        elif node_action == "disconnect":
            return self.srbd_disconnect() 
        elif node_action == "connect":
            return self.srbd_connect()
        else:
            return 1,"action not 'on off disconnect connect'"

