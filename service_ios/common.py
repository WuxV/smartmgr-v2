# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import pyudev
import shutil, json, time, errno
from pdsframe import *
from pdsframe.common.long_work import command
from service_ios import g
from service_ios.base.apidisk import APIDisk
from service_ios.base import apipal
from service_ios.base.apismartscsi import APISmartScsi
from service_ios.base.common import get_os_version
from service_ios.base.cmdlist import *
import message.pds_pb2 as msg_pds

def GetPoolExportInfoByName(pool_name):
    e, pool_list = apipal.Pool().get_pool_list()
    if e: return None

    # 获取pool导出基本信息
    pool_export_info = msg_pds.PoolExportInfo()
    for pool in pool_list:
        if pool.name() == pool_name:
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

            context = pyudev.Context()
            # 获取pool所在磁盘可提供的最大pool容量
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
            return pool_export_info

    return None

def GetPartInfo(uuid, disk_part, disk_list=None):
    # 如果没有指定disk list, 则实时获取, 否则使用传入的disk list
    # 解决外部如果循环调用该方法, 将导致获取磁盘列表动作非常消耗资源
    if disk_list == None:
        e, _disk_list = APIDisk().get_disk_list()
        if e: return None
        disk_list = _disk_list

    for disk in disk_list:
        if disk.has_key('HEADER') and str(disk['HEADER']['uuid']) == uuid:
            for part in disk['PARTS']:
                _index = part['INDEX']
                if int(_index) == int(disk_part):
                    return part
    return None

def CheckDriverConfigure(target_ids):
    e, target_id = apipal.Platform().driver_configure_get_target_id()
    if e:
        logger.run.error("Driver configure get target id failed %s:%s" % (e, target_id))
        sys.exit(-1)
    logger.run.debug("Driver configure get target id %s" % target_id)
    if target_id == -1*errno.EINVAL:
        if len(target_ids) == 0:
            _target_id = 0
        else:
            target_ids.sort()
            _target_id = target_ids[-1]+10
        logger.run.info("Start set target id to :%s" % _target_id)
        e, target_id = apipal.Platform().driver_configure_set_target_id(_target_id)
        if e:
            logger.run.error("Driver configure set target id failed %s:%s" % (e, target_id))
            sys.exit(-1)
    elif target_id < 0:
        logger.run.error("Driver configure get target id inside failed %s:%s" % (e, target_id))
        sys.exit(-1)

    with open("/proc/modules", 'r') as pmodules:
        modules   = [module.split()[0] for module in pmodules.read().strip().splitlines()]
        miss_list = []
        for r_m in ["pal", "pal_pile", "pal_cache", "pal_pmt", "pal_raw"]:
            if r_m not in modules:
                e, res = command("%s %s" % (MODPROBE,r_m))
                logger.run.debug("Modprobe:%s:%s:%s" % (r_m, e, res))

    with open("/proc/modules", 'r') as pmodules:
        modules   = [module.split()[0] for module in pmodules.read().strip().splitlines()]
        miss_list = []
        for r_m in ["pal", "pal_pile", "pal_cache"]:
            if r_m not in modules:
                miss_list.append(r_m)

        if len(miss_list) != 0:
            logger.run.error("Miss module : %s" % ",".join(miss_list))
            sys.exit(-1)
    return
