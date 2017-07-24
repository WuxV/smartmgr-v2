# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_ios import g
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
from service_ios.base.apismartscsi import APISmartScsi

class HeartBeatLunListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH

        if g.platform['sys_mode'] == "database":
            return MS_FINISH

        apismartscsi = APISmartScsi()
        lun_list     = apismartscsi.get_lun_list()

        mds_request = MakeRequest(msg_mds.HEARTBEAT_LUN_LIST_REQUEST)
        for lun_name, lun_detail_info in lun_list.items():
            lun_info  = lun_detail_info['attrs']
            stat_info = lun_detail_info['stats']

            # lun export info
            lun_export_info = msg_pds.LunExportInfo()
            lun_export_info.lun_name          = lun_name
            lun_export_info.t10_dev_id        = lun_info['t10_dev_id']
            lun_export_info.threads_pool_type = lun_info['threads_pool_type']
            lun_export_info.filename          = lun_info['filename']
            lun_export_info.size_mb           = int(lun_info['size_mb'])
            lun_export_info.threads_num       = int(lun_info['threads_num'])
            lun_export_info.io_error          = int(lun_info['io_error'])
            lun_export_info.last_errno        = int(lun_info['last_errno'])
            if not lun_info.has_key('exported'):
                continue
            for k,v in lun_info['exported'].items():
                exported = lun_export_info.exported.add()
                exported.key   = k
                exported.value = v
            if lun_info.has_key('group_name'):
                lun_export_info.group_name.extend(lun_info["group_name"])

            # lun stat info
            if stat_info == {}:
                continue
            lun_export_info.lun_stats_info.rio     = int(stat_info['rio'])
            lun_export_info.lun_stats_info.rmerge  = int(stat_info['rmerge'])
            lun_export_info.lun_stats_info.rsect   = int(stat_info['rsect'])
            lun_export_info.lun_stats_info.ruse    = int(stat_info['ruse'])
            lun_export_info.lun_stats_info.wio     = int(stat_info['wio'])
            lun_export_info.lun_stats_info.wmerge  = int(stat_info['wmerge'])
            lun_export_info.lun_stats_info.wsect   = int(stat_info['wsect'])
            lun_export_info.lun_stats_info.wuse    = int(stat_info['wuse'])
            lun_export_info.lun_stats_info.running = int(stat_info['running'])
            lun_export_info.lun_stats_info.use     = int(stat_info['use'])
            lun_export_info.lun_stats_info.aveq    = int(stat_info['aveq'])

            _lun_export_info = mds_request.body.Extensions[msg_mds.heartbeat_lun_list_request].lun_export_infos.add()
            _lun_export_info.CopyFrom(lun_export_info)

        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_HeartBeatLunList)
        return MS_CONTINUE

    def Entry_HeartBeatLunList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("%d %s" % (response.rc.retcode, response.rc.message))
        return MS_FINISH
