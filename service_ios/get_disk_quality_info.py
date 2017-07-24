# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_ios import g
from service_ios.base.disktest import DiskTest
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
disk_test_cache  = "/opt/smartmgr/files/disktest/.cache"
disk_test_out   = "/opt/smartmgr/files/disktest/"

class GetDiskQualityInfoMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.GET_DISK_QUALITY_INFO_REQUEST

    def INIT(self, request):
        self.response = MakeResponse(msg_ios.GET_DISK_QUALITY_INFO_RESPONSE, request)
        self.request  = request
        self.request_body = request.body.Extensions[msg_ios.get_disk_quality_info_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self, response)
            return MS_FINISH
        return self.GetDiskQualityInfo()

    def GetDiskQualityInfo(self):
        self.t_time = self.request_body.t_time
        uuid_2_disk = {}
        for disk in self.request_body.disk_infos:
            uuid_2_disk[disk.header.uuid] = disk
        
        # 获取指定磁盘信息
        diskTest = DiskTest(disk_test_cache, disk_test_out)
        diskTest.clear_old_result()
        e, result = diskTest.get_result_list()
        disk_quality = {}
        for r in result:
            if r['t_time'] == self.t_time:
                disk_quality = r
        if not disk_quality:
            self.response.rc.retcode = msg_ios.RC_IOS_GET_DISK_QUALITY_INFO_FAILED
            self.response.rc.message = "Can\'t find quality info of time"
            self.SendResponse(self.response)
            return MS_FINISH
        disk_quality_info = self.response.body.Extensions[msg_ios.get_disk_quality_info_response].disk_quality_info
        disk_quality_info.t_time     = int(disk_quality['t_time'])
        disk_quality_info.disk_count = len(disk_quality['result'])
        disk_quality_info.ioengine   = disk_quality['attr']['ioengine']
        disk_quality_info.run_time   = disk_quality['attr']['runtime']
        disk_quality_info.block_size = disk_quality['attr']['bs']
        disk_quality_info.num_jobs   = disk_quality['attr']['numjobs']
        disk_quality_info.iodepth    = disk_quality['attr']['iodepth']
        # 通过uuid补充盘的盘符/name字段
        for info in disk_quality['result']:
            quality_test_result = disk_quality_info.quality_test_result.add()
            uuid = info[1]['device']
            if uuid in uuid_2_disk.keys():
                if uuid_2_disk[uuid].dev_name:
                    quality_test_result.path = uuid_2_disk[uuid].dev_name
                if uuid_2_disk[uuid].disk_name:
                    quality_test_result.name = uuid_2_disk[uuid].disk_name
            if info[0] == 0:
                quality_test_result.randread_iops = int(info[1]['result']['randread-iops'])
                quality_test_result.read_bw = int(info[1]['result']['read-bw'])
        
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
