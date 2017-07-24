# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_targetmgr import ViewTargetMgr
import message.mds_pb2 as msg_mds
from pdsframe import *

class TargetMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['target']
        self.view = ViewTargetMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        if not params.has_key('type') or params['type'].lower() not in ['cache', 'raw']:
            return self.view.params_error("Miss target type parameter or type parameter illegal, support cache/raw")

        if params['type'].lower() == "cache":
            request = MakeRequest(msg_mds.GET_PALCACHE_LIST_REQUEST)
        else:
            request = MakeRequest(msg_mds.GET_PALRAW_LIST_REQUEST)

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)

        if params['type'].lower() == "cache":
            return self.view.cli_list_cache(request, response)
        else:
            return self.view.cli_list_raw(request, response)
