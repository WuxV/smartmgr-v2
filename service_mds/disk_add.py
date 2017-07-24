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

class DiskAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISK_ADD_REQUEST

    def INIT(self, request):
        self.default_timeout = 55
        self.response        = MakeResponse(msg_mds.DISK_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.disk_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.ces_addr  = None
        self.dev_name  = None
        self.disk_type = None

        # 检查dev_name参数
        # c:e:s    类型, 不准许带disk_type
        # dev name 类型, 必须带disk_type
        if not self.request_body.dev_name.startswith("/dev"):
            # ces
            items = self.request_body.dev_name.split(":")
            if len(items) not in [3,4]:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "param 'Raid.Addr' is ilegal"
                self.SendResponse(self.response)
                return MS_FINISH
            if self.request_body.HasField('disk_type'):
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Not support 'disk type' for add disk by Raid.Addr"
                self.SendResponse(self.response)
                return MS_FINISH
            self.ces_addr = self.request_body.dev_name
        else:
            # dev name
            if not self.request_body.HasField('disk_type'):
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "Please specify disk type, ssd/hdd"
                self.SendResponse(self.response)
                return MS_FINISH
            # 检查所有raid, 如果有盘的盘符为dev_name, 则提示使用ces操作
            for rdisk in g.raid_disk_list_all.raid_disk_infos:
                if rdisk.HasField('dev_name') and rdisk.dev_name == self.request_body.dev_name:
                    self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                    self.response.rc.message = "Please use Raid.Addr as params"
                    self.SendResponse(self.response)
                    return MS_FINISH
            self.dev_name  = self.request_body.dev_name
            self.disk_type = self.request_body.disk_type

        # 检查目标磁盘是否已经初始化过了
        for disk in g.disk_list.disk_infos:
            # 以盘符查找
            if self.dev_name != None and disk.dev_name == self.dev_name:
                self.response.rc.retcode = msg_mds.RC_MDS_DISK_ALREADY_ADDED
                self.response.rc.message = "Disk %s already added" % self.dev_name
                self.SendResponse(self.response)
                return MS_FINISH
            # 以ces查找
            elif disk.HasField('raid_disk_info'):
                ces_addr = "%s:%s:%s" % (disk.raid_disk_info.ctl, disk.raid_disk_info.eid, disk.raid_disk_info.slot)
                if ces_addr == self.ces_addr:
                    self.response.rc.retcode = msg_mds.RC_MDS_DISK_ALREADY_ADDED
                    self.response.rc.message = "Disk %s already added" % self.ces_addr
                    self.SendResponse(self.response)
                    return MS_FINISH

        self.raid_disk_info = None
        # 检查目标盘是否存在
        # 以盘符查找
        if self.dev_name != None:
            disk = [disk for disk in g.disk_list_all.disk_infos if disk.dev_name == self.dev_name]
            if len(disk) == 0:
                self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
                self.response.rc.message = "Disk %s not exist" % self.dev_name
                self.SendResponse(self.response)
                return MS_FINISH
            if disk[0].HasField('raid_disk_info'):
                self.raid_disk_info = msg_pds.RaidDiskInfo()
                self.raid_disk_info.CopyFrom(disk[0].raid_disk_info)
        # 以ces查找
        if self.ces_addr != None:
            raid_disk = []
            for disk in g.raid_disk_list_all.raid_disk_infos:
                if "%s:%s:%s" % (disk.ctl, disk.eid, disk.slot) == self.ces_addr:
                    raid_disk.append(disk)
            if len(raid_disk) == 0:
                self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
                self.response.rc.message = "Disk %s not exist" % self.ces_addr
                self.SendResponse(self.response)
                return MS_FINISH
            if raid_disk[0].HasField('dev_name') and raid_disk[0].dev_name != "":
                # 如果raid有盘符, 则直接通过盘符初始化, 不再通过ces_addr
                self.dev_name = raid_disk[0].dev_name
                self.ces_addr = None
            self.raid_disk_info = msg_pds.RaidDiskInfo()
            self.raid_disk_info = raid_disk[0]
            if raid_disk[0].drive_type.lower() == "ssd":
                self.disk_type = msg_pds.DISK_TYPE_SSD
            else:
                self.disk_type = msg_pds.DISK_TYPE_HDD

        ios_request = MakeRequest(msg_ios.DISK_ADD_REQUEST, self.request)
        if self.dev_name != None:
            ios_request.body.Extensions[msg_ios.disk_add_request].dev_name = self.dev_name
        else:
            ios_request.body.Extensions[msg_ios.disk_add_request].ces_addr = self.ces_addr
        ios_request.body.Extensions[msg_ios.disk_add_request].partition_count = self.request_body.partition_count
        self.SendRequest(g.ios_service.listen_ip, g.ios_service.listen_port, ios_request, self.Entry_DiskAdd)
        return MS_CONTINUE

    def Entry_DiskAdd(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        # 初始化后的盘信息
        disk_info = response.body.Extensions[msg_ios.disk_add_response].disk_info

        # 设置磁盘逻辑id
        if self.request_body.HasField('disk_name'):
            disk_info.disk_name       = self.request_body.disk_name
        else:
            disk_info.disk_name       = common.NewDiskName(self.disk_type)
        disk_info.actual_state        = True
        disk_info.disk_type           = self.disk_type
        disk_info.last_heartbeat_time = int(time.time())
        for diskpart in disk_info.diskparts:
            diskpart.actual_state        = True
            diskpart.last_heartbeat_time = int(time.time())
        if self.raid_disk_info != None:
            disk_info.raid_disk_info.CopyFrom(self.raid_disk_info)

        # 将磁盘配置信息持久化
        data = pb2dict_proxy.pb2dict("disk_info", disk_info)
        e, _ = dbservice.srv.create("/disk/%s" % disk_info.header.uuid, data)
        if e:
            logger.run.error("Create disk faild %s:%s" % (e, _))
            self.response.rc.retcode = msg_mds.RC_MDS_CREATE_DB_DATA_FAILED
            self.response.rc.message = "Keep data failed"
            self.SendResponse(self.response)
            return MS_FINISH

        # 更新磁盘列表
        g.disk_list.disk_infos.add().CopyFrom(disk_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
