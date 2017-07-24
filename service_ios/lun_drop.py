# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_ios import g
from service_ios import common
import message.ios_pb2 as msg_ios
import message.pds_pb2 as msg_pds
from service_ios.base.apismartcache import APISmartCache
from service_ios.base.apismartscsi import APISmartScsi
from service_ios.base import apipal

class LunDropMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.LUN_DROP_REQUEST
    
    def INIT(self, request):
        self.default_timeout = 40

        self.response     = MakeResponse(msg_ios.LUN_DROP_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_ios.lun_drop_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_ios.RC_IOS_SERVICE_IS_NOT_READY
            self.response.rc.message = "IOS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

       
        g.last_modify_time = int(time.time())
        
        self.group_name = []
        if self.request_body.group_name:
            for k in self.request_body.group_name:
                self.group_name.append(k)
        if self.request_body.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            return self.DropLunSmartCache()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            return self.DropLunBaseDisk()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            return self.DropLunPalCache()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALRAW:
            return self.DropLunPalRaw()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALPMT:
            return self.DropLunPalPmt()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            return self.DropLunBaseDev()
        else:
            assert(0)

    def DropLunPalCache(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_palcache].palcache_name
        params['disk_id']     = self.request_body.Extensions[msg_ios.ext_lundroprequest_palcache].disk_id
        params['disk_part']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_palcache].disk_part
        params['pal_id']      = self.request_body.Extensions[msg_ios.ext_lundroprequest_palcache].pal_id
        params['pool_name']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_palcache].Extensions[msg_ios.ext_palcacheinfo_pool_name]
        params['keep_res']    = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_palcache, params, self.Entry_LunDrop)
        return MS_CONTINUE

    def DropLunPalRaw(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_palraw].palraw_name
        params['disk_id']     = self.request_body.Extensions[msg_ios.ext_lundroprequest_palraw].disk_id
        params['disk_part']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_palraw].disk_part
        params['pal_id']      = self.request_body.Extensions[msg_ios.ext_lundroprequest_palraw].pal_id
        params['keep_res']    = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_palraw, params, self.Entry_LunDrop)
        return MS_CONTINUE

    def DropLunPalPmt(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_palpmt].palpmt_name
        params['keep_res']    = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_palpmt, params, self.Entry_LunDrop)
        return MS_CONTINUE

    def DropLunBaseDisk(self):
        params = {}
        params['disk_id']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_basedisk].disk_id
        params['disk_part'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_basedisk].disk_part
        params['keep_res']  = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_basedisk, params, self.Entry_LunDrop)
        return MS_CONTINUE

    def DropLunBaseDev(self):
        params = {}
        params['dev_name'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_basedev].dev_name
        params['keep_res'] = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_basedev, params, self.Entry_LunDrop)
        return MS_CONTINUE

    def DropLunSmartCache(self):
        params = {}
        params['smartcache_id']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].smartcache_id
        params['data_disk_id']    = self.request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].data_disk_id
        params['data_disk_part']  = self.request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].data_disk_part
        params['cache_disk_id']   = self.request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].cache_disk_id
        params['cache_disk_part'] = self.request_body.Extensions[msg_ios.ext_lundroprequest_smartcache].cache_disk_part
        params['keep_res']        = self.request_body.keep_res
        self.LongWork(self.drop_lun_with_cache, params, self.Entry_LunDrop)
        return MS_CONTINUE

    # 带cache的lun
    def drop_lun_with_cache(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        smartcache_id   = params['smartcache_id']
        data_disk_id    = params['data_disk_id']
        data_disk_part  = params['data_disk_part']
        cache_disk_id   = params['cache_disk_id']
        cache_disk_part = params['cache_disk_part']

        # 先从smartscsi中删除设备
        # XXX: 只要smartscsi中可以正常删除, 则判整个删除流程成功
        device_name  = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)
        apismartscsi = APISmartScsi()
        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun
        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''


        if params['keep_res'] == True:
            pass
        else:
            # 只是尝试删除smartcache
            e, res = APISmartCache().dm_remove({'cache_name':smartcache_id})
            if e: logger.run.error("Dmsetup remove failed,%s:%s:%s" % (smartcache_id, e, res))

            part = common.GetPartInfo(cache_disk_id, cache_disk_part)
            if part != None:
                e, res = APISmartCache().destroy({'cache_dev':part['DEVNAME']})
                if e: logger.run.error("Destroy cache failed,%s:%s:%s" % (part['DEVNAME'], e, res))
        return rc, ''

    def drop_lun_with_basedisk(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        device_name = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)

        # 从smartscsi中删除设备
        apismartscsi = APISmartScsi()

        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun

        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''
        return rc, ''

    def drop_lun_with_basedev(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        device_name = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)

        # 从smartscsi中删除设备
        apismartscsi = APISmartScsi()

        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun
        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''
        return rc, ''

    def drop_lun_with_palcache(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])
        pool_name   = str(params['pool_name'])
        disk_id     = params['disk_id']
        disk_part   = params['disk_part']

        # 先从smartscsi中删除设备
        # XXX: 只要smartscsi中可以正常删除, 则判整个删除流程成功
        device_name  = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)
        apismartscsi = APISmartScsi()
        
        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun

        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''

        if params['keep_res'] == True:
            pass
        else:
            # 删除target, 
            e, res = apipal.Target().del_target(target_name)
            if e:
                if res.find("target not exists") != -1:
                    # target不存在的时候, 需要检查对应的pool是否是在loading状态
                    # 如果是需要将target-id设置obsolete
                    if None == common.GetPartInfo(params['disk_id'], params['disk_part']):
                        e, pal_pools = apipal.Pool().get_pool_list()
                        if not e:
                            for pool in pal_pools:
                                if pool.name() == params['pool_name'] and apipal.testBit(pool.state(), apipal.POOL_STATE_LOADING):
                                    try:
                                        logger.run.info("Set obsolete target %s:%s" % (params['pool_name'], params['pal_id']))
                                        pool.add_obsolete(int(params['pal_id']))
                                    except Exception as e:
                                        logger.run.error("Set obsolete failed %s:%s:%s" % (params['pool_name'], params['pal_id'], e))
                                    break
                else:
                    logger.run.error("Drop target failed,%s:%s:%s" % (target_name, e, res))

            # 删除pal数据盘
            part = common.GetPartInfo(disk_id, disk_part)
            if part != None:
                e, res = apipal.Disk().del_disk(part['DEVNAME'])
                if e and res.find("not added in PAL") == -1:
                    logger.run.error("Drop pal disk failed,%s:%s:%s" % (part['DEVNAME'], e, res))
        return rc, ''

    def drop_lun_with_palraw(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])
        disk_id     = params['disk_id']
        disk_part   = params['disk_part']

        # 先从smartscsi中删除设备
        # XXX: 只要smartscsi中可以正常删除, 则判整个删除流程成功
        device_name  = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)
        apismartscsi = APISmartScsi()

        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun

        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''

        if params['keep_res'] == True:
            pass
        else:
            # 删除target, 
            e, res = apipal.Target().del_target(target_name)
            if e:
                if res.find("target not exists") != -1:
                    pass
                else:
                    logger.run.error("Drop target failed,%s:%s:%s" % (target_name, e, res))

            # 删除pal数据盘
            part = common.GetPartInfo(disk_id, disk_part)
            if part != None:
                e, res = apipal.Disk().del_disk(part['DEVNAME'])
                if e and res.find("not added in PAL") == -1:
                    logger.run.error("Drop pal disk failed,%s:%s:%s" % (part['DEVNAME'], e, res))
        return rc, ''

    def drop_lun_with_palpmt(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])

        # 先从smartscsi中删除设备
        # XXX: 只要smartscsi中可以正常删除, 则判整个删除流程成功
        device_name  = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)
        apismartscsi = APISmartScsi()

        if self.group_name:
            logger.run.info("Start drop lun, device:%s group:%s" % (device_name,self.group_name))
            e,exist_lun = apismartscsi.drop_lun(device_name,self.group_name)
        else:
            logger.run.info("Start drop lun, device:%s" % device_name)
            e,exist_lun = apismartscsi.drop_lun(device_name)
        self.response.body.Extensions[msg_ios.lun_drop_response].exist_lun = exist_lun

        if e:
            rc.retcode = msg_ios.RC_IOS_DROP_LUN_FAILED
            rc.message = "Lun drop failed:%s" % apismartscsi.errmsg
            return rc, ''

        if params['keep_res'] == True:
            pass
        else:
            # 删除target, 
            e, res = apipal.Target().del_target(target_name)
            if e:
                if res.find("target not exists") != -1:
                    pass
                else:
                    logger.run.error("Drop target failed,%s:%s:%s" % (target_name, e, res))
        return rc, ''

    def Entry_LunDrop(self, result):
        rc, _ = result

        self.response.rc.CopyFrom(rc)
        self.SendResponse(self.response)
        return MS_FINISH
