# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, os
from pdsframe import *
from service_ios import g
from service_ios import common
import message.ios_pb2 as msg_ios
import message.pds_pb2 as msg_pds
from service_ios.base.apismartcache import APISmartCache
from service_ios.base.apismartscsi import APISmartScsi
from service_ios.base import apipal

class LunAddMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_ios.LUN_ADD_REQUEST
    
    def INIT(self, request):
        self.default_timeout = 110

        self.response     = MakeResponse(msg_ios.LUN_ADD_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_ios.lun_add_request]

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
            return self.AddLunSmartCache()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            return self.AddLunBaseDisk()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            return self.AddLunPalCache()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALRAW:
            return self.AddLunPalRaw()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_PALPMT:
            return self.AddLunPalPmt()
        elif self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            return self.AddLunBaseDev()
        else:
            assert(0)

    def AddLunPalCache(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].palcache_name
        params['disk_id']     = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].disk_id
        params['disk_part']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].disk_part
        params['pool_name']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palcache].Extensions[msg_ios.ext_palcacheinfo_pool_name]
        params['keep_res']    = self.request_body.keep_res
        # FIXME: 添加palcache不能放在线程中操作, 否则其他线程进行scan的时候, 会导致内存指向错误
        result = self.add_lun_with_palcache(params)
        return self.Entry_LunAdd(result)

    def AddLunPalRaw(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].palraw_name
        params['disk_id']     = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].disk_id
        params['disk_part']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palraw].disk_part
        params['keep_res']    = self.request_body.keep_res
        # FIXME: 添加palraw不能放在线程中操作, 否则其他线程进行scan的时候, 会导致内存指向错误
        result = self.add_lun_with_palraw(params)
        return self.Entry_LunAdd(result)

    def AddLunPalPmt(self):
        params = {}
        params['target_name'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].palpmt_name
        params['pool_name']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].Extensions[msg_ios.ext_palpmtinfo_pool_name]
        params['size']        = self.request_body.Extensions[msg_ios.ext_lunaddrequest_palpmt].size
        params['keep_res']    = self.request_body.keep_res
        # FIXME: 添加palpmt不能放在线程中操作, 否则其他线程进行scan的时候, 会导致内存指向错误
        result = self.add_lun_with_palpmt(params)
        return self.Entry_LunAdd(result)

    def AddLunBaseDisk(self):
        params = {}
        params['disk_id']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk].disk_id
        params['disk_part'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_basedisk].disk_part
        params['keep_res']  = self.request_body.keep_res
        self.LongWork(self.add_lun_with_basedisk, params, self.Entry_LunAdd)
        return MS_CONTINUE

    def AddLunBaseDev(self):
        params = {}
        params['dev_name'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_basedev].dev_name
        params['keep_res'] = self.request_body.keep_res
        self.LongWork(self.add_lun_with_basedev, params, self.Entry_LunAdd)
        return MS_CONTINUE

    def AddLunSmartCache(self):
        params = {}
        params['smartcache_id']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].smartcache_id
        params['data_disk_id']    = self.request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].data_disk_id
        params['data_disk_part']  = self.request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].data_disk_part
        params['cache_disk_id']   = self.request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].cache_disk_id
        params['cache_disk_part'] = self.request_body.Extensions[msg_ios.ext_lunaddrequest_smartcache].cache_disk_part
        params['keep_res']        = self.request_body.keep_res
        self.LongWork(self.add_lun_with_cache, params, self.Entry_LunAdd)
        return MS_CONTINUE

    # 带cache的lun
    def add_lun_with_cache(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        smartcache_id   = params['smartcache_id']
        data_disk_id    = params['data_disk_id']
        data_disk_part  = params['data_disk_part']
        cache_disk_id   = params['cache_disk_id']
        cache_disk_part = params['cache_disk_part']

        # 数据盘信息
        data_part = common.GetPartInfo(data_disk_id, data_disk_part)
        if data_part == None:
            rc.retcode = msg_ios.RC_IOS_DISKPART_NOT_EXIST
            rc.message = "part %s,%s not exist" % (data_disk_id, data_disk_part)
            return rc, ''

        # cache盘信息
        cache_part = common.GetPartInfo(cache_disk_id, cache_disk_part)
        if cache_part == None:
            rc.retcode = msg_ios.RC_IOS_DISKPART_NOT_EXIST
            rc.message = "part %s,%s not exist" % (data_disk_id, data_disk_part)
            return rc, ''

        if params['keep_res'] == True:
            e, smartcache_list = APISmartCache().list()
            if e or smartcache_id not in smartcache_list:
                err_msg="Cann't find sc %s, dev:%s, cache:%s, res:%s"%(smartcache_id,data_part['DEVNAME'],cache_part['DEVNAME'],smartcache_list)
                logger.run.error(err_msg)
                rc.retcode = msg_ios.RC_IOS_SMARTCACHE_IS_INVALID
                rc.message = "Smartcache %s is invalid" % (smartcache_id)
                return rc, ''
        else:
            # 检查数据盘和cache盘是否有属于某个在线的dm设备，如果有，则先卸载
            e, smartcache_list = APISmartCache().list()
            if not e:
                for s_id in smartcache_list.keys():
                    e, smartcache_info = APISmartCache().info({"cache_name":s_id})
                    if e: continue
                    if smartcache_info['data_dev'] == data_part['DEVNAME'] or smartcache_info['cache_dev'] == cache_part['DEVNAME']:
                        logger.run.info("Dm remove smartcache %s" % s_id)
                        APISmartCache().dm_remove({"cache_name":s_id})

            # 无论磁盘是否真的做过smartcache,都先清除下磁盘的smartcache-supperblock
            APISmartCache().destroy({"cache_dev":data_part['DEVNAME']})
            APISmartCache().destroy({"cache_dev":cache_part['DEVNAME']})

            # 绑定smartcache
            e, res = APISmartCache().create({'cache_name':smartcache_id, 'data_dev':data_part['DEVNAME'], 'cache_dev':cache_part['DEVNAME']})
            if e:
                err_msg="Create smartcache failed %s, dev:%s, cache:%s, msg:%s"%(smartcache_id, data_part['DEVNAME'], cache_part['DEVNAME'], res)
                logger.run.error(err_msg)
                rc.retcode = msg_ios.RC_IOS_CREATE_SMARTCACHE_FAILED
                rc.message = "Create smartcache failed"
                return rc, ''

        # 获取创建出来的cache信息
        e, part = APISmartCache().info({'cache_name':smartcache_id})
        if e:
            logger.run.error("Get smartcache info:%s failed" % smartcache_id)
            rc.retcode = msg_ios.RC_IOS_LIST_SMARTCACHE_FAILED
            rc.message = "Get smartcache info failed"
            return rc, ''
        return rc, {'DEVNAME':part['DEVNAME']}
    
    def add_lun_with_basedisk(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        disk_id   = params['disk_id']
        disk_part = params['disk_part']

        part = common.GetPartInfo(disk_id, disk_part)
        if part == None:
            rc.retcode = msg_ios.RC_IOS_DISKPART_NOT_EXIST
            rc.message = "part %s,%s not exist" % (disk_id, disk_part)
            return rc, ''
        return rc, {'DEVNAME':part['DEVNAME']}

    def add_lun_with_basedev(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        if not os.path.exists(params['dev_name']):
            rc.retcode = msg_ios.RC_IOS_DEV_NOT_EXIST
            rc.message = "Device %s not exist" % params['dev_name']
            return rc, ''
        return rc, {'DEVNAME':params['dev_name']}

    def add_lun_with_palcache(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])
        pool_name   = str(params['pool_name'])
        disk_id     = params['disk_id']
        disk_part   = params['disk_part']

        # 首先检查数据盘是否存在
        part = common.GetPartInfo(disk_id, disk_part)
        if part == None:
            rc.retcode = msg_ios.RC_IOS_DISKPART_NOT_EXIST
            rc.message = "part %s,%s not exist" % (disk_id, disk_part)
            return rc, ''

        if params['keep_res'] == True:
            # 检查target是否存在
            e, target_list = apipal.Target().get_target_list()
            if e or target_name not in [target.name() for target in target_list]:
                err_msg="Cann't find target %s, dev:%s, res:%s"%(target_name, part['DEVNAME'], target_list)
                logger.run.error(err_msg)
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_IS_INVALID
                rc.message = "PAL-Target %s is invalid" % (target_name)
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name)}
        else:
            # 添加磁盘
            e, res = apipal.Disk().add_disk(part['DEVNAME'], False)
            if e:
                if res.find("already added in PAL") != -1:
                    e, res = apipal.Disk().del_disk(part['DEVNAME'])
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                        rc.message = "pal add disk failed :%s" % res
                        return rc, ''
                    e, res = apipal.Disk().add_disk(part['DEVNAME'], False)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                        rc.message = "pal add disk failed  :%s" % res
                        return rc, ''
                else:
                    rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                    rc.message = "pal add disk failed  :%s" % res
                    return rc, ''
            # 创建target 
            e, res = apipal.Target().add_target_palcache(target_name, pool_name, part['DEVNAME'])
            if e:
                if res.find("target already exists") != -1:
                    e, res = apipal.Target().del_target(target_name)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed :%s" % res
                        return rc, ''
                    time.sleep(2)
                    e, res = apipal.Target().add_target_palcache(target_name, pool_name, part['DEVNAME'])
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed  :%s" % res
                        return rc, ''
                else:
                    rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                    rc.message = "pal add target failed  :%s" % res
                    return rc, ''
            # 补充pal的pal-id, 和target-id
            e, target_list = apipal.Target().get_target_list()
            if e:
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_LIST_FAILED
                rc.message = "Get target list failed:%s" % target_list
                return rc, ''
            target_pal_id = None
            target_id     = None
            for target in target_list:
                if str(target.name()) == str(target_name):
                    target_pal_id = target.id()
                    target_id     = str(target.uuid())
                    break
            if target_pal_id == None or target_id == None:
                rc.retcode = msg_ios.RC_IOS_GET_TARGET_ID_FAILED
                rc.message = "Get target id failed"
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name), 'target_pal_id':target_pal_id, 'target_id':target_id}

    def add_lun_with_palraw(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])
        disk_id     = params['disk_id']
        disk_part   = params['disk_part']

        # 首先检查数据盘是否存在
        part = common.GetPartInfo(disk_id, disk_part)
        if part == None:
            rc.retcode = msg_ios.RC_IOS_DISKPART_NOT_EXIST
            rc.message = "part %s,%s not exist" % (disk_id, disk_part)
            return rc, ''

        if params['keep_res'] == True:
            # 检查target是否存在
            e, target_list = apipal.Target().get_target_list()
            if e or target_name not in [target.name() for target in target_list]:
                err_msg="Cann't find target %s, dev:%s, res:%s"%(target_name, part['DEVNAME'], target_list)
                logger.run.error(err_msg)
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_IS_INVALID
                rc.message = "PAL-Target %s is invalid" % (target_name)
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name)}
        else:
            # 添加磁盘
            e, res = apipal.Disk().add_disk(part['DEVNAME'], False)
            if e:
                if res.find("already added in PAL") != -1:
                    e, res = apipal.Disk().del_disk(part['DEVNAME'])
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                        rc.message = "pal add disk failed :%s" % res
                        return rc, ''
                    e, res = apipal.Disk().add_disk(part['DEVNAME'], False)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                        rc.message = "pal add disk failed  :%s" % res
                        return rc, ''
                else:
                    rc.retcode = msg_ios.RC_IOS_PAL_DISK_ADD_FAILED
                    rc.message = "pal add disk failed  :%s" % res
                    return rc, ''
            # 创建target 
            e, res = apipal.Target().add_target_palraw(target_name, part['DEVNAME'])
            if e:
                if res.find("target already exists") != -1:
                    e, res = apipal.Target().del_target(target_name)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed :%s" % res
                        return rc, ''
                    time.sleep(2)
                    e, res = apipal.Target().add_target_palraw(target_name, part['DEVNAME'])
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed  :%s" % res
                        return rc, ''
                else:
                    rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                    rc.message = "pal add target failed  :%s" % res
                    return rc, ''
            # 补充pal的pal-id, 和target-id
            e, target_list = apipal.Target().get_target_list()
            if e:
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_LIST_FAILED
                rc.message = "Get target list failed:%s" % target_list
                return rc, ''
            target_pal_id = None
            target_id     = None
            for target in target_list:
                if str(target.name()) == str(target_name):
                    target_pal_id = target.id()
                    target_id     = str(target.uuid())
                    break
            if target_pal_id == None or target_id == None:
                rc.retcode = msg_ios.RC_IOS_GET_TARGET_ID_FAILED
                rc.message = "Get target id failed"
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name), 'target_pal_id':target_pal_id, 'target_id':target_id}

    def add_lun_with_palpmt(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS

        target_name = str(params['target_name'])
        pool_name   = params['pool_name']
        size        = params['size']

        if params['keep_res'] == True:
            # 检查target是否存在
            e, target_list = apipal.Target().get_target_list()
            if e or target_name not in [target.name() for target in target_list]:
                err_msg="Cann't find target %s, res:%s"%(target_name, target_list)
                logger.run.error(err_msg)
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_IS_INVALID
                rc.message = "PAL-Target %s is invalid" % (target_name)
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name)}
        else:
            # 创建target 
            e, res = apipal.Target().add_target_palpmt(target_name, pool_name, size)
            if e:
                if res.find("target already exists") != -1:
                    e, res = apipal.Target().del_target(target_name)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed :%s" % res
                        return rc, ''
                    time.sleep(2)
                    e, res = apipal.Target().add_target_palpmt(target_name, pool_name, size)
                    if e:
                        rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                        rc.message = "pal add target failed  :%s" % res
                        return rc, ''
                else:
                    rc.retcode = msg_ios.RC_IOS_PAL_TARGET_ADD_FAILED
                    rc.message = "pal add target failed  :%s" % res
                    return rc, ''
            # 补充pal的pal-id, 和target-id
            e, target_list = apipal.Target().get_target_list()
            if e:
                rc.retcode = msg_ios.RC_IOS_PAL_TARGET_LIST_FAILED
                rc.message = "Get target list failed:%s" % target_list
                return rc, ''
            target_pal_id = None
            target_id     = None
            for target in target_list:
                if str(target.name()) == str(target_name):
                    target_pal_id = target.id()
                    target_id     = str(target.uuid())
                    break
            if target_pal_id == None or target_id == None:
                rc.retcode = msg_ios.RC_IOS_GET_TARGET_ID_FAILED
                rc.message = "Get target id failed"
                return rc, ''
            return rc, {'DEVNAME':os.path.join("/dev", target_name), 'target_pal_id':target_pal_id, 'target_id':target_id}

    def Entry_LunAdd(self, result):
        rc, device = result
        if rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(rc)
            self.SendResponse(self.response)
            return MS_FINISH

        apismartscsi = APISmartScsi()

        # 如果是新创建的lun, 则需要dd一下对应的设备
        if self.request_body.keep_res == False:
            e = apismartscsi.zero_device(device['DEVNAME'])
            if e:
                logger.run.error("Zero device failed:%s" % apismartscsi.errmsg)
                self.response.rc.retcode = msg_ios.RC_IOS_ZERO_DEVICE_FAILED
                self.response.rc.message = "Zero device %s failed:%s" % (params['path'], apismartscsi.errmsg)
                self.SendResponse(self.response)
                return MS_FINISH

        params = {}
        if self.group_name:
            params["group_name"] = self.group_name
        params['device_name'] = "%s_%s" % (self.request_body.node_name, self.request_body.lun_name)
        params['path']        = device['DEVNAME']
        params['t10_dev_id']  = self.request_body.lun_id[:23]
        logger.run.info("Start create lun, device:%s, dev:%s ,group:%s" % (params['device_name'], params['path'],self.group_name))
        apismartscsi = APISmartScsi()
        e = apismartscsi.add_lun(params)
        if e:
            logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
            self.response.rc.retcode = msg_ios.RC_IOS_ADD_LUN_FAILED
            self.response.rc.message = "Lun add failed:%s" % apismartscsi.errmsg
            self.SendResponse(self.response)
            return MS_FINISH

        # 针对于basedev类型的资源, 补充lun的size
        if self.request_body.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            lun_list = apismartscsi.get_lun_list()
            for lun_name, lun_info in lun_list.items():
                if lun_name == params['device_name'] and lun_info['attrs']['t10_dev_id'] == params['t10_dev_id']:
                    self.response.body.Extensions[msg_ios.lun_add_response].size = lun_info['attrs']['size_mb']*1048576/512
                    break
        if self.request_body.lun_type in [msg_pds.LUN_TYPE_PALCACHE, msg_pds.LUN_TYPE_PALRAW, msg_pds.LUN_TYPE_PALPMT] \
                and self.request_body.keep_res == False:
            self.response.body.Extensions[msg_ios.lun_add_response].target_pal_id = device['target_pal_id']
            self.response.body.Extensions[msg_ios.lun_add_response].target_id     = device['target_id']

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
