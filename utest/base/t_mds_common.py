# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))
print sys.path

from pdsframe.common.config import init_config, config
from pdsframe.common.dbclient import *
from pdsframe.common.logger import *
from pdsframe import *

init_config('../../files/conf/test/utest_mds.ini')
init_logger()
init_dbservice()

from service_mds.common import list_ibnodes
from service_mds.common import list_ports
if __name__ == "__main__":
    print "---------------------"
    print list_ibnodes()
    print "---------------------"
    print list_ports()
