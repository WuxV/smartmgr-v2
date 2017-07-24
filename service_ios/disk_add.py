# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
from service_ios import g
from service_ios.base.apidisk import APIDisk
from service_ios.base.raid.megaraid import MegaRaid
from service_ios.base.raid.hpsaraid import HPSARaid

class DiskAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.DISK_ADD_REQUEST

    def INIT(self, request):
        self.default_timeout = 50
        self.response        = MakeResponse(msg_ios.DISK_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.disk_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        self.dev_name = None
        # 如果传过来的是ces_addr,说明需要先做megaraid的raid
        if self.request_body.HasField('ces_addr'):
            if len(self.request_body.ces_addr.split(":")) == 3:
                e, dev_name = MegaRaid().make_raid(self.request_body.ces_addr)
                if e:
                    self.response.rc.retcode = msg_ios.RC_IOS_MAKE_RAID_FAILD
                    self.response.rc.message = "Create megaraid failed %s:%s" % (e, dev_name)
                    self.SendResponse(self.response)
                    return MS_FINISH
            else:
                e, dev_name = HPSARaid().make_raid(self.request_body.ces_addr)
                if e:
                    self.response.rc.retcode = msg_ios.RC_IOS_MAKE_RAID_FAILD
                    self.response.rc.message = "Create hpsaraid failed %s:%s" % (e, dev_name)
                    self.SendResponse(self.response)
                    return MS_FINISH
            self.dev_name = dev_name
        else:
            self.dev_name = self.request_body.dev_name
        return self.DiskAdd()

    def DiskAdd(self):
        # 获取目标磁盘
        disk_info = None
        e, disk_list = APIDisk().get_disk_list()
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            self.response.rc.message = "Get IOS disk list failed"
            self.SendResponse(self.response)
            return MS_FINISH

        for disk in disk_list:
            if disk['DEVNAME'] == self.dev_name:
                disk_info = disk
                break

        if disk_info == None:
            self.response.rc.retcode = msg_ios.RC_IOS_DISK_NOT_EXIST
            self.response.rc.message = "Disk '%s' not exist" % self.dev_name
            self.SendResponse(self.response)
            return MS_FINISH

        params = {}
        params['devinfo']         = disk_info
        params['partition_count'] = self.request_body.partition_count

        self.LongWork(APIDisk().disk_init, params, self.Entry_DiskAdd)
        return MS_CONTINUE
    
    def Entry_DiskAdd(self, result):
        e ,res = result
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_ADD_DISK_FAILED
            self.response.rc.message = "ADD disk failed :%s" % res.decode("utf-8")
            self.SendResponse(self.response)
            return MS_FINISH

        self.disk_info = None

        e, disk_list = APIDisk().get_disk_list()
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            self.response.rc.message = "Get IOS disk list failed"
            self.SendResponse(self.response)
            return MS_FINISH

        for disk in disk_list:
            if disk['DEVNAME'] == self.dev_name:
                self.disk_info = disk
                break

        if self.disk_info == None:
            self.response.rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            self.response.rc.message = "Get IOS disk list failed"
            self.SendResponse(self.response)
            return MS_FINISH

        disk_info = self.response.body.Extensions[msg_ios.disk_add_response].disk_info
        disk_info.dev_name  = self.disk_info['DEVNAME']
        disk_info.size      = self.disk_info['SIZE']
        if self.disk_info.has_key('HEADER'):
            disk_info.header.uuid = self.disk_info['HEADER']['uuid']

        # 追加分区信息
        for part in self.disk_info['PARTS']:
            diskpart = disk_info.diskparts.add()
            diskpart.disk_part = int(part['INDEX'])
            diskpart.size       = part['SIZE']
            diskpart.dev_name   = part['DEVNAME']

        # 检查分区数是否满足需求
        if len(disk_info.diskparts) != self.request_body.partition_count:
            logger.run.error("Get disk parts :%s, request disk parts :%s" % (len(disk_info.diskparts), self.request_body.partition_count))
            self.response.rc.retcode = msg_ios.RC_IOS_ADD_DISK_FAILED
            self.response.rc.message = "Create disk part failed"
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
