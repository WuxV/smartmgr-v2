# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_ios import g
from service_ios.base.disktest import DiskTest
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
disk_fio_script = "/opt/smartmgr/scripts/fiotest.py"
disk_test_cache  = "/opt/smartmgr/files/disktest/.cache"
disk_test_out   = "/opt/smartmgr/files/disktest/"

class GetDiskQualityListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.GET_DISK_QUALITY_LIST_REQUEST

    def INIT(self, request):
        self.response = MakeResponse(msg_ios.GET_DISK_QUALITY_LIST_RESPONSE, request)
        self.request  = request
        self.request_body = request.body.Extensions[msg_ios.get_disk_quality_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

		# 获取磁盘质量列表
        diskTest = DiskTest(disk_test_cache, disk_test_out)
        diskTest.clear_old_result()
        e, disk_quality_list = diskTest.get_result_list()
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_GET_DISK_QUALITY_LIST_FAILED
            self.response.rc.message = "Get disk quality list failed : %s" % disk_quality_list
            self.SendResponse(self.response)
            return MS_FINISH
        for disk_quality in disk_quality_list:
            disk_quality_info = self.response.body.Extensions[msg_ios.get_disk_quality_list_response].disk_quality_infos.add()
            disk_quality_info.t_time     = int(disk_quality['t_time'])
            disk_quality_info.disk_count = len(disk_quality['result'])
            disk_quality_info.ioengine   = disk_quality['attr']['ioengine']
            disk_quality_info.run_time   = disk_quality['attr']['runtime']
            disk_quality_info.block_size = disk_quality['attr']['bs']
            disk_quality_info.num_jobs   = disk_quality['attr']['numjobs']
            disk_quality_info.iodepth    = disk_quality['attr']['iodepth']
        # 获取正在测试的磁盘质量信息
        curr_test = diskTest.get_curr_test()
        if curr_test != None:
            curr_disk_quality_info = self.response.body.Extensions[msg_ios.get_disk_quality_list_response].disk_quality_infos.add()
            curr_disk_quality_info.curr_test  = True
            curr_disk_quality_info.t_time     = int(curr_test['t_time'])
            curr_disk_quality_info.disk_count = len(curr_test['devices'])
            curr_disk_quality_info.ioengine   = curr_test['attr']['ioengine']
            curr_disk_quality_info.run_time   = curr_test['attr']['runtime']
            curr_disk_quality_info.block_size = curr_test['attr']['bs']
            curr_disk_quality_info.num_jobs   = curr_test['attr']['numjobs']
            curr_disk_quality_info.iodepth    = curr_test['attr']['iodepth']

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
