# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os
sys.path.append(os.path.abspath(os.path.join(__file__, '../')))
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../message/')))
from pdsframe import *
from pdsframe.common.config import init_config, config
import message.pds_pb2 as msg_pds
import message.demo_1_pb2 as msg_demo_1

from utest.base import send

init_config('../../files/conf/test/service.demo_1.ini')

if __name__ == "__main__":
    request = MakeRequest(msg_demo_1.DEMO1_DROP_NAME_REQUEST)
    request.body.Extensions[msg_demo_1.demo1_drop_name_request].name = "d2adccfa-6e7f-11e6-8d38-525400047e15"

    print send(request)
