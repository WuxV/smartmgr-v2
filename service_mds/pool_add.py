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

# input: sd01p1
# 1. 检查disk_name是否存在, 并检查磁盘的实时状态是否在线
# 2. 检查disk是否已经被pool引用
# 3. 检查disk是否已经被smartcache引用
# 4. 检查disk是否已经被basedisk引用
# 5. 将请求发送给ios执行创建pool动作

class PoolAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.POOL_ADD_REQUEST

    def INIT(self, request):
        self.default_timeout = 55
        self.response        = MakeResponse(msg_mds.POOL_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.pool_add_request]

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

        disk_name = disk_names[0]
        rc, self.disk_info = self.check_disk_available(disk_name)
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Check disk faild %s:%s" % (disk_name, rc.message))
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        pool_info                = msg_pds.PoolInfo()
        if self.request_body.HasField('pool_name'):
            pool_info.pool_name  = self.request_body.pool_name
        else:
            pool_info.pool_name  = common.NewPoolName()
        pool_info.is_variable    = self.request_body.is_variable
        pool_disk_info           = pool_info.pool_disk_infos.add()
        pool_disk_info.disk_id   = self.disk_info.header.uuid
        pool_disk_info.disk_part = int(disk_name.split('p')[1])
        if self.request_body.HasField('extent'): pool_info.extent = self.request_body.extent
        if self.request_body.HasField('bucket'): pool_info.bucket = self.request_body.bucket
        if self.request_body.HasField('sippet'): pool_info.sippet = self.request_body.sippet

        self.ios_request = MakeRequest(msg_ios.POOL_ADD_REQUEST, self.request)
        self.ios_request.body.Extensions[msg_ios.pool_add_request].pool_info.CopyFrom(pool_info)

        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, self.ios_request, self.Entry_AddPool)
        return MS_CONTINUE

    def Entry_AddPool(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 将Pool配置信息持久化
        pool_info                     = self.ios_request.body.Extensions[msg_ios.pool_add_request].pool_info
        pool_info.pool_id             = response.body.Extensions[msg_ios.pool_add_response].pool_id
        pool_info.is_variable         = self.request_body.is_variable
        pool_info.actual_state        = True
        pool_info.last_heartbeat_time = int(time.time())

        data = pb2dict_proxy.pb2dict("pool_info", pool_info)
        e, _ = dbservice.srv.create("/pool/%s" % pool_info.pool_id, data)
        if e:
            logger.run.error("Create pool faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 及时更新pool导出信息，换盘需要
        pool_export_info = response.body.Extensions[msg_ios.pool_add_response].ext_poolinfo_pool_export_info
        pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].CopyFrom(pool_export_info)

        # 更新内存pool列表
        g.pool_list.pool_infos.add().CopyFrom(pool_info)

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
