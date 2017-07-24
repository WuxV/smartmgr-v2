# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

SRBDADM = "/usr/sbin/drbdadm"
#SRBD_INIT_SH = "../files/scripts/set_conf.sh"
#INIT_SRBD_SH = "../files/scripts/init_srbd.sh"
SRBD_INIT_SH = "/opt/smartmgr/scripts/set_conf.sh"
INIT_SRBD_SH = "/opt/smartmgr/scripts/init_srbd.sh"

class SrbdInitMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SRBD_INIT_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.SRBD_INIT_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.srbd_init_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        e,res = self.init_conf()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_SRBD_INIT_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        e,res = self.init_srbd()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_SRBD_INIT_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        e,res = self.start_srbd()
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_SRBD_INIT_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH       

        # 初始化srbd的配置文件,及相关配置信息 
    def init_conf(self):
        node1_srbd_ip      = config.safe_get('node1', 'node1_srbd_ip')
        node1_name         = config.safe_get('node1', 'node1_hostname')
        node1_srbd_mask    = config.safe_get('node1', 'node1_srbd_mask')
        node1_srbd_netcard = config.safe_get('node1', 'node1_srbd_netcard')
        node2_srbd_ip      = config.safe_get('node2', 'node2_srbd_ip')
        node2_passwd       = config.safe_get('node2', 'node2_passwd') 

        e, out = command(SRBD_INIT_SH  + ' ' + node1_srbd_ip + ' ' + node1_srbd_mask + ' ' +node1_name + ' ' + \
        node1_srbd_netcard + ' ' + node2_srbd_ip + ' ' +  node2_passwd)
        if e:
            return e,out            
        e, res = common.config_nodename(node2_srbd_ip)
        if e:
            return e, res
        return 0,"success"
              
        # 初始化srbd的元数据,如果srbd磁盘挂载，先卸载      
    def init_srbd(self):
        e, out = common._umount()
        if e:
            return e,out
        cmd_str = "%s down r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
             return e,out
        e,out = command(INIT_SRBD_SH)
        if e:
            return e,out
        return 0,"success" 

        # 启动srbd服务并设置该节点为主节点
    def start_srbd(self):
        cmd_str = "%s up r0" % SRBDADM
        e,out = command(cmd_str)
        if e:
            if re.search(r'(.*)Device(.*)is configured(.*)',out):
                cmd_str = "%s down r0" % SRBDADM
                e,out = command(cmd_str)
                if e:
                     return e,out
                cmd_str = "%s up r0" % SRBDADM
                e,out = command(cmd_str)
                if e:
                     return e,out
            else:
                return e,out
        return 0," srbd init success"
