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

    MID = msg_mds.GROUP_DEL_REQUEST
    
    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.GROUP_DEL_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.group_del_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.group_name = self.request_body.group_name
        node_index = self.request_body.node_index
        error,self.node_uuid = common.GetUUIDFromIndex(node_index)
        if error:
            self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
            self.response.rc.message = "Not find %s" %node_index
            self.SendResponse(self.response)
            return MS_FINISH

        error,self.group_info = common.GetGroupInfoFromName(self.group_name)
        if error:
            self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
            self.response.rc.message = "Not found group %s"% self.group_name
            self.SendResponse(self.response)
            return MS_FINISH

        if not self.node_uuid in self.group_info.node_uuids:
            self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
            self.response.rc.message = "Not find %s in %s" %(node_index,self.group_name)
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新lun信息
        # 如果已经存在node计数 >= 2则减1
        self.task_info = []
        for lun_info in g.lun_list.lun_infos:
            if self.group_name in lun_info.group_name:
                for group_info in lun_info.group_info:
                    if self.node_uuid == group_info.group_uuid and group_info.group_state >= 2:
                        group_info.group_state -=1
                        data = pb2dict_proxy.pb2dict("lun_info", lun_info)
                        e, _ = dbservice.srv.update("/lun/%s" % lun_info.lun_id, data)
                        if e:
                            logger.run.error("Update lun info faild %s:%s" % (e, _))
                            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
                            self.response.rc.message = "Keep data failed"
                            self.SendResponse(self.response)
                            return MS_FINISH
                    # 如果已经存在node计数=1offline此节点
                    elif self.node_uuid == group_info.group_uuid and group_info.group_state == 1:
                        self.task_info.append(lun_info)
        
        if self.task_info:
            return self.Do_Task()
        else:
            return self.Update_Group_Config()
    
    def Do_Task(self):
        if len(self.task_info) == 0:
            return self.Update_Group_Config()
        lun_info = self.task_info.pop()
        lun_name = g.node_info.node_name + "_" + lun_info.lun_name
        request = MakeRequest(msg_mds.LUN_OFFLINE_REQUEST)
        request.body.Extensions[msg_mds.lun_offline_request].lun_name = lun_name
        request.body.Extensions[msg_mds.lun_offline_request].group_uuid =self.node_uuid
        self.SendInternalRequest(request,self.Entry_ConfigDrop)
        return MS_CONTINUE
            
    def Entry_ConfigDrop(self,response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        return self.Do_Task() 

    def Update_Group_Config(self):
        self.group_info.node_uuids.remove(self.node_uuid)
        data = pb2dict_proxy.pb2dict("group_info", self.group_info)
        e, _ = dbservice.srv.update("/group_list/%s"%self.group_name, data)
        if e:
            logger.run.error("Update node list faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

