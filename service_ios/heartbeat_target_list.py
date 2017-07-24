# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_ios import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
from service_ios.base import apipal

class HeartBeatTargetListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH

        if g.platform['sys_mode'] == "database":
            return MS_FINISH

        e, target_list = apipal.Target().get_target_list()
        if e:
            logger.run.error('Get target list failed %s:%s' % (e, target_list))
            return MS_FINISH

        mds_request = MakeRequest(msg_mds.HEARTBEAT_TARGET_LIST_REQUEST)
        for target in target_list:
            target_export_info = msg_pds.TargetExportInfo()
            target_export_info.pal_id      = target.id()
            target_export_info.target_name = target.name()
            target_export_info.target_id   = target.uuid()
            target_export_info.state_str   = target.state_str()

            # cache mode
            if target.mode_str().lower() == "writeback":
                target_export_info.palcache_cache_model = msg_pds.PALCACHE_CACHE_MODEL_WRITEBACK
            elif target.mode_str().lower() == "writethrough":
                target_export_info.palcache_cache_model = msg_pds.PALCACHE_CACHE_MODEL_WRITETHROUGH
            else:
                target_export_info.palcache_cache_model = msg_pds.PALCACHE_CACHE_MODEL_UNKNOWN

            # target type
            if target.type() == apipal.TARGET_TYPE_UNKNOWN:
                target_export_info.type = msg_pds.TARGET_TYPE_UNKNOWN
            elif target.type() == apipal.TARGET_TYPE_CACHE:
                target_export_info.type = msg_pds.TARGET_TYPE_CACHE
            elif target.type() == apipal.TARGET_TYPE_PMT:
                target_export_info.type = msg_pds.TARGET_TYPE_PMT
            elif target.type() == apipal.TARGET_TYPE_RAW:
                target_export_info.type = msg_pds.TARGET_TYPE_RAW
            else:
                assert(0)
            _target_export_info = mds_request.body.Extensions[msg_mds.heartbeat_target_list_request].target_export_infos.add()
            _target_export_info.CopyFrom(target_export_info)

        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_HeartBeatTargetList)
        return MS_CONTINUE

    def Entry_HeartBeatTargetList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("%d %s" % (response.rc.retcode, response.rc.message))
        return MS_FINISH
