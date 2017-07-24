# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class GroupDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.GROUP_DROP_REQUEST
    
    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.GROUP_DROP_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.group_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        group_name = self.request_body.group_name
        error,self.group_info = common.GetGroupInfoFromName(group_name)
        if error:
            self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
            self.response.rc.message = "Not found group %s"% group_name
            self.SendResponse(self.response)
            return MS_FINISH
        
        found = 0
        for lun_info in g.lun_list.lun_infos:
            if group_name in lun_info.group_name:
                found += 1
        if found:
            self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
            self.response.rc.message = "Group %s is used for lun" %group_name 
            self.SendResponse(self.response)
            return MS_FINISH

        e, _ = dbservice.srv.delete("/group_list/%s"%group_name)
        if e:
            logger.run.error("Delete group list faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        
        # 同配置文件全局更新
        group_list = msg_mds.G_GroupConfList()
        for group in g.group_list.groups:
            if group_name != group.group_name:
                group_list.groups.add().CopyFrom(group)
        g.group_list = group_list
        
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
