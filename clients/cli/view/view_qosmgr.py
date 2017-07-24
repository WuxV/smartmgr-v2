# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewQosMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # QoS list
    def cli_list(self, request, response):
        out    = []
        for template_info in response.body.Extensions[msg_mds.get_qos_template_list_response].qos_template_infos:
            info = {}
            info["qos_name"] = template_info.template_name

            qos_info = template_info.qos_info
            info["read-bps"]   = qos_info.read_bps
            info["write-bps"]  = qos_info.write_bps
            info["read-iops"]  = qos_info.read_iops
            info["write-iops"] = qos_info.write_iops

            out.append(info)

        tbl_th  = ['Qos Name', 'read-bps', 'write-bps', 'read-iops', 'write-iops']
        tbl_key = ['qos_name', 'read-bps', 'write-bps', 'read-iops', 'write-iops']

        return self.common_list(tbl_th, tbl_key, idx_key='qos_name', data=out, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # QoS add
    def cli_add(self, request, response):
        return "success : add qos '%s' success" % request.body.Extensions[msg_mds.qos_template_add_request].template_name

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("error [%s]: %s!" % (retcode, message))

    # QoS drop
    def cli_drop(self, request, response):
        return "success : drop qos '%s' success" % request.body.Extensions[msg_mds.qos_template_drop_request].template_name

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("error [%s]: %s!" % (retcode, message))

    # QoS update
    def cli_update(self, request, response):
        return "success : update qos '%s' success" % request.body.Extensions[msg_mds.qos_template_update_request].template_name

    def cli_update_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("error [%s]: %s!" % (retcode, message))

    # QoS link
    def cli_link(self, request, response):
        return "success : link qos '%s' success" % request.body.Extensions[msg_mds.link_qos_template_request].template_name

    def cli_link_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("error [%s]: %s!" % (retcode, message))

    # QoS unlink
    def cli_unlink(self, request, response):
        return "success : unlink lun '%s' with QoS success" % request.body.Extensions[msg_mds.unlink_qos_template_request].lun_name

    def cli_unlink_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("error [%s]: %s!" % (retcode, message))

