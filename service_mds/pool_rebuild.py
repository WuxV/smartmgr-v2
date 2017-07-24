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

# input: disk_names->sd01p1 pool_name->pool01
# 1. 检查disk_name是否存在, 并检查磁盘的实时状态是否在线
# 2  检查pool是否已经配置了is_invalid状态
# 3. 检查disk是否已经被smartcache引用
# 4. 检查disk是否已经被basedisk引用
# 5. 检查disk是否已经被其他pool引用
# 6. 将请求发送给ios执行创建pool动作

class PoolRebuildMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.POOL_REBUILD_REQUEST

    def INIT(self, request):
        self.default_timeout = 55
        self.response        = MakeResponse(msg_mds.POOL_REBUILD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.pool_rebuild_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        disk_names = self.request_body.disk_names

        # 当前仅支持单磁盘单pool配置
        if len(disk_names) > 1:
            self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            self.response.rc.message = "Does not support multi-disk config pool "
            self.SendResponse(self.response)
            return MS_FINISH

        # 查找到pool
        self.pool_info = common.GetPoolInfoByName(self.request_body.pool_name)
        if self.pool_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_POOL_NOT_EXIST
            self.response.rc.message = "Pool %s not exist" % self.request_body.pool_name
            self.SendResponse(self.response)
            return MS_FINISH

        # 非is_invalid状态的pool禁止rebuild
        if self.pool_info.is_invalid != True:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Please disable pool first and reboot"
            self.SendResponse(self.response)
            return MS_FINISH

        # 如果pool下已经有palcache在运行, 则禁止执行rebuild
        for palcache_info in filter(lambda palcache_info:palcache_info.pool_id == self.pool_info.pool_id, g.palcache_list.palcache_infos):
            if palcache_info.actual_state == True:
                self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
                self.response.rc.message = "Not support for exist running palcache of pool %s" % self.pool_info.pool_name
                self.SendResponse(self.response)
                return MS_FINISH

        # 验证磁盘
        disk_name = disk_names[0]
        rc, self.disk_info = self.check_disk_available(disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        pool_info                = msg_pds.PoolInfo()
        pool_info.pool_name      = self.pool_info.pool_name     # 使用老的pool名称
        pool_disk_info           = pool_info.pool_disk_infos.add()
        pool_disk_info.disk_id   = self.disk_info.header.uuid
        pool_disk_info.disk_part = int(disk_name.split('p')[1])
        if self.pool_info.HasField('extent'): pool_info.extent = self.pool_info.extent
        if self.pool_info.HasField('bucket'): pool_info.bucket = self.pool_info.bucket
        if self.pool_info.HasField('sippet'): pool_info.sippet = self.pool_info.sippet

        self.ios_request = MakeRequest(msg_ios.POOL_ADD_REQUEST, self.request)
        self.ios_request.body.Extensions[msg_ios.pool_add_request].pool_info.CopyFrom(pool_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddPool)
        return MS_CONTINUE

    def Entry_AddPool(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 补充创建回来的pool-id
        new_pool_info                     = self.ios_request.body.Extensions[msg_ios.pool_add_request].pool_info
        new_pool_info.pool_id             = response.body.Extensions[msg_ios.pool_add_response].pool_id
        new_pool_info.is_rebuild          = True
        new_pool_info.actual_state        = True
        new_pool_info.last_heartbeat_time = int(time.time())

        # 创建新的pool info
        data = pb2dict_proxy.pb2dict("pool_info", new_pool_info)
        e, _ = dbservice.srv.create("/pool/%s" % new_pool_info.pool_id, data)
        if e:
            logger.run.error("Create pool faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH
        g.pool_list.pool_infos.add().CopyFrom(new_pool_info)

        # 更新所有老的palcache的pool id为新的pool id
        ok_flag = True
        for palcache_info in filter(lambda palcache_info:palcache_info.pool_id == self.pool_info.pool_id, g.palcache_list.palcache_infos):
            _palcache_info = msg_pds.PalCacheInfo()
            _palcache_info.CopyFrom(palcache_info)
            # 替换为新的pool-id
            _palcache_info.pool_id = new_pool_info.pool_id
            # 更新配置
            data = pb2dict_proxy.pb2dict("palcache_info", _palcache_info)
            e, _ = dbservice.srv.update("/palcache/%s" % _palcache_info.palcache_id, data)
            if e:
                logger.run.error("Update palcache %s info faild %s:%s" % (_palcache_info.palcache_id, e, _))
                ok_flag = False
                continue
            # 更新内存
            palcache_info.CopyFrom(_palcache_info)

        # 删除老的pool info
        if ok_flag == True:
            e, _ = dbservice.srv.delete("/pool/%s" % self.pool_info.pool_id)
            if e:
                logger.run.error("Delete pool info faild %s:%s" % (e, _))
                self.response.rc.retcode = msg_mds.RC_MDS_DELETE_DB_DATA_FAILED
                self.response.rc.message = "Drop data failed"
                self.SendResponse(self.response)
                return MS_FINISH
            pool_list = msg_mds.G_PoolList()
            for pool_info in filter(lambda pool_info:pool_info.pool_id!=self.pool_info.pool_id,g.pool_list.pool_infos):
                pool_list.pool_infos.add().CopyFrom(pool_info)
            g.pool_list = pool_list

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    # 检查磁盘参数合法性
    def check_disk_available(self, disk_part_name):
        # disk_part_name : hdNpM
        rc = msg_pds.ResponseCode()
        if len(disk_part_name.split('p')) != 2:
            rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
            rc.message = "Disk name '%s' is not legal, please use 'sdNpM'" % disk_part_name
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

        # 检查磁盘是否在线
        if disk_info.actual_state == False:
            rc.retcode = msg_mds.RC_MDS_DISK_OFFLINE
            rc.message = "Disk '%s' is not online" % disk_name
            return rc, None

        # 磁盘类型必须是SSD
        if disk_info.disk_type != msg_pds.DISK_TYPE_SSD:
            rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            rc.message = "Only support use SSD disk to create pool"
            return rc, None

        # 检查分区是否存在
        if len([diskpart for diskpart in disk_info.diskparts if diskpart.disk_part == disk_part]) == 0:
            rc.retcode = msg_mds.RC_MDS_DISK_PART_NOT_EXIST
            rc.message = "Disk %s's part %s is not exist" % (disk_name, disk_part)
            return rc, None

        # 检查磁盘分区是否有被POOL使用过
        pool_info = common.GetPoolInfoByDiskPart(disk_info.header.uuid, disk_part)
        if pool_info != None and pool_info.pool_name != self.pool_info.pool_name:
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
