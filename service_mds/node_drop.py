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

class NodeDelMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.NODE_DROP_REQUEST
    
    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.NODE_DROP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.node_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        #处理参数传递
        if self.request_body.HasField('node_index'):
            node_index = self.request_body.node_index
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Not specify params node index"
            self.SendResponse(self.response)
            return MS_FINISH

        #获取本地节点列表对应的uuid
        error,self.node_uuid = common.GetUUIDFromIndex(node_index)
        if error:
            self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
            self.response.rc.message = "Not find %s" %node_index
            self.SendResponse(self.response)
            return MS_FINISH
 
        # 查询此节点有没有做lun映射
        for _lun_info in g.lun_list.lun_infos:
            if  _lun_info.group_info:
                for info in _lun_info.group_info:
                    if info.group_state and info.group_uuid == self.node_uuid:
                        self.response.rc.retcode = msg_mds.RC_MDS_NODE_HAV_LUN
                        self.response.rc.message = "The node for lun used drop first"
                        self.SendResponse(self.response)
                        return MS_FINISH
        
        self.ios_request = MakeRequest(msg_ios.LUN_GROUP_DROP_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_group_drop_request]
        self.ios_request_body.node_uuid = self.node_uuid
        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_DropLunGroup)
        return MS_CONTINUE
    
    def Entry_DropLunGroup(self,response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        
        e, node_list = dbservice.srv.delete("/node_list/%s"%self.node_uuid)
        if e:
            logger.run.error("delete list info faild %s:%s" % (e, node_list))
            self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        
        # 同配置文件全局更新
        node_list = msg_mds.G_NSNodeConfList()
        for node_info in filter(lambda node_info:node_info.node_uuid!=self.node_uuid,g.nsnode_conf_list.nsnode_infos):
            node_list.nsnode_infos.add().CopyFrom(node_info)
        g.nsnode_conf_list = node_list
        
        #同一节点可以在多个组中
        group_info = msg_pds.GroupInfoConf()
        for group in g.group_list.groups:
            if self.node_uuid in group.node_uuids:
                group_info.CopyFrom(group)
                group_info.remove(self.node_uuid)
                data = pb2dict_proxy.pb2dict("group_info", group_info)
                e, _ = dbservice.srv.update("/group_list/%s"%group.group_name, data)
                if e:
                    logger.run.error("Update node list faild %s:%s" % (e, _))
                    self.response.rc.retcode = msg_mds.RC_MDS_UPDATE_DB_DATA_FAILED
                    self.response.rc.message = "Keep data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH
                group.remove(self.node_uuid)
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

