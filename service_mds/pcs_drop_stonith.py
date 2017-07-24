# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

PCS = "/usr/sbin/pcs"

class PcsDropStonithMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.PCS_DROP_STONITH_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.PCS_DROP_STONITH_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.pcs_drop_stonith_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        stonith_name = self.request_body.stonith_name
        e,res = self.pcs_drop_stonith(stonith_name)
        if e:
            self.response.rc.retcode = msg_mds.RC_MDS_PCS_DROP_STONITH_FAILED
            self.response.rc.message = "%s" % res
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH       

    def stonith_info(self):
        stonith_infos = []
        cmd_str = "%s stonith" % PCS
        e,out = command(cmd_str)
        if e:
            return e,out
        for line in out.splitlines():
            stonith_info = {}
            st = line.split()
            stonith_info['stonith_name'] = st[0]
            stonith_info['stonith_status'] = st[-1]
            stonith_infos.append(stonith_info)
        return 0, stonith_infos

    def pcs_drop_stonith(self, stonith_name):
        # 先判读stonith id 是否存在，再判断stonith的状态，stopped可上删除, startd不可删除
        e, stonith_infos = self.stonith_info()
        if e:
            return e, stonith_infos
        found = 0
        status = None
        for stonith_info in stonith_infos:
            if str(stonith_name) == str(stonith_info['stonith_name']):
                found = 1
                status = stonith_info['stonith_status']
                break
        if found == 0:
            return 1, "%s not exists" % stonith_name
        cmd_str = "%s stonith delete %s" % (PCS, stonith_name)
        e,out = command(cmd_str)
        if e:
            return e,out
        return 0,"pcs drop stonith success"
