# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewDiskgroupMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # Diskgroup list
    def cli_list(self, request, response):
        out    = []
        for diskgroup_info in response.body.Extensions[msg_mds.get_diskgroup_list_response].diskgroup_infos:
            info = {}
            info["diskgroup_name"] = diskgroup_info.diskgroup_name
            info["diskgroup_id"]   = diskgroup_info.diskgroup_id
            info["offline_disks"]  = diskgroup_info.offline_disks
            info["type"]           = diskgroup_info.type
            info["state"]          = diskgroup_info.state
            info["total_mb"]       = diskgroup_info.total_mb
            info["free_mb"]        = diskgroup_info.free_mb
            info["usable_file_mb"] = diskgroup_info.usable_file_mb

            out.append(info)

        tbl_th  = ['Diskgroup Name', 'Diskgroup ID', 'Type', 'State', 'Offline disks', 'Total MB', 'Free MB', 'Usable File MB']
        tbl_key = ['diskgroup_name', 'diskgroup_id', 'type', 'state', 'offline_disks', 'total_mb', 'free_mb', 'usable_file_mb']

        return self.common_list(tbl_th, tbl_key, idx_key='diskgroup_id', data=out, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Diskgroup add
    def cli_add(self, request, response):
        return "Success : add asm diskgroup success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Diskgroup drop
    def cli_drop(self, request, response):
        return "Success : drop asm diskgroup success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Diskgroup config
    def cli_config(self, request, response):
        return "Success : config asm diskgroup rebalance success"

    def cli_config_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Diskgroup mount
    def cli_mount(self, request, response):
        return "Success : mount asm diskgroup success"

    def cli_mount_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Diskgroup umount
    def cli_umount(self, request, response):
        return "Success : umount asm diskgroup success"

    def cli_umount_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
