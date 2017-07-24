# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_basediskmgr import ViewBaseDiskMgr
import message.mds_pb2 as msg_mds
from pdsframe import *

class BaseDiskMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['basedisk']
        self.view = ViewBaseDiskMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_BASEDISK_LIST_REQUEST)
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)
