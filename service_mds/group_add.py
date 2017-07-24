# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, uuid
from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class GroupAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GROUP_ADD_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.GROUP_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.group_add_request]
    
        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        if self.request_body.HasField('group_name'):
            group_name = self.request_body.group_name
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Not find params group_name"
            self.SendResponse(self.response)
            return MS_FINISH

        for group_info in g.group_list.groups:
            if group_name == group_info.group_name:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Group %s already configured" % group_name
                self.SendResponse(self.response)
                return MS_FINISH
        
        data = {}
        data.update({"group_name":group_name})
        data.update({"node_uuids":[]})
        e, _ = dbservice.srv.create("/group_list/%s"%group_name, data)
        if e:
            logger.run.error("Create node list faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        
        # 同配置文件全局更新
        lst = g.group_list.groups.add()
        lst.group_name = group_name
        
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
