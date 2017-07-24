# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time

from pdsframe import *
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios


class LunDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_DROP_REQUEST
    
    def INIT(self, request):
        self.default_timeout = 45

        self.response     = MakeResponse(msg_mds.LUN_DROP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.lun_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        
        items = self.request_body.lun_name.split("_")
        if len(items) != 2 or items[0] != g.node_info.node_name:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH
        self.lun_name = items[1]
        
        if self.lun_name == "lvvote" and self.request_body.force == False:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Please use params [-f] to drop lvvote lun"
            self.SendResponse(self.response)
            return MS_FINISH

        # 获取lun信息
        self.lun_info = common.GetLunInfoByName(self.lun_name)
        if self.lun_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_LUN_NOT_EXIST
            self.response.rc.message = "Lun '%s' is not exist" % self.request_body.lun_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 如果lun的状态是配置online,则禁止删除
        if self.lun_info.config_state == True:
            if not self.lun_info.HasField("asm_status") or self.lun_info.asm_status == "ONLINE":
                self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
                self.response.rc.message = "Lun %s is online state, please offline first." % self.lun_name
                self.SendResponse(self.response)
                return MS_FINISH

        # 删除offline的asmdisk,必须使用-f
        if self.lun_info.asm_status == 'INACTIVE' and not self.request_body.force:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Lun %s is inactive state, please use -f."
            self.SendResponse(self.response)
            return MS_FINISH

        # 需先在计算节点删掉asm
        self.database_node_list = [node_info for node_info in g.nsnode_list.nsnode_infos if node_info.sys_mode != "storage"]
        if self.lun_info.asm_status in ['ACTIVE', 'INACTIVE']:
            self.mds_database_request = MakeRequest(msg_mds.ASMDISK_DROP_REQUEST)
            asmdisk_info = common.GetASMDiskInfoByLunName(self.request_body.lun_name)
            if self.lun_info.asm_status == 'ACTIVE':
                self.mds_database_request.body.Extensions[msg_mds.asmdisk_drop_request].asmdisk_name = asmdisk_info.asmdisk_name
            else:
                self.mds_database_request.body.Extensions[msg_mds.asmdisk_drop_request].asmdisk_name = asmdisk_info.dskname
            if self.request_body.force:
                self.mds_database_request.body.Extensions[msg_mds.asmdisk_drop_request].force = True
            rebalance_power = self.request_body.rebalance_power
            if rebalance_power:
                self.mds_database_request.body.Extensions[msg_mds.asmdisk_drop_request].rebalance_power = rebalance_power

            # 先向第一个计算节点发送请求
            self.request_num = 1
            return self.send_asm_request()
        else:
            return self.drop_lun()

    def send_asm_request(self):
        node_info = self.database_node_list[self.request_num-1]
        self.SendRequest(node_info.listen_ip, node_info.listen_port, self.mds_database_request, self.Entry_ASMDiskDrop)
        return MS_CONTINUE

    def Entry_ASMDiskDrop(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            # 向另外的计算节点发送请求，全部失败才返回
            if self.request_num < len(self.database_node_list):
                self.request_num += 1
                return self.send_asm_request()
            else:
                self.response.rc.CopyFrom(response.rc)
                self.SendResponse(self.response)
                return MS_FINISH

        self.LongWork(self.rebalance_wait, {})

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
    
    def rebalance_wait(self, params={}):
        rc = msg_pds.ResponseCode()
        while True:
            time.sleep(1)
            lun_info = common.GetLunInfoByName(self.lun_name)
            if lun_info.asm_status != "DROPPING":
                break

        if lun_info.asm_status == "HUNG":
            logger.run.error("Lun drop faild: asm drop filed because disk space not enough")
            rc.retcode = msg_mds.RC_MDS_LUN_DROP_FAILED
            return rc, None
        
        self.LongWork(self.offline_lun, {})

        rc.retcode = msg_pds.RC_SUCCESS
        return rc, None

    def offline_lun(self, params={}):
        mds_request = MakeRequest(msg_mds.LUN_OFFLINE_REQUEST)
        mds_request.body.Extensions[msg_mds.lun_offline_request].lun_name = self.request_body.lun_name
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_LunOffline)

        return MS_CONTINUE

    def Entry_LunOffline(self, response):
        rc = msg_pds.ResponseCode()
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error(response.rc.message)
            rc.retcode = response.rc.retcode
            return rc, None
        
        return self.drop_lun()

    def drop_lun(self):
        # 请求转发给对应的ios节点
        self.ios_request = MakeRequest(msg_ios.LUN_DROP_REQUEST, self.request)
        self.ios_request_body           = self.ios_request.body.Extensions[msg_ios.lun_drop_request]
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = self.lun_info.lun_id
        self.ios_request_body.lun_name  = self.lun_info.lun_name
        self.ios_request_body.lun_type  = self.lun_info.lun_type
        self.ios_request_body.keep_res  = False

        group_uuids = []
        for guuid in self.lun_info.group_info:
            group_uuids.append(guuid.group_uuid)
        self.ios_request_body.group_name.extend(group_uuids)

        if self.lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            smartcache_info = common.GetSmartCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].CopyFrom(smartcache_info)
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            basedisk_info = common.GetBaseDiskInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedisk].CopyFrom(basedisk_info)
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_info = common.GetPalCacheInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
            # palcache类型需要补充pool的名字, 解决palcache不可用时, 设置obsolete的过程
            palcache_info.Extensions[msg_ios.ext_palcacheinfo_pool_name] = common.GetPoolInfoById(palcache_info.pool_id).pool_name
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palcache].CopyFrom(palcache_info)
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            palraw_info = common.GetPalRawInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palraw].CopyFrom(palraw_info)
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            palpmt_info = common.GetPalPmtInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palpmt].CopyFrom(palpmt_info)
        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            basedev_info = common.GetBaseDevInfoById(self.lun_info.Extensions[msg_pds.ext_luninfo_basedev_id])
            self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedev].CopyFrom(basedev_info)
        else:
            assert(0)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_LunDrop)
        return MS_CONTINUE

    def Entry_LunDrop(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            if self.lun_info.asm_status == "ACTIVE":
                rc = msg_pds.ResponseCode()
                logger.run.error(response.rc.message)
                rc.retcode = response.rc.retcode
                return rc, None
            else:
                self.response.rc.CopyFrom(response.rc)
                self.SendResponse(self.response)
                return MS_FINISH
        return self.LunDropMetaData()

    def LunDropMetaData(self):
        rc = msg_pds.ResponseCode()
        if self.lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            smartcache_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].smartcache_id

            e, _ = dbservice.srv.delete("/smartcache/%s" % smartcache_id)
            if e:
                logger.run.error("Delete smartcache info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            smartcache_list = msg_mds.G_SmartCacheList()
            for smartcache_info in filter(lambda smartcache_info:smartcache_info.smartcache_id!=smartcache_id,g.smartcache_list.smartcache_infos):
                smartcache_list.smartcache_infos.add().CopyFrom(smartcache_info)
            g.smartcache_list = smartcache_list

        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            basedisk_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedisk].basedisk_id

            e, _ = dbservice.srv.delete("/basedisk/%s" % basedisk_id)
            if e:
                logger.run.error("Delete basedisk info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            basedisk_list = msg_mds.G_BaseDiskList()
            for basedisk_info in filter(lambda basedisk_info:basedisk_info.basedisk_id!=basedisk_id,g.basedisk_list.basedisk_infos):
                basedisk_list.basedisk_infos.add().CopyFrom(basedisk_info)
            g.basedisk_list = basedisk_list

        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            basedev_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_basedev].basedev_id

            e, _ = dbservice.srv.delete("/basedev/%s" % basedev_id)
            if e:
                logger.run.error("Delete basedev info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            basedev_list = msg_mds.G_BaseDevList()
            for basedev_info in filter(lambda basedev_info:basedev_info.basedev_id!=basedev_id,g.basedev_list.basedev_infos):
                basedev_list.basedev_infos.add().CopyFrom(basedev_info)
            g.basedev_list = basedev_list

        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palcache].palcache_id

            e, _ = dbservice.srv.delete("/palcache/%s" % palcache_id)
            if e:
                logger.run.error("Delete palcache info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            palcache_list = msg_mds.G_PalCacheList()
            for palcache_info in filter(lambda palcache_info:palcache_info.palcache_id!=palcache_id,g.palcache_list.palcache_infos):
                palcache_list.palcache_infos.add().CopyFrom(palcache_info)
            g.palcache_list = palcache_list

        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            palraw_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palraw].palraw_id

            e, _ = dbservice.srv.delete("/palraw/%s" % palraw_id)
            if e:
                logger.run.error("Delete palraw info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            palraw_list = msg_mds.G_PalRawList()
            for palraw_info in filter(lambda palraw_info:palraw_info.palraw_id!=palraw_id,g.palraw_list.palraw_infos):
                palraw_list.palraw_infos.add().CopyFrom(palraw_info)
            g.palraw_list = palraw_list

        elif self.lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            palpmt_id = self.ios_request_body.Extensions[msg_ios.ext_lundroprequest_palpmt].palpmt_id

            e, _ = dbservice.srv.delete("/palpmt/%s" % palpmt_id)
            if e:
                logger.run.error("Delete palpmt info faild %s:%s" % (e, _))
                if self.lun_info.asm_status == "ACTIVE":
                    rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    return rc, None
                else:
                    self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                    self.response.rc.message = "Drop data failed"
                    self.SendResponse(self.response)
                    return MS_FINISH

            palpmt_list = msg_mds.G_PalPmtList()
            for palpmt_info in filter(lambda palpmt_info:palpmt_info.palpmt_id!=palpmt_id,g.palpmt_list.palpmt_infos):
                palpmt_list.palpmt_infos.add().CopyFrom(palpmt_info)
            g.palpmt_list = palpmt_list

        else:
            assert(0)

        e, _ = dbservice.srv.delete("/lun/%s" % self.lun_info.lun_id)
        if e:
            logger.run.error("Delete lun info faild %s:%s" % (e, _))
            if self.lun_info.asm_status == "ACTIVE":
                rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                return rc, None
            else:
                self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                self.response.rc.message = "Drop data failed"
                self.SendResponse(self.response)
                return MS_FINISH

        # 从内存中删除该Lun
        lun_list = msg_mds.G_LunList()
        for lun_info in filter(lambda lun_info:lun_info.lun_id!=self.lun_info.lun_id,g.lun_list.lun_infos):
            lun_list.lun_infos.add().CopyFrom(lun_info)
        g.lun_list = lun_list

        if self.lun_info.asm_status == "ACTIVE":
            logger.run.info("Lun %s drop success" % self.request_body.lun_name)
            rc.retcode = msg_pds.RC_SUCCESS
            return rc, None

        self.response.body.Extensions[msg_mds.lun_drop_response].drop_success = True
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
