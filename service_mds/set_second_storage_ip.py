# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class SetSecondStorageIpMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.SET_SECOND_STORAGE_IP_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.SET_SECOND_STORAGE_IP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.set_second_storage_ip_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        found = False
        node_list = g.nsnode_list.nsnode_infos
        for node in node_list:
            if node.listen_ip == self.request_body.second_storage_ip: 
                found = True

        if found == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SET_STORAGE_IP_FAIL
            self.response.rc.message = "%s ip can't set" % self.request_body.second_storage_ip
            self.SendResponse(self.response)
            return MS_FINISH

        is_file_dir = os.path.dirname(g.second_storage_ip_file)
        if not os.path.isdir(is_file_dir):
            os.makedirs(ip_file_dir)
        try:
            with open(g.second_storage_ip_file,'wb') as f:
                f.write(self.request_body.second_storage_ip)
            f.close()
            g.second_storage_ip = self.request_body.second_storage_ip 
            self.response.rc.retcode = msg_pds.RC_SUCCESS
        except:
            self.response.rc.retcode = msg_mds.RC_MDS_SET_STORAGE_IP_FAIL
            self.response.rc.message = "set storage ip %s faild" % self.request_body.second_storage_ip
        self.SendResponse(self.response)
        return MS_FINISH
