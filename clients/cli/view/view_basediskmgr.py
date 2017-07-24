# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewBaseDiskMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    def cli_list(self, request, response):
        out  = []
        formats = {}

        for basedisk_info in response.body.Extensions[msg_mds.get_basedisk_list_response].basedisk_infos:
            info = {}
            info['basedisk_id'] = basedisk_info.basedisk_id
            info['disk_id']     = basedisk_info.disk_id
            info['disk_part']   = basedisk_info.disk_part
            out.append(info)

        tbl_th  = ['basedisk_id', 'disk_id', 'disk_part']
        tbl_key = ['basedisk_id', 'disk_id', 'disk_part']
        return self.common_list(tbl_th, tbl_key, data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
