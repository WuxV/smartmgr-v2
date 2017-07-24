# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
from service_ios import g
from service_ios import common
from service_ios.base.apidisk import APIDisk
from service_ios.base import apipal

class PoolAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.POOL_ADD_REQUEST

    def INIT(self, request):
        self.default_timeout = 50
        self.response        = MakeResponse(msg_ios.POOL_ADD_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_ios.pool_add_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        g.last_modify_time = int(time.time())

        pool_info = self.request_body.pool_info

        params = {}
        params['pool_name']   = pool_info.pool_name
        params['is_variable'] = pool_info.is_variable
        params['disk_id']     = pool_info.pool_disk_infos[0].disk_id
        params['disk_part']   = pool_info.pool_disk_infos[0].disk_part
        if pool_info.HasField('extent'): params['extent'] = pool_info.extent
        if pool_info.HasField('bucket'): params['bucket'] = pool_info.bucket
        if pool_info.HasField('sippet'): params['sippet'] = pool_info.sippet

        self.LongWork(self.add_pool, params, self.Entry_PoolAdd)
        return MS_CONTINUE

    def add_pool(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        pool_name   = str(params['pool_name'])
        disk_id     = params['disk_id']
        disk_part   = params['disk_part']
        is_variable = params['is_variable']

        # 获取分区信息
        part = common.GetPartInfo(disk_id, disk_part)
        if part == None:
            rc.retcode = msg_ios.RC_IOS_LUN_NOT_EXIST
            rc.message = "part %s,%s not exist" % (disk_id, disk_part)
            return rc, ''

        p_attr = {}
        if "extent" in params.keys(): p_attr['extent'] = params['extent']
        if "bucket" in params.keys(): p_attr['bucket'] = params['bucket']
        if "sippet" in params.keys(): p_attr['sippet'] = params['sippet']

        # 计算pool的最大size
        len_mode = apipal.POOL_LENGTH_FIXED
        if is_variable: len_mode = apipal.POOL_LENGTH_VARIABLE
        e, pool_size = apipal.Pool().calc_max_pool_size(part['SIZE'], p_attr, len_mode)
        if e:
            rc.retcode = msg_ios.RC_IOS_PAL_POOL_SIZE_CALC_FAILED
            rc.message = "pal cale max pool size failed:%s" % pool_size
            return rc, ''

        # 添加磁盘
        e, res = apipal.Disk().add_disk(part['DEVNAME'], True)
        if e:
            if res.find("already added in PAL") != -1:
                e, res = apipal.Disk().del_disk(part['DEVNAME'])
                if e:
                    rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                    rc.message = "pal add disk failed :%s" % res
                    return rc, ''
                e, res = apipal.Disk().add_disk(part['DEVNAME'], True)
                if e:
                    rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                    rc.message = "pal add disk failed  :%s" % res
                    return rc, ''
            else:
                rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                rc.message = "pal add disk  failed  :%s" % res
                return rc, ''

        # 创建pool
        e, res = apipal.Pool().add_pool(pool_name, pool_size, 'pile', p_attr, is_variable)
        if e:
            if res.find("pool already exists") != -1:
                e, res = apipal.Pool().del_pool(pool_name)
                if e:
                    rc.retcode = msg_ios.RC_IOS_PAL_POOL_ADD_FAILED
                    rc.message = "pal add pool failed :%s" % res
                    return rc, ''
                e, res = apipal.Pool().add_pool(pool_name, pool_size, 'pile', p_attr, is_variable)
                if e:
                    rc.retcode = msg_ios.RC_IOS_PAL_POOL_ADD_FAILED
                    rc.message = "pal add pool failed  :%s" % res
                    return rc, ''
            else:
                rc.retcode = msg_ios.RC_IOS_PAL_POOL_ADD_FAILED
                rc.message = "pal add pool failed  :%s" % res
                return rc, ''

        # 添加磁盘
        e, res = apipal.Pool().insert_ssd(pool_name, part['DEVNAME'])
        if e and res.find("disk already in pool") == -1:
            rc.retcode = msg_ios.RC_IOS_PAL_POOL_ADD_DISK_FAILED
            rc.message = "pal pool insert disk failed:%s" % res
            return rc, ''

        # run执行pool
        e, pool_list = apipal.Pool().get_pool_list()
        if e:
            rc.retcode = msg_ios.RC_IOS_PAL_POOL_LIST_FAILED
            rc.message = "Get pool list faild:%s" % pool_list
            return rc, ''
        pool_id = None
        for pool in pool_list:
            if pool.name() == pool_name:
                pool_id = pool.uuid()
                e, res  = apipal.Pool().run(pool_name)
                if e:
                    rc.retcode = msg_ios.RC_IOS_PAL_POOL_RUN_FAILED
                    rc.message = "pal start pool failed:%s" % res
                    return rc, ''
                break
        return rc, pool_id

    def Entry_PoolAdd(self, result):
        rc, pool_id = result
        self.response.rc.CopyFrom(rc)
        if rc.retcode == msg_pds.RC_SUCCESS:
            self.response.body.Extensions[msg_ios.pool_add_response].pool_id = pool_id

        # 及时返回实时信息，换盘需要
        pool_export_info = common.GetPoolExportInfoByName(self.request_body.pool_info.pool_name)
        self.response.body.Extensions[msg_ios.pool_add_response].ext_poolinfo_pool_export_info.CopyFrom(pool_export_info)
        self.SendResponse(self.response)
        return MS_FINISH
