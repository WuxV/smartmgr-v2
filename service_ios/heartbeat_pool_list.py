# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import pyudev
from pdsframe import *
from service_ios import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
from service_ios.base import apipal

class HeartBeatPoolListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH

        if g.platform['sys_mode'] == "database":
            return MS_FINISH

        e, pool_list = apipal.Pool().get_pool_list()
        if e:
            logger.run.error('Get pool list failed %s:%s' % (e, pool_list))
            return MS_FINISH

        # 获取基本信息
        mds_request = MakeRequest(msg_mds.HEARTBEAT_POOL_LIST_REQUEST)
        for pool in pool_list:
            pool_export_info = msg_pds.PoolExportInfo()
            pool_export_info.pool_name = pool.name()
            pool_export_info.state_str = pool.state_str()
            pool_export_info.state     = pool.state()
            pool_export_info.size      = pool.cache_per_disk()
            pool_export_info.extent    = pool.extent_sectors()
            pool_export_info.bucket    = pool.bucket_sectors()
            pool_export_info.sippet    = pool.sippet_sectors()
            pool_export_info.max_size  = 0
            pool_export_info.dev_name.append(pool.get_disks()[0])
            pool_export_info.is_variable = True
            if apipal.POOL_LENGTH_FIXED == pool.len_mode():
                pool_export_info.is_variable = False
            if apipal.testBit(pool.state(), apipal.POOL_STATE_MIGRATING):
                pool_export_info.state_exp = "MIGRATING"
            _pool_export_info = mds_request.body.Extensions[msg_mds.heartbeat_pool_list_request].pool_export_infos.add()
            _pool_export_info.CopyFrom(pool_export_info)

        # 获取统计信息
        for pool_export_info in mds_request.body.Extensions[msg_mds.heartbeat_pool_list_request].pool_export_infos:
            e, state = apipal.Pool().get_pool_stat(pool_export_info.pool_name)
            if e:
                logger.run.error('Get pool state failed %s:%s' % (e, pool_export_info.pool_name))
                continue
            pool_export_info.valid          = state['valid']
            pool_export_info.p_valid        = state['p_valid']
            pool_export_info.dirty          = state['dirty']
            pool_export_info.p_dirty        = state['p_dirty']
            pool_export_info.error          = state['error']
            pool_export_info.p_lower_thresh = state['p_lower_thresh']
            pool_export_info.lower_thresh   = state['lower_thresh']
            pool_export_info.p_upper_thresh = state['p_upper_thresh']
            pool_export_info.upper_thresh   = state['upper_thresh']

        context = pyudev.Context()
        # 获取pool所在磁盘可提供的最大pool容量
        for pool_export_info in mds_request.body.Extensions[msg_mds.heartbeat_pool_list_request].pool_export_infos:
            try:
                attr = {}
                attr['extent'] = pool_export_info.extent
                attr['bucket'] = pool_export_info.bucket
                attr['sippet'] = pool_export_info.sippet
                blk_size = int(pyudev.Devices.from_device_file(context, pool_export_info.dev_name[0]).attributes.get('size'))
                len_mode = apipal.POOL_LENGTH_FIXED
                if pool_export_info.is_variable == True:
                    len_mode = apipal.POOL_LENGTH_VARIABLE
                e, max_size = apipal.Pool().calc_max_pool_size(blk_size, attr, len_mode)
                if e: continue
                pool_export_info.max_size = max_size
            except Exception as e:
                pass

        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_HeartBeatPoolList)
        return MS_CONTINUE

    def Entry_HeartBeatPoolList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("%d %s" % (response.rc.retcode, response.rc.message))
        return MS_FINISH
