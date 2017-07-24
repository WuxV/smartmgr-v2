# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_licensemgr import ViewLicenseMgr
import message.mds_pb2 as msg_mds
from pdsframe import *

class LicenseMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['license']
        self.view = ViewLicenseMgr(self.srv)    # 注册视图类

    def cli_info(self, params = {}):
        request = MakeRequest(msg_mds.GET_LICENSE_INFO_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_info_error(request, response)
        return self.view.cli_info(request, response)
