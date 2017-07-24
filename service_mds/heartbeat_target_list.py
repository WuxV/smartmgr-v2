# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
from service_mds import pb2dict_proxy
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class HeartBeatTargetListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_TARGET_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_TARGET_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_target_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        palcache_export_list = {}
        palraw_export_list   = {}
        palpmt_export_list   = {}

        for target_export_info in self.request_body.target_export_infos:
            if target_export_info.type == msg_pds.TARGET_TYPE_CACHE:
                palcache_export_list[target_export_info.target_id] = target_export_info
            if target_export_info.type == msg_pds.TARGET_TYPE_RAW:
                palraw_export_list[target_export_info.target_id] = target_export_info
            if target_export_info.type == msg_pds.TARGET_TYPE_PMT:
                palpmt_export_list[target_export_info.target_id] = target_export_info

        # palcache
        for palcache_info in g.palcache_list.palcache_infos:
            if palcache_info.palcache_id in palcache_export_list.keys():
                if palcache_info.actual_state == False:
                    logger.run.info('[NODE STATE]: change palcache %s actual state to True' % palcache_info.palcache_id)
                palcache_info.actual_state        = True
                palcache_info.last_heartbeat_time = int(time.time())
                palcache_info.Extensions[msg_mds.ext_palcache_export_info].CopyFrom(palcache_export_list[palcache_info.palcache_id])
                # 检查palcache pal-id, 如果变更,需要更新配置文件
                if not palcache_info.HasField('pal_id'):
                    continue
                if palcache_info.pal_id != palcache_export_list[palcache_info.palcache_id].pal_id:
                    logger.run.info("Start update palcache %s pal id" % palcache_info.palcache_id)
                    _palcache_info = msg_pds.PalCacheInfo()
                    _palcache_info.CopyFrom(palcache_info)
                    _palcache_info.pal_id = palcache_export_list[palcache_info.palcache_id].pal_id
                    data = pb2dict_proxy.pb2dict("palcache_info", _palcache_info)
                    e, _ = dbservice.srv.update("/palcache/%s" % _palcache_info.palcache_id, data)
                    if e:
                        logger.run.error("Update palcache pal id %s info faild %s:%s" % (_palcache_info.palcache_id, e, _))
                        continue
                    palcache_info.CopyFrom(_palcache_info)

        # palraw
        for palraw_info in g.palraw_list.palraw_infos:
            if palraw_info.palraw_id in palraw_export_list.keys():
                if palraw_info.actual_state == False:
                    logger.run.info('[NODE STATE]: change palraw %s actual state to True' % palraw_info.palraw_id)
                palraw_info.actual_state        = True
                palraw_info.last_heartbeat_time = int(time.time())
                palraw_info.Extensions[msg_mds.ext_palraw_export_info].CopyFrom(palraw_export_list[palraw_info.palraw_id])
                # 检查palraw pal-id, 如果变更,需要更新配置文件
                if not palraw_info.HasField('pal_id'):
                    continue
                if palraw_info.pal_id != palraw_export_list[palraw_info.palraw_id].pal_id:
                    logger.run.info("Start update palraw %s pal id" % palraw_info.palraw_id)
                    _palraw_info = msg_pds.PalRawInfo()
                    _palraw_info.CopyFrom(palraw_info)
                    _palraw_info.pal_id = palraw_export_list[palraw_info.palraw_id].pal_id
                    data = pb2dict_proxy.pb2dict("palraw_info", _palraw_info)
                    e, _ = dbservice.srv.update("/palraw/%s" % _palraw_info.palraw_id, data)
                    if e:
                        logger.run.error("Update palraw pal id %s info faild %s:%s" % (_palraw_info.palraw_id, e, _))
                        continue
                    palraw_info.CopyFrom(_palraw_info)

        # palpmt
        for palpmt_info in g.palpmt_list.palpmt_infos:
            if palpmt_info.palpmt_id in palpmt_export_list.keys():
                if palpmt_info.actual_state == False:
                    logger.run.info('[NODE STATE]: change palpmt %s actual state to True' % palpmt_info.palpmt_id)
                palpmt_info.actual_state        = True
                palpmt_info.last_heartbeat_time = int(time.time())
                palpmt_info.Extensions[msg_mds.ext_palpmt_export_info].CopyFrom(palpmt_export_list[palpmt_info.palpmt_id])
                # 检查palpmt pal-id, 如果变更,需要更新配置文件
                if not palpmt_info.HasField('pal_id'):
                    continue
                if palpmt_info.pal_id != palpmt_export_list[palpmt_info.palpmt_id].pal_id:
                    logger.run.info("Start update palpmt %s pal id" % palpmt_info.palpmt_id)
                    _palpmt_info = msg_pds.PalPmtInfo()
                    _palpmt_info.CopyFrom(palpmt_info)
                    _palpmt_info.pal_id = palpmt_export_list[palpmt_info.palpmt_id].pal_id
                    data = pb2dict_proxy.pb2dict("palpmt_info", _palpmt_info)
                    e, _ = dbservice.srv.update("/palpmt/%s" % _palpmt_info.palpmt_id, data)
                    if e:
                        logger.run.error("Update palpmt pal id %s info faild %s:%s" % (_palpmt_info.palpmt_id, e, _))
                        continue
                    palpmt_info.CopyFrom(_palpmt_info)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
