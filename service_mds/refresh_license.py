# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds


class RefreshLicenseMachine(BaseMachine):
    __metaclass__ = MataMachine

    # 一天更新一次
    LOOP_TIME  = 60*60*24

    def INIT(self):
        if g.is_ready == False:
            logger.run.debug("RefreshLicense MDS service is not ready")
            return MS_FINISH

        g.license  = common.load_license()
        return MS_FINISH
