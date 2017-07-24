# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewLunMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # Lun list
    def cli_list_node(self,request, response):
        out    = []
        for lun_info in response.body.Extensions[msg_mds.get_lun_list_response].lun_infos:
            info = {}
            info["lun_name"]        = "%s_%s" % (lun_info.Extensions[msg_mds.ext_luninfo_node_name], lun_info.lun_name)
            info["lun_id"]          = lun_info.lun_id
            info["node_index"]      = "|".join(lun_info.node_index)
            out.append(info)
        tbl_th  = ['Lun Name','Lun For Node']
        tbl_key = ['lun_name','node_index']

        return self.common_list(tbl_th, tbl_key, idx_key='lun_name', data=out, count=True)

    def cli_list(self, request, response):
        out    = []
        e_flag = False
        for lun_info in response.body.Extensions[msg_mds.get_lun_list_response].lun_infos:
            info = {}
            info["lun_name"]        = "%s_%s" % (lun_info.Extensions[msg_mds.ext_luninfo_node_name], lun_info.lun_name)
            info["lun_id"]          = lun_info.lun_id
            info['qos_name']        = lun_info.qos_template_name
            info['size']            = lun_info.Extensions[msg_mds.ext_luninfo_size]
            info['scsiid']          = lun_info.Extensions[msg_mds.ext_luninfo_scsiid]
            info['data_disk_name']  = lun_info.Extensions[msg_mds.ext_luninfo_data_disk_name]
            info['data_dev_name']   = lun_info.Extensions[msg_mds.ext_luninfo_data_dev_name]
            info['data_dev']        = "%s(%s)" % (info['data_disk_name'], info['data_dev_name']=="" and "--" or info['data_dev_name'])
            info['io_error']        = lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].io_error
            info['last_errno']      = lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].last_errno
            info['data_actual_state'] = lun_info.Extensions[msg_mds.ext_luninfo_data_actual_state]
            info['cache_actual_state'] = lun_info.Extensions[msg_mds.ext_luninfo_cache_actual_state]
            info['error']           = info['io_error']
            if lun_info.config_state == True and lun_info.actual_state == True:
                if lun_info.asm_status:
                    info['state'] = lun_info.asm_status
                else:
                    info['state'] = "ONLINE"
                if lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].io_error != 0:
                    info['state'] = "FAULTY"
                    e_flag = True
                if info['data_actual_state'] == False or False in info['cache_actual_state']:
                    info['state'] = "FAULTY"
                    e_flag = True

            if lun_info.config_state == True and lun_info.actual_state == False:
                info['state'] = "MISSING"
            if lun_info.config_state == False:
                info['state'] = "OFFLINE"

            if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                info['lun_type']   = "BASEDISK"
                info['cache_size'] = "--"
                info['cache_dev']  = "--"
            elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
                info['lun_type']   = "BASEDEV"
                info['cache_size'] = "--"
                info['cache_dev']  = "--"
                info['data_dev']   = info['data_dev_name']=="" and "--" or info['data_dev_name'].split('/')[-1]
            elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
                info['lun_type']   = "SMARTCACHE"
                info['cache_size']      = lun_info.Extensions[msg_mds.ext_luninfo_cache_size]
                info['cache_disk_name'] = lun_info.Extensions[msg_mds.ext_luninfo_cache_disk_name]
                info['cache_dev_name']  = lun_info.Extensions[msg_mds.ext_luninfo_cache_dev_name][0]
                info['cache_dev']       = "%s(%s)" % (info['cache_disk_name'], info['cache_dev_name']=="" and "--" or info['cache_dev_name'])
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                info['lun_type']        = "PAL-CACHE(--)"
                info['cache_disk_name'] = lun_info.Extensions[msg_mds.ext_luninfo_cache_disk_name]
                info['cache_dev_name']  = lun_info.Extensions[msg_mds.ext_luninfo_cache_dev_name][0]
                info['cache_dev']       = "%s(%s)" % (info['cache_disk_name'], info['cache_dev_name']=="" and "--" or info['cache_dev_name'])
                info['cache_size']      = lun_info.Extensions[msg_mds.ext_luninfo_cache_size]
                if lun_info.HasExtension(msg_mds.ext_luninfo_palcache_cache_model):
                    if lun_info.Extensions[msg_mds.ext_luninfo_palcache_cache_model] == msg_pds.PALCACHE_CACHE_MODEL_WRITEBACK:
                        info['lun_type']   = "PAL-CACHE(WB)"
                    elif lun_info.Extensions[msg_mds.ext_luninfo_palcache_cache_model] == msg_pds.PALCACHE_CACHE_MODEL_WRITETHROUGH:
                        info['lun_type']   = "PAL-CACHE(WT)"
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                info['lun_type']        = "PAL-RAW"
                info['cache_disk_name'] = "--"
                info['cache_dev_name']  = "--"
                info['cache_dev']       = "--"
                info['cache_size']      = "--"
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
                info['lun_type']        = "PAL-PMT"
                info['cache_disk_name'] = "--"
                info['cache_dev_name']  = "--"
                info['cache_dev']       = "--"
                info['cache_size']      = "--"
                info['size']            *= (1.0*1000/1024)**3
            else:
                assert(0)
            info['device_name'] = lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].filename
            info['group_name'] = "|".join(lun_info.group_name)
            out.append(info)

        formats = {}
        formats['size'] = {}
        formats['size']['fun'] = "disk_size_sector"
        formats['size']['params'] = {'cl':True}
        formats['cache_size'] = {}
        formats['cache_size']['fun'] = "disk_size_sector"
        formats['cache_size']['params'] = {'cl':True}
        formats['state'] = {}
        formats['state']['fun'] = "lun_state"
        formats['state']['params'] = {'cl':True}
        formats['data_dev'] = {}
        formats['data_dev']['fun'] = "lun_dev_name"
        formats['data_dev']['params'] = {'cl':True}

        tbl_th  = ['Lun Name', 'Lun Type', 'Size', 'Cache',      'Data Dev', 'Cache Dev', 'Device',      'State', 'QoS', 'Group']
        tbl_key = ['lun_name', 'lun_type', 'size', 'cache_size', 'data_dev', 'cache_dev', 'device_name', 'state', 'qos_name', 'group_name']
        if e_flag == True:
            tbl_th.extend( ['IO Error'])
            tbl_key.extend(['error'])

        return self.common_list(tbl_th, tbl_key, idx_key='lun_name', data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun add
    def cli_add(self, request, response):
        return "Success : add lun success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun drop
    def cli_drop(self, request, response):
        drop_success = response.body.Extensions[msg_mds.lun_drop_response].drop_success
        if drop_success:
            return "Success : drop lun success"
        else:
            return "Success : drop lun is running"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun online
    def cli_online(self, request, response):
        return "Success : online lun success"

    def cli_online_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun config
    def cli_config(self, request, response):
        if request.body.Extensions[msg_mds.lun_config_request].del_group:
            return "Success :delete config lun success"
        return "Success : config lun success"

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun offline
    def cli_offline(self, request, response):
        return "Success : offline lun success"

    def cli_offline_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun active
    def cli_active(self, request, response):
        return "Success : active lun is running"

    def cli_active_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Lun inactive
    def cli_inactive(self, request, response):
        return "Success : inactive lun success"

    def cli_inactive_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
