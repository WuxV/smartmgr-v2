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

class NodeAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.NODE_ADD_REQUEST
    
    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.NODE_ADD_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.node_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        #处理添加节点
        if self.request_body.HasField('node_name'):
            node_name = self.request_body.node_name
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Not specify params node_name"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.HasField('group_name'):
            self.group_name = self.request_body.group_name
        else:
            self.group_name = ""
        group_exists = 0
        # 当指定组的时候查找组名
        if self.group_name:
            error,self.group_info = common.GetGroupInfoFromName(self.group_name)
            if error:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Not found group %s"% self.group_name
                self.SendResponse(self.response)
                return MS_FINISH
           
        #获取实时节点列表对应的uuid
        found = 0
        self.node_info = msg_pds.NodeInfoConf()
        for nsnode_info in g.nsnode_list.nsnode_infos:
            logger.run.debug("node info :%s" % nsnode_info)
            if not nsnode_info.HasField("listen_ip") or not nsnode_info.HasField("broadcast_ip") :
                continue

            # FIXME:计算节点是否需要添加存储节点
            if node_name == nsnode_info.node_name and  nsnode_info.HasField("node_uuid") and nsnode_info.sys_mode != "storage":
                self.node_info.node_uuid = nsnode_info.node_uuid
                self.node_info.node_name = nsnode_info.node_name
                self.node_info.listen_ip = nsnode_info.listen_ip
                self.node_info.listen_port = nsnode_info.listen_port
                self.node_info.node_guids.extend(nsnode_info.ibguids)
                found+=1

        # FIXME:暂不支持同局域网 同nodename
        if found > 1:
            self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
            self.response.rc.message = "Found %d same node name in node list"%found
            self.SendResponse(self.response)
            return MS_FINISH
        elif found == 0:
            self.response.rc.retcode = msg_mds.RC_MDS_NODE_FIND_FAIL
            self.response.rc.message = " Not found %s in node list with database" % node_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 查询是否添加
        for node in g.nsnode_conf_list.nsnode_infos:
            if self.node_info.node_uuid == node.node_uuid:
                self.response.rc.retcode = msg_mds.RC_MDS_NODE_ADD_FAIL
                self.response.rc.message = "The node already add(%s)"%node_name
                self.SendResponse(self.response)
                return MS_FINISH
        
        self.ios_request = MakeRequest(msg_ios.LUN_GROUP_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_group_add_request]
        self.ios_request_body.node_uuid = self.node_info.node_uuid
        self.ios_request_body.ibguids.extend(self.node_info.node_guids)
        ret  = self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunGroup)
        return MS_CONTINUE

    def Entry_AddLunGroup(self,response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 添加节点配置
        idx = common.NewNodeName()
        self.node_info.node_index = idx
        self.data = pb2dict_proxy.pb2dict("nsnode_info", self.node_info)
        e, _ = dbservice.srv.create("/node_list/%s"%self.node_info.node_uuid, self.data)
        if e:
            logger.run.error("Create node list faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        
        node = msg_pds.NSNodeInfoConf()
        node.node_uuid = self.node_info.node_uuid
        node.node_info.CopyFrom(self.node_info)
        g.nsnode_conf_list.nsnode_infos.add().CopyFrom(node)

        # 如果 指定组将节点加入到组中
        if self.group_name:
            request = MakeRequest(msg_mds.NODE_CONFIG_REQUEST)
            request.body.Extensions[msg_mds.node_config_request].node_index = self.node_info.node_index
            request.body.Extensions[msg_mds.node_config_request].group_name = self.group_name
            self.SendInternalRequest(request,self.Entry_ConfigAdd)
            return MS_CONTINUE
        
    def Entry_ConfigAdd(self,response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
        
