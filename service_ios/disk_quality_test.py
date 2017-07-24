# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_ios import g
from service_ios.base.disktest import DiskTest
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
disk_fio_script = "/opt/smartmgr/scripts/fiotest.py"
disk_test_cache = "/opt/smartmgr/files/disktest/.cache"
disk_test_out   = "/opt/smartmgr/files/disktest/"

class DiskQualityTestMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.DISK_QUALITY_TEST_REQUEST
    
    def INIT(self, request):
        self.response        = MakeResponse(msg_ios.DISK_QUALITY_TEST_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.disk_quality_test_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH
        return self.DiskQualityTest()

    def DiskQualityTest(self):
        # 从配置文件获取相关信息
        attr = {}
        attr['ioengine'] = config.safe_get('disktest', 'ioengine', 'libaio')
        attr['bs']       = config.safe_get('disktest', 'bs', '4k')
        attr['runtime']  = config.safe_get_int('disktest', 'runtime', '120')
        attr['iodepth']  = config.safe_get_int('disktest', 'iodepth', '8')
        attr['numjobs']  = config.safe_get_int('disktest', 'numjobs', '32')
        # 获取初始化磁盘的uuid和盘符 
        devices = {}
        for disk_info in self.request_body.disk_infos:
            if disk_info.dev_name:
                devices[disk_info.dev_name] = disk_info.header.uuid
    
        if not devices:
            self.response.rc.retcode = msg_ios.RC_IOS_DISK_QUALITY_TEST_FAILED
            self.response.rc.message = "No available disk"
            self.SendResponse(self.response)
            return MS_FINISH


        params = {}
        params['attr']    = attr
        params['devices'] = devices
        params['test_script'] = disk_fio_script 

        diskTest = DiskTest(disk_test_cache, disk_test_out)
        e, msg = diskTest.start_test(params)
        if e:
            self.response.rc.retcode = msg_ios.RC_IOS_DISK_QUALITY_TEST_FAILED
            self.response.rc.message = msg 
            self.SendResponse(self.response)
            return MS_FINISH

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
