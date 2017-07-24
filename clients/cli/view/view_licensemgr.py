# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewLicenseMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # License info
    def cli_info(self, request, response):
        kvs = response.body.Extensions[msg_mds.get_license_info_response].kvs
        out  = []
        for kv in kvs:
            out.append({"key":"%s" % kv.key, 'value':kv.value})

        tbl_th  = ['Key', 'Value']
        tbl_key = ['key', 'value']
        return self.common_list(tbl_th, tbl_key, idx_key='key', data=out)

    def cli_info_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
