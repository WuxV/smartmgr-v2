# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewPoolMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # Pool info
    def cli_info(self, request, response, pool_name):
        out = []
        for pool_info in response.body.Extensions[msg_mds.get_pool_list_response].pool_infos:
            if pool_info.pool_name != pool_name:
                continue
            out.append({"key":"Pool Name",   'value':pool_info.pool_name})
            out.append({"key":"Pool ID",     'value':pool_info.pool_id})
            out.append({"key":"State",       'value':pool_info.actual_state == True and "ONLINE" or "MISSING"})
            out.append({"key":"Length Mode", 'value':pool_info.is_variable == True and "variable" or "fixed"})
            out.append({"key":"Extent",      'value':self.format_disk_size_sector(pool_info.extent)})
            out.append({"key":"Bucket",      'value':"%sM" % (pool_info.bucket*512>>20)})
            out.append({"key":"Sippet",      'value':"%sK" % (pool_info.sippet*512>>10)})

        if out == []:
            return self.out_error("Error [%s]: Pool '%s' not exist!" % (msg_mds.RC_MDS_POOL_NOT_EXIST, pool_name))

        tbl_th  = ['Key', 'Value']
        tbl_key = ['key', 'value']
        return self.common_list(tbl_th, tbl_key, data=out)

    def cli_info_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool list
    def cli_list(self, request, response):
        out    = []
        e_flag = False
        for pool_info in response.body.Extensions[msg_mds.get_pool_list_response].pool_infos:
            info = {}
            info["pool_id"]     = pool_info.pool_id
            info["pool_name"]   = pool_info.pool_name
            pool_disk_info      = pool_info.pool_disk_infos[0] 
            info['size']        = "--"
            info['skip_thresh'] = "%sK" % pool_info.skip_thresh
            info['sync_level']  = pool_info.sync_level
            info['dev_name']    = pool_disk_info.Extensions[msg_mds.ext_pool_disk_info_dev_name]
            info['disk_name']   = pool_disk_info.Extensions[msg_mds.ext_pool_disk_info_disk_name]
            info['disk']        = "%s(%s)" % (info['disk_name'], info['dev_name']=="" and "--" or info['dev_name'])
            if pool_info.is_variable == True:
                info['length_mode'] = "variable"
            else:
                info['length_mode'] = "fixed"
            pool_cache_model = pool_info.Extensions[msg_mds.ext_poolinfo_pool_cache_model]
            info['cache_model'] = "--"
            if pool_cache_model == msg_pds.POOL_CACHE_MODEL_WRITEBACK:
                info['cache_model'] = "write-back"
            elif pool_cache_model == msg_pds.POOL_CACHE_MODEL_WRITETHROUGH:
                info['cache_model'] = "write-through"
            elif pool_cache_model == msg_pds.POOL_CACHE_MODEL_MIX:
                info['cache_model'] = "mix"

            if pool_info.actual_state == False:
                info['state'] = "MISSING"
                if pool_info.is_disable == True:
                    info['state'] = "DISABLE"
            if pool_info.actual_state == True :
                info['state'] = "ONLINE"
                state_exp = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].state_exp
                if state_exp != "":
                    info['state'] = "%s|%s" % (info['state'], state_exp)
                size                 = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].size
                max_size             = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].max_size
                pmt_size             = pool_info.Extensions[msg_mds.ext_poolinfo_pool_pmt_size]
                info['size']         = (size*512)>>30
                info['pmt_size']     = (pmt_size*512)>>30
                info['max_size']     = (max_size*512)>>30
                if info['max_size'] != 0:
                    info['info_size'] = "%sG/%sG/%sG" % (info['size'], info['pmt_size'], info['max_size']-info['size']-info['pmt_size'])
                else:
                    info['info_size'] = "%sG/%sG/--"  % (info['size'], info['pmt_size'])
                info['s_dirty_nr']   = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].dirty
                info['s_p_dirty']    = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].p_dirty
                info['s_dirty']      = "%.2f%%" % info['s_p_dirty']
                info['s_valid_nr']   = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].valid
                info['s_p_valid']    = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].p_valid
                info['s_valid']      = "%.2f%%" % info['s_p_valid']
                info['s_error']      = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].error
                info['state_str']    = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].state_str
                if info['s_error'] != 0:
                    e_flag = True

                p_lower_thresh = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].p_lower_thresh
                p_upper_thresh = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].p_upper_thresh
                info['a_dirty_thresh'] = "%s%%/%s%%" % (p_lower_thresh, p_upper_thresh)
                if pool_info.HasField('dirty_thresh'):
                    p_lower_thresh = pool_info.dirty_thresh.lower
                    p_upper_thresh = pool_info.dirty_thresh.upper
                    info['dirty_thresh'] = "%s%%/%s%%" % (p_lower_thresh, p_upper_thresh)
                else:
                    info['dirty_thresh'] = info['a_dirty_thresh']
            out.append(info)

        formats = {}
        formats['state'] = {}
        formats['state']['fun']    = "pool_online_state"
        formats['state']['params'] = {'cl':True}
        formats['disk'] = {}
        formats['disk']['fun']    = "pool_dev_name"
        formats['disk']['params'] = {'cl':True}

        tbl_th  = ['Name',      'Cache/Pmt/Free', 'Disk', 'Cache Model', 'Sync Level', 'Skip-THR',    'Dirty-THR L/U', 'Dirty',   'Valid',   'Len Mode', 'State']
        tbl_key = ['pool_name', 'info_size',      'disk', 'cache_model', 'sync_level', 'skip_thresh', 'dirty_thresh',  's_dirty', 's_valid', 'length_mode', 'state']

        if self.detail == True:
            tbl_th.extend( ['a_dirty_thresh', 'is_invalid', 'is_disable', 'state_str'])
            tbl_key.extend(['a_dirty_thresh', 'is_invalid', 'is_disable', 'state_str'])

        if e_flag == True:
            tbl_th.extend( ['Error I/O'])
            tbl_key.extend(['s_error'])

        return self.common_list(tbl_th, tbl_key, idx_key='pool_name', data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool add
    def cli_add(self, request, response):
        return "Success : add pool success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool drop
    def cli_drop(self, request, response):
        return "Success : drop pool success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool config
    def cli_config(self, request, response):
        return "Success : config pool success"

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool disable
    def cli_disable(self, request, response):
        return "Success : disabel pool success"

    def cli_disable_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool rebuild
    def cli_rebuild(self, request, response):
        return "Success : rebuild pool success"

    def cli_rebuild_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Pool resize
    def cli_resize(self, request, response):
        return "Success : resize pool success"

    def cli_resize_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
