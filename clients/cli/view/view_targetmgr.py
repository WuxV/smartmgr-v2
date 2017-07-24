# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewTargetMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    def cli_list_cache(self, request, response):
        out  = []
        formats = {}

        for palcache_info in response.body.Extensions[msg_mds.get_palcache_list_response].palcache_infos:
            info = {}
            info['palcache_id']   = palcache_info.palcache_id
            info['palcache_name'] = palcache_info.palcache_name
            info['pool_id']     = palcache_info.pool_id
            info['disk_id']     = palcache_info.disk_id
            info['disk_part']   = palcache_info.disk_part
            info['pal_id']      = palcache_info.pal_id
            if palcache_info.actual_state == False:
                info['state'] = "MISSING"
            if palcache_info.actual_state == True :
                info['state'] = "ONLINE"
                info['mode_str']  = palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model
                info['state_str'] = palcache_info.Extensions[msg_mds.ext_palcache_export_info].state_str
                palcache_type     = palcache_info.Extensions[msg_mds.ext_palcache_export_info].type
                # palcache cache mode
                palcache_cache_model = palcache_info.Extensions[msg_mds.ext_palcache_export_info].palcache_cache_model
                if palcache_cache_model == msg_pds.TARGET_CACHE_MODEL_UNKNOWN:
                    info['mode_str'] = "unknown"
                elif palcache_cache_model == msg_pds.TARGET_CACHE_MODEL_WRITEBACK:
                    info['mode_str'] = "writeback"
                elif palcache_cache_model == msg_pds.TARGET_CACHE_MODEL_WRITETHROUGH:
                    info['mode_str'] = "writethrough"
                else:
                    assert(0)
            out.append(info)

        tbl_th  = ['palcache_name', 'palcache_id', 'pool_id', 'disk_id', 'disk_part', 'mode_str', 'state_str', 'pal_id', 'state']
        tbl_key = ['palcache_name', 'palcache_id', 'pool_id', 'disk_id', 'disk_part', 'mode_str', 'state_str', 'pal_id', 'state']
        return self.common_list(tbl_th, tbl_key, data=out, formats=formats, count=True)

    def cli_list_raw(self, request, response):
        out  = []
        formats = {}

        for palraw_info in response.body.Extensions[msg_mds.get_palraw_list_response].palraw_infos:
            info = {}
            info['palraw_id']   = palraw_info.palraw_id
            info['palraw_name'] = palraw_info.palraw_name
            info['disk_id']     = palraw_info.disk_id
            info['disk_part']   = palraw_info.disk_part
            info['pal_id']      = palraw_info.pal_id
            if palraw_info.actual_state == False:
                info['state'] = "MISSING"
            if palraw_info.actual_state == True :
                info['state'] = "ONLINE"
                info['state_str'] = palraw_info.Extensions[msg_mds.ext_palraw_export_info].state_str
            out.append(info)

        tbl_th  = ['palraw_name', 'palraw_id', 'disk_id', 'disk_part', 'state_str', 'pal_id', 'state']
        tbl_key = ['palraw_name', 'palraw_id', 'disk_id', 'disk_part', 'state_str', 'pal_id', 'state']
        return self.common_list(tbl_th, tbl_key, data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
