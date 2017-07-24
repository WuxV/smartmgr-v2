# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from pdsframe import *
from pdsframe.common import dbclient
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

class NodeConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.NODE_CONFIG_REQUEST
    
    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.NODE_CONFIG_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.node_config_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.HasField("node_index") and self.request_body.HasField("group_name"):
            node_index = self.request_body.node_index
            self.group_name = self.request_body.group_name
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

            if self.node_uuid in self.group_info.node_uuids:
                 self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
                 self.response.rc.message = "Node %s already in group %s" % (node_index,self.group_name)
                 self.SendResponse(self.response)
                 return MS_FINISH
               
           # 更新lun信息
           # 如果已经存在node则直接更新配置计数
            found = 0
            for lun_info in g.lun_list.lun_infos:
                if self.group_name in lun_info.group_name:
                    for group_info in lun_info.group_info:
                        if self.node_uuid == group_info.group_uuid:
                            group_info.group_state +=1
                            data = pb2dict_proxy.pb2dict("lun_info", lun_info)
                            e, _ = dbservice.srv.update("/lun/%s" % lun_info.lun_id, data)
                            if e:
                                logger.run.error("Update lun info faild %s:%s" % (e, _))
                                self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
                                self.response.rc.message = "Keep data failed"
                                self.SendResponse(self.response)
                                return MS_FINISH
                            found += 1
            # 如果不存在需要上线该节点
            if not found:
                self.task_info = []
                for lun_info in g.lun_list.lun_infos:
                    if self.group_name in lun_info.group_name:
                        self.task_info.append(lun_info)
                return self.Do_Task()
            else:
                return self.Update_Group_Config()

        elif self.request_body.HasField('node_name'):
            node_info = msg_pds.NodeInfo()
            node_info.CopyFrom(g.node_info)
            
            # TODO: 补充node-name个数和字符的合法性检查
            if len(self.request_body.node_name) > 5:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Node name max len is 5"
                self.SendResponse(self.response)
                return MS_FINISH

            # 检查当前是否有在线的lun
            if len([lun_info for lun_info in g.lun_list.lun_infos if lun_info.config_state==True]) != 0:
                self.response.rc.retcode = msg_mds.RC_MDS_REFUSE_CONFIG_NODE_NAME
                self.response.rc.message = "Please offline all luns before config node name"
                self.SendResponse(self.response)
                return MS_FINISH

            node_info.node_name = self.request_body.node_name
            data = pb2dict_proxy.pb2dict("node_info", node_info)
            # 首次配置的时候, 配置文件中还没有node-info
            e, _ = dbservice.srv.get("/node_info")
            if e == dbclient.RC_ERR_NODE_NOT_EXIST:
                e, _ = dbservice.srv.create("/node_info", data)
                if e:
                    logger.run.error("Create node info faild %s:%s" % (e, _))
                    self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
                    self.response.rc.message = "Keep data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH
            else:
                e, _ = dbservice.srv.update("/node_info", data)
                if e:
                    logger.run.error("Update node info faild %s:%s" % (e, _))
                    self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
                    self.response.rc.message = "Keep data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            g.node_info.CopyFrom(node_info)
            # 更新广播全局节点列表
            for nsnode_info in g.nsnode_list.nsnode_infos:
                if nsnode_info.node_uuid == g.node_uuid:
                    nsnode_info.node_name = node_info.node_name

        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "params error"
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def Do_Task(self):
        if len(self.task_info) == 0:
            return self.Update_Group_Config()
        self.lun_info = self.task_info.pop()
        lun_name = g.node_info.node_name + "_" + self.lun_info.lun_name
        request = MakeRequest(msg_mds.LUN_ONLINE_REQUEST)
        request.body.Extensions[msg_mds.lun_online_request].lun_name = lun_name
        request.body.Extensions[msg_mds.lun_online_request].group_uuid =self.node_uuid
        self.SendInternalRequest(request,self.Entry_ConfigAdd)
        return MS_CONTINUE
            
    def Entry_ConfigAdd(self,response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        return self.Do_Task() 

    def Update_Group_Config(self):
        self.group_info.node_uuids.extend([self.node_uuid])
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

