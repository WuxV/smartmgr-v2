# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewASMDiskMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # ASMDisk list
    def cli_list(self, request, response):
        out    = []
        for asmdisk_info in response.body.Extensions[msg_mds.get_asmdisk_list_response].asmdisk_infos:
            info = {}
            info["asmdisk_name"]   = asmdisk_info.asmdisk_name
            info["asmdisk_id"]     = asmdisk_info.asmdisk_id
            info["diskgroup_id"]   = asmdisk_info.diskgroup_id
            info["path"]           = asmdisk_info.path
            info["mode_status"]    = asmdisk_info.mode_status
            info["state"]          = asmdisk_info.state
            info["failgroup"]      = asmdisk_info.failgroup
            info["total_mb"]       = asmdisk_info.total_mb
            info["free_mb"]        = asmdisk_info.free_mb
            info['idx_key']        = info["diskgroup_id"] + info["path"]

            out.append(info)

        tbl_th  = ['ASMDisk Name', 'ASMDisk ID', 'Diskgroup ID', 'Path', 'Mode Status', 'State', 'Failgroup', 'Total MB', 'Free MB']
        tbl_key = ['asmdisk_name', 'asmdisk_id', 'diskgroup_id', 'path', 'mode_status', 'state', 'failgroup', 'total_mb', 'free_mb']

        return self.common_list(tbl_th, tbl_key, idx_key='idx_key', data=out, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # ASMDisk add
    def cli_add(self, request, response):
        return "Success : add asmdisk success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # ASMDisk drop
    def cli_drop(self, request, response):
        return "Success : drop asmdisk success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # ASMDisk online
    def cli_online(self, request, response):
        return "Success : online asmdisk is running"

    def cli_online_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # ASMDisk offline
    def cli_offline(self, request, response):
        return "Success : offline asmdisk success"

    def cli_offline_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
