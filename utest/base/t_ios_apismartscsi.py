# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))

from pdsframe.common.config import init_config, config
from pdsframe.common.dbclient import *
from pdsframe.common.logger import *
from pdsframe import *

init_config('../../files/conf/test/utest_ios.ini')
init_logger()
#init_dbservice()

from service_ios.base.apismartscsi import  APISmartScsi
if __name__ == "__main__":
    x = APISmartScsi()
    print "---------add group------------"
    print x.add_group("test",["yyyy"])
    print x.errmsg

    print "---------add lun------------"
    params = {}
    params['device_name'] = "su001_sdb1"
    params['path']        = "/dev/sdb1"
    params['t10_dev_id']  = "abc"
    params['group_name']  = "test"
    print x.add_lun(params)
    print x.errmsg
    
    print "---------drop lun------------"
    print x.drop_lun("su001_sdb1")
    print x.errmsg

    print "---------drop group-----------"
    print x.drop_group("test")
    print x.errmsg
    print "---------list group------------"
    print x.list_group()
    print x.errmsg
    print "---------list lun------------"
    print x.get_lun_list()
