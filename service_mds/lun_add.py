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

# input: hd01p1 [hd02p1] [pool01]
# 1. 检查数据盘是否存在, 以及实时状态是否存在
# 2. 检查数据盘是否已经创建过lun
# 3. 如果有cache盘, 检查cache盘是否已经创建过lun, 是否在线, 大小是否超过数据盘
# 4. 如果有pool, 检查pool是否已经创建过pool
# 5. 讲请求发送给ios执行创建lun动作 

class LunAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.LUN_ADD_REQUEST

    def INIT(self, request):
        self.default_timeout = 120
        self.response        = MakeResponse(msg_mds.LUN_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.lun_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.data_disk_info  = None
        self.cache_disk_info = None
        self.pool_info       = None
        if self.request_body.HasField('lun_name'):
            self.lun_name        = self.request_body.lun_name
        else:
            self.lun_name        = common.NewLunName()
       
        # 查询组中节点信息
        if self.request_body.HasField("group_name"):
            error,group_info = common.GetGroupInfoFromName(self.request_body.group_name)
            if error:
                self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
                self.response.rc.message = "Not found group %s"% self.request_body.group_name
                self.SendResponse(self.response)
                return MS_FINISH

            self.group_uuid = group_info.node_uuids
            if not self.group_uuid:
               self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
               self.response.rc.message = "Group %s not configure node"%self.request_body.group_name
               self.SendResponse(self.response)
               return MS_FINISH
        else:
            self.response.rc.retcode = msg_mds.RC_MDS_GROUP_FIND_FAIL
            self.response.rc.message = "Not specify group name"
            self.SendResponse(self.response)
            return MS_FINISH

        if self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            return self.BaseDiskCheck()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            if g.license['SmartCacheSupport'].lower() != "yes":
                return self.LicenseFailed()
            return self.SmartCacheCheck()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            if g.license['PALSupport'].lower() != "yes":
                return self.LicenseFailed()
            return self.PalCacheCheck()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALRAW:
            if g.license['PALSupport'].lower() != "yes":
                return self.LicenseFailed()
            return self.PalRawCheck()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALPMT:
            if g.license['PALSupport'].lower() != "yes":
                return self.LicenseFailed()
            return self.PalPmtCheck()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            return self.BaseDevCheck()
        else:
            assert(0)

    def LicenseFailed(self):
        self.response.rc.retcode = msg_mds.RC_MDS_LICENSE_FAILED
        self.response.rc.message = "License not support"
        self.SendResponse(self.response)
        return MS_FINISH

    def BaseDevCheck(self):
        for basedev_info in g.basedev_list.basedev_infos:
            if basedev_info.dev_name == self.request_body.Extensions[msg_mds.ext_lunaddrequest_basedev].dev_name:
                self.response.rc.retcode = msg_mds.RC_MDS_LUN_ALREADY_EXIST
                self.response.rc.message = "Dev %s already exist" % basedev_info.dev_name
                self.SendResponse(self.response)
                return MS_FINISH

        dev_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_basedev].dev_name
        if dev_name.startswith("/dev/mapper/") and dev_name.find("lvvote") != -1:
            self.lun_name = dev_name.split("-")[1]
            if common.GetLunInfoByName(self.lun_name) != None:
                self.response.rc.retcode = msg_mds.RC_MDS_LUN_ALREADY_EXIST
                self.response.rc.message = "Lun %s already exist" % self.lun_name
                self.SendResponse(self.response)
                return MS_FINISH
        return self.AddLunBaseDev()

    def BaseDiskCheck(self):
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_basedisk].data_disk_name
        rc, self.data_disk_info = self.check_disk_available(data_disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (data_disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        data_disk_part = common.GetDiskPartByID(self.data_disk_info.header.uuid, int(data_disk_name.split('p')[1]))

        # data大小不能超过2T
        if data_disk_part.size >= 2000*1024*1024*1024/512:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk size is bigger then limit size 2000G"
            self.SendResponse(self.response)
            return MS_FINISH
        return self.AddLunBaseDisk()

    def SmartCacheCheck(self):
        data_disk_name  = self.request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].data_disk_name
        cache_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].cache_disk_name

        rc, self.data_disk_info = self.check_disk_available(data_disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (data_disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        rc, self.cache_disk_info = self.check_disk_available(cache_disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (cache_disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 磁盘类型必须是SSD
        if self.cache_disk_info.disk_type != msg_pds.DISK_TYPE_SSD:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Only support SSD disk as cache dev"
            self.SendResponse(self.response)
            return MS_FINISH

        data_disk_part  = common.GetDiskPartByID(self.data_disk_info.header.uuid, int(data_disk_name.split('p')[1]))
        cache_disk_part = common.GetDiskPartByID(self.cache_disk_info.header.uuid, int(cache_disk_name.split('p')[1]))

        # data大小不能超过2T
        if data_disk_part.size >= 2000*1024*1024*1024/512:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk size is bigger then limit size 2000G"
            self.SendResponse(self.response)
            return MS_FINISH

        # cache大小不能超过1T
        if cache_disk_part.size >= 1024*1024*1024*1024/512:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Cache disk size is bigger then limit size 1T"
            self.SendResponse(self.response)
            return MS_FINISH
        
        # cache大小不能超过data
        if cache_disk_part.size >= data_disk_part.size:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Cache disk size is bigger then data disk size"
            self.SendResponse(self.response)
            return MS_FINISH

        # cache和data不能在一个盘上
        if self.data_disk_info.header.uuid == self.cache_disk_info.header.uuid:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk and cache disk can not be on the same physical device"
            self.SendResponse(self.response)
            return MS_FINISH
        
        return self.AddLunSmartCache()

    def PalRawCheck(self):
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palraw].data_disk_name
        rc, self.data_disk_info = self.check_disk_available(data_disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (data_disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        data_disk_part = common.GetDiskPartByID(self.data_disk_info.header.uuid, int(data_disk_name.split('p')[1]))

        # data大小不能超过2T
        if data_disk_part.size >= 2000*1024*1024*1024/512:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk size is bigger then limit size 2000G"
            self.SendResponse(self.response)
            return MS_FINISH
        return self.AddLunPalRaw()

    def PalPmtCheck(self):
        pool_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].pool_name
        size      = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].size

        if size >= 2000:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk size is bigger then limit size 2000G"
            self.SendResponse(self.response)
            return MS_FINISH

        rc, self.pool_info = self.check_pool_available(pool_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check pool faild %s:%s" % (pool_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        pmt_size = 0
        for palpmt_info in g.palpmt_list.palpmt_infos:
            if palpmt_info.pool_id == self.pool_info.pool_id:
                pmt_size += palpmt_info.size
        max_size  = self.pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].max_size
        pool_size = self.pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].size
        max_pmt_size = (max_size-pool_size-pmt_size)*512>>30

        # pmt容量不能超过最大可用
        if max_pmt_size < size:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Support max pal-pmt lun size is : %sG" % max_pmt_size
            self.SendResponse(self.response)
            return MS_FINISH
        return self.AddLunPalPmt()

    def PalCacheCheck(self): 
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].data_disk_name
        pool_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].pool_name

        rc, self.data_disk_info = self.check_disk_available(data_disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (data_disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        data_disk_part = common.GetDiskPartByID(self.data_disk_info.header.uuid, int(data_disk_name.split('p')[1]))

        # data大小不能超过2T
        if data_disk_part.size >= 2000*1024*1024*1024/512:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Data disk size is bigger then limit size 2000G"
            self.SendResponse(self.response)
            return MS_FINISH

        # 磁盘类型必须是HDD
        if self.data_disk_info.disk_type != msg_pds.DISK_TYPE_HDD:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Only support HDD disk as data dev for pal-palcache"
            self.SendResponse(self.response)
            return MS_FINISH

        rc, self.pool_info = self.check_pool_available(pool_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check pool faild %s:%s" % (pool_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH
        return self.AddLunPalCache()

    def AddLunSmartCache(self):
        data_disk_name  = self.request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].data_disk_name
        cache_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].cache_disk_name

        smartcache_info = msg_pds.SmartCacheInfo()
        smartcache_info.smartcache_id   = str(uuid.uuid1())
        smartcache_info.data_disk_id    = self.data_disk_info.header.uuid
        smartcache_info.data_disk_part  = int(data_disk_name.split('p')[1])
        smartcache_info.cache_disk_id   = self.cache_disk_info.header.uuid
        smartcache_info.cache_disk_part = int(cache_disk_name.split('p')[1])

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_SMARTCACHE
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].CopyFrom(smartcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunSmartCache)
        return MS_CONTINUE

    def Entry_AddLunSmartCache(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        smartcache_info = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache]

        # 将smartcache配置信息持久化
        data = pb2dict_proxy.pb2dict("smartcache_info", smartcache_info)
        e, _ = dbservice.srv.create("/smartcache/%s" % smartcache_info.smartcache_id, data)
        if e:
            logger.run.error("Create smartcache faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.smartcache_list.smartcache_infos.add().CopyFrom(smartcache_info)
        return self.CreateLunMetaData()

    def AddLunBaseDev(self):
        dev_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_basedev].dev_name

        basedev_info = msg_pds.BaseDevInfo()
        basedev_info.basedev_id = str(uuid.uuid1())
        basedev_info.dev_name   = dev_name

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_BASEDEV
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedev].CopyFrom(basedev_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunBaseDev)
        return MS_CONTINUE

    def Entry_AddLunBaseDev(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        basedev_info      = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedev]
        basedev_info.size = response.body.Extensions[msg_ios.lun_add_response].size

        # 将磁盘配置信息持久化
        data = pb2dict_proxy.pb2dict("basedev_info", basedev_info)
        e, _ = dbservice.srv.create("/basedev/%s" % basedev_info.basedev_id, data)
        if e:
            logger.run.error("Create basedev faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.basedev_list.basedev_infos.add().CopyFrom(basedev_info)
        return self.CreateLunMetaData()

    def AddLunBaseDisk(self):
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_basedisk].data_disk_name

        basedisk_info = msg_pds.BaseDiskInfo()
        basedisk_info.basedisk_id = str(uuid.uuid1())
        basedisk_info.disk_id     = self.data_disk_info.header.uuid
        basedisk_info.disk_part   = int(data_disk_name.split('p')[1])

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_BASEDISK
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk].CopyFrom(basedisk_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunBaseDisk)
        return MS_CONTINUE

    def Entry_AddLunBaseDisk(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        basedisk_info = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk]

        # 将磁盘配置信息持久化
        data = pb2dict_proxy.pb2dict("basedisk_info", basedisk_info)
        e, _ = dbservice.srv.create("/basedisk/%s" % basedisk_info.basedisk_id, data)
        if e:
            logger.run.error("Create basedisk faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.basedisk_list.basedisk_infos.add().CopyFrom(basedisk_info)
        return self.CreateLunMetaData()

    def AddLunPalCache(self):
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].data_disk_name

        palcache_info = msg_pds.PalCacheInfo()
        palcache_info.palcache_name = common.NewTargetName()
        palcache_info.pool_id       = self.pool_info.pool_id
        palcache_info.disk_id       = self.data_disk_info.header.uuid
        palcache_info.disk_part     = int(data_disk_name.split('p')[1])
        palcache_info.Extensions[msg_ios.ext_palcacheinfo_pool_name] = self.pool_info.pool_name

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_PALCACHE
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].CopyFrom(palcache_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunPalCache)
        return MS_CONTINUE

    def Entry_AddLunPalCache(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        palcache_info             = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palcache]
        palcache_info.pal_id      = response.body.Extensions[msg_ios.lun_add_response].target_pal_id
        palcache_info.palcache_id = response.body.Extensions[msg_ios.lun_add_response].target_id

        # 将palcache配置信息持久化
        data = pb2dict_proxy.pb2dict("palcache_info", palcache_info)
        e, _ = dbservice.srv.create("/palcache/%s" % palcache_info.palcache_id, data)
        if e:
            logger.run.error("Create palcache faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.palcache_list.palcache_infos.add().CopyFrom(palcache_info)
        return self.CreateLunMetaData()

    def AddLunPalRaw(self):
        data_disk_name = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palraw].data_disk_name

        palraw_info = msg_pds.PalRawInfo()
        palraw_info.palraw_name   = common.NewTargetName()
        palraw_info.disk_id       = self.data_disk_info.header.uuid
        palraw_info.disk_part     = int(data_disk_name.split('p')[1])

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_PALRAW
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].CopyFrom(palraw_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunPalRaw)
        return MS_CONTINUE

    def Entry_AddLunPalRaw(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        palraw_info           = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palraw]
        palraw_info.pal_id    = response.body.Extensions[msg_ios.lun_add_response].target_pal_id
        palraw_info.palraw_id = response.body.Extensions[msg_ios.lun_add_response].target_id

        # 将palraw配置信息持久化
        data = pb2dict_proxy.pb2dict("palraw_info", palraw_info)
        e, _ = dbservice.srv.create("/palraw/%s" % palraw_info.palraw_id, data)
        if e:
            logger.run.error("Create palraw faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.palraw_list.palraw_infos.add().CopyFrom(palraw_info)
        return self.CreateLunMetaData()

    def AddLunPalPmt(self):
        palpmt_info = msg_pds.PalPmtInfo()
        palpmt_info.palpmt_name = common.NewTargetName()
        palpmt_info.pool_id     = self.pool_info.pool_id
        palpmt_info.size        = self.request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].size
        palpmt_info.Extensions[msg_ios.ext_palpmtinfo_pool_name] = self.pool_info.pool_name

        self.ios_request = MakeRequest(msg_ios.LUN_ADD_REQUEST, self.request)
        self.ios_request_body = self.ios_request.body.Extensions[msg_ios.lun_add_request]
        if self.group_uuid:
            self.ios_request_body.group_name.extend(self.group_uuid)
        self.ios_request_body.node_name = g.node_info.node_name
        self.ios_request_body.lun_id    = str(uuid.uuid1())
        self.ios_request_body.lun_name  = self.lun_name
        self.ios_request_body.lun_type  = msg_pds.LUN_TYPE_PALPMT
        self.ios_request_body.keep_res  = False
        self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].CopyFrom(palpmt_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddLunPalPmt)
        return MS_CONTINUE

    def Entry_AddLunPalPmt(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        palpmt_info           = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt]
        palpmt_info.pal_id    = response.body.Extensions[msg_ios.lun_add_response].target_pal_id
        palpmt_info.palpmt_id = response.body.Extensions[msg_ios.lun_add_response].target_id
        palpmt_info.size      = (palpmt_info.size<<30)/512

        # 将palpmt配置信息持久化
        data = pb2dict_proxy.pb2dict("palpmt_info", palpmt_info)
        e, _ = dbservice.srv.create("/palpmt/%s" % palpmt_info.palpmt_id, data)
        if e:
            logger.run.error("Create palpmt faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        g.palpmt_list.palpmt_infos.add().CopyFrom(palpmt_info)
        return self.CreateLunMetaData()

    # 检查池参数的合法性
    def check_pool_available(self, pool_name):
        # pool_name : pool01
        rc = msg_pds.ResponseCode()
        # 检查pool是否存在
        pool_info = common.GetPoolInfoByName(pool_name)
        if pool_info == None:
            rc.retcode = msg_mds.RC_MDS_POOL_NOT_EXIST
            rc.message = "Pool '%s' is not exist" % pool_name
            return rc, None
        # 检查pool是否在线
        if pool_info.actual_state == False:
            rc.retcode = msg_mds.RC_MDS_POOL_NOT_AVAILABLE
            rc.message = "Pool %s is not available" % pool_name
            return rc, None

        rc.retcode = msg_pds.RC_SUCCESS
        return rc, pool_info

    # 检查磁盘参数合法性
    def check_disk_available(self, disk_part_name):
        # disk_part_name : hdNpM
        rc = msg_pds.ResponseCode()
        if len(disk_part_name.split('p')) != 2:
            rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            rc.message = "Disk name '%s' is not legal, please use 'hdNpM'" % disk_part_name
            return rc, None

        disk_part  = disk_part_name.split('p')[1]
        disk_name  = disk_part_name.split('p')[0]
        if not disk_part.isdigit():
            rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            rc.message = "Disk name '%s' is not legal" % disk_part_name
            return rc, None
        disk_part = int(disk_part)

        # 检查磁盘是否存在
        disk_info = common.GetDiskInfoByName(disk_name)
        if disk_info == None:
            rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            rc.message = "Disk '%s' is not exist" % disk_name
            return rc, None

        # 检查分区是否存在
        if len([diskpart for diskpart in disk_info.diskparts if diskpart.disk_part == disk_part]) == 0:
            rc.retcode = msg_mds.RC_MDS_DISK_PART_NOT_EXIST
            rc.message = "Disk %s's part %s is not exist" % (disk_name, disk_part)
            return rc, None

        # 检查磁盘分区是否有被POOL使用过
        pool_info = common.GetPoolInfoByDiskPart(disk_info.header.uuid, disk_part)
        if pool_info != None:
            rc.retcode = msg_mds.RC_MDS_DISK_PART_IS_IN_USED
            rc.message = "Disk '%s' is used by Pool:'%s'" % (disk_part_name, pool_info.pool_name)
            return rc, None

        # 检查磁盘是否已经创建过lun
        lun_info = common.GetLunInfoByDiskPart(disk_info.header.uuid, disk_part)
        if lun_info != None:
            rc.retcode = msg_mds.RC_MDS_DISK_PART_IS_IN_USED
            rc.message = "Disk '%s' is used by Lun:'%s'" % (disk_part_name, lun_info.lun_name)
            return rc, None

        rc.retcode = msg_pds.RC_SUCCESS
        return rc, disk_info

    def CreateLunMetaData(self):
        lun_info = msg_pds.LunInfo()
        lun_info.lun_id              = self.ios_request_body.lun_id
        lun_info.lun_name            = self.ios_request_body.lun_name
        lun_info.lun_type            = self.ios_request_body.lun_type
        lun_info.config_state        = True
        lun_info.actual_state        = True
        lun_info.last_heartbeat_time = int(time.time())
        if self.group_uuid:
            for k in self.group_uuid:
                info = lun_info.group_info.add()
                info.group_uuid = k
                info.group_state = 1
        
        lun_info.group_name.extend([self.request_body.group_name])
        
        if lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            smartcache_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].smartcache_id
            lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id] = smartcache_id
        elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            basedisk_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk].basedisk_id
            lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id] = basedisk_id
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].palcache_id
            lun_info.Extensions[msg_pds.ext_luninfo_palcache_id] = palcache_id
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            palraw_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].palraw_id
            lun_info.Extensions[msg_pds.ext_luninfo_palraw_id] = palraw_id
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            palpmt_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].palpmt_id
            lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id] = palpmt_id
        elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            basedev_id = self.ios_request_body.Extensions[msg_ios.ext_lunaddrequest_basedev].basedev_id
            lun_info.Extensions[msg_pds.ext_luninfo_basedev_id] = basedev_id
        # 将lun配置信息持久化
        data = pb2dict_proxy.pb2dict("lun_info", lun_info)
        e, _ = dbservice.srv.create("/lun/%s" % lun_info.lun_id, data)
        if e:
            logger.run.error("Create lun info faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新lun列表
        g.lun_list.lun_infos.add().CopyFrom(lun_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
