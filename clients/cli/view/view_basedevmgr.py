# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewBaseDevMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    def cli_list(self, request, response):
        out  = []
        formats = {}

        for basedev_info in response.body.Extensions[msg_mds.get_basedev_list_response].basedev_infos:
            info = {}
            info['basedev_id'] = basedev_info.basedev_id
            info['dev_name']   = basedev_info.dev_name
            info['size']       = basedev_info.size
            out.append(info)

        tbl_th  = ['basedev_id', 'dev_name', 'size']
        tbl_key = ['basedev_id', 'dev_name', 'size']
        return self.common_list(tbl_th, tbl_key, data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
