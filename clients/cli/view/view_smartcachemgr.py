# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewSmartCacheMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    def cli_list(self, request, response):
        out  = []
        formats = {}

        for smartcache_info in response.body.Extensions[msg_mds.get_smartcache_list_response].smartcache_infos:
            info = {}
            info['smartcache_id']    = smartcache_info.smartcache_id
            info['data_disk_id']     = smartcache_info.data_disk_id
            info['data_disk_part']   = smartcache_info.data_disk_part
            info['cache_disk_id']    = smartcache_info.cache_disk_id
            info['cache_disk_part']  = smartcache_info.cache_disk_part
            out.append(info)

        tbl_th  = ['smartcache_id', 'data_disk_id', 'data_disk_part', 'cache_disk_id', 'cache_disk_part']
        tbl_key = ['smartcache_id', 'data_disk_id', 'data_disk_part', 'cache_disk_id', 'cache_disk_part']
        return self.common_list(tbl_th, tbl_key, data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
