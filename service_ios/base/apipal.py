# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, ctypes
sys.path.append(os.path.abspath("/opt/pal"))

from pylib import pypal
from pylib.pypal import PMT_Attr, Raw_Attr, Cache_Attr, CACHE_MODE_WRITEBACK, PAL_INDEX_NULL, DISK_TYPE_SSD
from pylib.pypal import SECTOR_PER_EXTENT_MAX, SECTOR_PER_EXTENT_MIN
from pylib.pypal import SECTOR_PER_BUCKET_MAX, SECTOR_PER_BUCKET_MIN
from pylib.pypal import SECTOR_PER_SIPPET_MAX, SECTOR_PER_SIPPET_MIN

TARGET_LOADED        = pypal.TARGET_LOADED
POOL_LEVEL_PILE      = pypal.POOL_LEVEL_PILE
POOL_STATE_LOADING   = pypal.POOL_STATE_LOADING
POOL_STATE_MIGRATING = pypal.POOL_STATE_MIGRATING

# target type
TARGET_TYPE_UNKNOWN = pypal.PAL_SPEC_UNKNOWN
TARGET_TYPE_CACHE   = pypal.PAL_SPEC_CACHE
TARGET_TYPE_PMT     = pypal.PAL_SPEC_PMT
TARGET_TYPE_RAW     = pypal.PAL_SPEC_RAW

# pool length type
POOL_LENGTH_UNKNOWN  = pypal.POOL_LENGTH_UNKNOWN
POOL_LENGTH_FIXED    = pypal.POOL_LENGTH_FIXED
POOL_LENGTH_VARIABLE = pypal.POOL_LENGTH_VARIABLE

# 脏数据刷新速度等级
SYNC_LEVEL = { \
        0:(0,        50, 50), 
        1:(2<<5,     50, 50),
        2:(2<<6,     50, 50),
        3:(2<<7,     50, 50),
        4:(2<<8,     50, 50),
        5:(2<<9,     50, 50),
        6:(2<<10,    50, 50),
        7:(2<<11,    50, 50),
        8:(2<<12,    50, 50),
        9:(2<<14,    50, 50),
       10:((2<<15)-1, 0,  0),
        }

Kilo = 1024
Mega = Kilo * Kilo
Giga = Mega * Kilo

def GetSyncLevel(a1, a2, a3):
    for level, value in SYNC_LEVEL.items():
        if value[0] == a1 and value[1] == a2 and value[2] == a3:
            return level
    return -1

def testBit(int_type, offset):
    return(int_type & (1 << offset))

class Platform():
    def driver_configure_get_target_id(self): 
        try:
            platform = pypal.Platform_get_platform()
            return 0, platform.driver_configure_get_target_id()
        except Exception as e:
            return -1, e

    def driver_configure_set_target_id(self, target_id): 
        try:
            platform = pypal.Platform_get_platform()
            return 0, platform.driver_configure_set_target_id(target_id)
        except Exception as e:
            return -1, e

class Disk():
    # 获取磁盘列表
    def get_disk_list(self, *args, **kwargs): 
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            disks = platform.get_disks()
        except Exception as e:
            return -1, str(e)
        return 0, disks

    # Load磁盘
    def load_disk(self, path_name, spec_type=None, pool_name=None):
        ## 正常方式载入
        # use load_disk(path_name)
        ## pool丢失, 载入disk 变成raw
        # use load_disk(path_name, spec_type=raw)
        ## raw载入同时指定pool
        # use load_disk(path_name, spec_type=cache, pool_name=pool_name)
        assert(spec_type == None or spec_type == "raw" or spec_type == "cache")
        assert((spec_type=="cache" and pool_name!=None) or (spec_type==None and pool_name==None) or (spec_type=="raw" and pool_name==None))
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            para = None
            # disk load /dev/sdX
            if spec_type == None:
                para = None
            # disk load /dev/sdX raw
            if spec_type == "raw":
                para = pypal.MD_Load_Parameter(pypal.PAL_SPEC_RAW)
            # disk load /dev/sdX cache pool_name
            if spec_type == "cache":
                para = pypal.MD_Load_Parameter(pypal.PAL_SPEC_CACHE)
                para.set_pool_name(str(pool_name))

            disk = platform.find_disk(path_name)
            if disk != None:
                if disk.is_online():
                    raise Exception("disk '%s' already loaded in PAL" % path_name)
                else:
                    disk.load(para)
                    disk.info_sync()
            else:
                disk = platform.create_and_scan_offline_disk(path_name);
                if disk == None:
                    raise Exception("offline scan disk '%s' failed" % path_name)
                disk.load(para)
                disk.info_sync();
                platform.insert_disk(disk);
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 添加磁盘, 添加MD/SSD盘统一操作
    def add_disk(self, path_name, is_ssd):
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            disk = platform.find_disk(path_name)
            if disk == None:
                if is_ssd:
                    platform.create_and_add_ssd(path_name)
                else:
                    platform.create_and_add_md(path_name)
            elif not disk.is_online():
                platform.del_and_destroy_disk(path_name);
                platform.create_and_add_ssd(path_name);
            else:
                raise Exception("disk '%s' already added in PAL" % path_name)
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 删除磁盘
    def del_disk(self, path_name):
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            disk = platform.find_disk(path_name)
            if disk == None:
                raise Exception("disk '%s' not added in PAL" % path_name)
            platform.del_and_destroy_disk(path_name);
        except Exception as e:
            return -1, str(e)
        return 0, ""

class Pool():
    # 通过pool名获取pool结构
    def get_by_name(self, pool_name):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
        except Exception as e:
            return -1, str(e)
        return 0, pool
    
    # 获取pool的在线状态
    def get_pool_stat(self, pool_name):
        pool_name = str(pool_name)
        state = {}
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            sippet_num              = pool.get_cache_sippets()*len(pool.get_disks())
            # valid
            state['valid']          = platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_VALID)
            state['p_valid']        = 100.0*state['valid']/sippet_num
            # dirty
            state['dirty']          = platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_DIRTY)
            state['p_dirty']        = 100.0*state['dirty']/sippet_num
            # error
            state['error']          = platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_ERROR)
            # thresh
            sippet_per_bucket       = pool.bucket_sectors()/pool.sippet_sectors()
            dirty_thresh            = platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_DIRTY_THRESH)
            # lower_thresh
            state['lower_thresh']   = ctypes.c_uint32(dirty_thresh).value
            # p_lower_thresh
            state['p_lower_thresh'] = int(100.0*state['lower_thresh']/sippet_per_bucket)
            # upper_thresh
            state['upper_thresh']   = ctypes.c_uint32(dirty_thresh>>32).value
            # p_upper_thresh
            state['p_upper_thresh'] = int(100.0*state['upper_thresh']/sippet_per_bucket)
            # dirty level
            state['sync_level']     = GetSyncLevel(platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_MAX_SYNC_IO), \
                                                   platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_SYNC_FRONTEND_WAITING_MS), \
                                                   platform.get_pool_stat(pool_name, pypal.PAL_ATTR_POOL_SYNC_IO_SCAN_MS))
        except Exception as e:
            return -1, str(e)
        return 0, state

    # 根据给定的参数, 计算支持的最大pool-size
    def calc_max_pool_size(self, disk_size, attr={}, len_mode=POOL_LENGTH_FIXED):
        extent_sectors = "extent" in attr.keys() and attr['extent'] or 1*Giga/512
        bucket_sectors = "bucket" in attr.keys() and attr['bucket'] or 8*Mega/512

        if "sippet" in attr.keys():
            sippet_sectors = attr['sippet']
        else:
            if len_mode == POOL_LENGTH_VARIABLE:
                sippet_sectors = 64*Kilo/512
            else:
                sippet_sectors = 8*Kilo/512

        try:
            platform = pypal.Platform_get_platform()
            size = platform.calc_max_pool_cache_size(disk_size, extent_sectors, bucket_sectors, sippet_sectors, len_mode)
        except Exception as e:
            return -1, str(e)
        return 0, size

    # 获取存储池列表
    def get_pool_list(self, *args, **kwargs): 
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pools = platform.get_pools()
        except Exception as e:
            return -1, str(e)
        return 0, pools

    # 设置pool trough
    def wb2wt(self, pool_name, is_start):
        pool_name = str(pool_name)
        state = {}
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            if is_start:
                pool.wb2wt_start()
            else:
                pool.wb2wt_stop()
        except Exception as e:
            return -1, str(e)
        return 0, ''

    # 添加存储池
    def add_pool(self, pool_name, cache_per_disk, pool_type, attr={}, is_variable=False):
        pool_name = str(pool_name)
        extent_sectors = "extent" in attr.keys() and attr['extent'] or 1*Giga/512
        bucket_sectors = "bucket" in attr.keys() and attr['bucket'] or 8*Mega/512
        len_mode = POOL_LENGTH_FIXED
        if is_variable == True:
            len_mode = POOL_LENGTH_VARIABLE

        if "sippet" in attr.keys():
            sippet_sectors = attr['sippet']
        else:
            if len_mode == POOL_LENGTH_VARIABLE:
                sippet_sectors = 64*Kilo/512
            else:
                sippet_sectors = 8*Kilo/512

        try:
            if pool_type.lower() != "pile":
                raise Exception("pool type only support 'pile' now")
            def is_power_of_2(v):
                return ( v != 0 ) and ( (v & (v-1)) == 0 )
            if cache_per_disk % extent_sectors != 0:
                cache_per_disk = (cache_per_disk/extent_sectors)*extent_sectors
            if cache_per_disk == 0:
                raise Exception("cache per disk is 0")
            if extent_sectors > cache_per_disk or extent_sectors > SECTOR_PER_EXTENT_MAX or extent_sectors < SECTOR_PER_EXTENT_MIN:
                raise Exception("Invalid extent_sectors=%s" % extent_sectors)
            if extent_sectors % bucket_sectors != 0:
                raise Exception("extent_sectors '%s' is not multiple of bucket_sectors '%s'" % (extent_sectors, bucket_sectors))
            if bucket_sectors > extent_sectors or not is_power_of_2(bucket_sectors) or \
                    bucket_sectors > SECTOR_PER_BUCKET_MAX or bucket_sectors < SECTOR_PER_BUCKET_MIN:
                raise Exception("Invalid bucket_sectors=%s" % bucket_sectors)
            if sippet_sectors > bucket_sectors or not is_power_of_2(sippet_sectors) or \
                    sippet_sectors > SECTOR_PER_SIPPET_MAX or bucket_sectors < SECTOR_PER_SIPPET_MIN:
                raise Exception("Invalid sippet_sectors=%s" % sippet_sectors)
            if bucket_sectors / sippet_sectors > PAL_INDEX_NULL:
                raise Exception("bucket_sectors '%s' is too larget for sippet_sectors '%s'" % (bucket_sectors, sippet_sectors))
            if len_mode == POOL_LENGTH_VARIABLE and (sippet_sectors<16 or sippet_sectors>256):
                raise Exception("When pool's length is variable, sippet should be range from 8k to 128k")
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            platform.create_and_add_pool(pool_name, POOL_LEVEL_PILE, cache_per_disk, extent_sectors, bucket_sectors, sippet_sectors, len_mode)
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 删除存储池
    def del_pool(self, pool_name):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            platform.del_and_destroy_pool(pool_name);
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 存储池容量修改
    def resize_pool(self, pool_name, size):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            pool.resize_cache((size<<30)/512);
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 存储池中添加磁盘
    def insert_ssd(self, pool_name, path_name, meta_type="local"):
        pool_name = str(pool_name)
        try:
            if meta_type.lower() != 'local':
                raise Exception("meta type only support 'local' now")
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            disk = platform.find_disk(path_name)
            if disk == None:
                raise Exception("disk '%s' not added in PAL" % pool_name)
            if not disk.is_online():
                raise Exception("disk '%s' is not online" % pool_name)
            if disk.type() != DISK_TYPE_SSD:
                raise Exception("disk '%s' is not ssd" % pool_name)
            pool.insert_disk(disk)
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 存储池中删除磁盘
    def remove_ssd(self, pool_name, path_name):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            disk = platform.find_disk(path_name)
            if disk == None:
                raise Exception("disk '%s' not added in PAL" % pool_name)
            pool.remove_disk(disk)
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 重新load存储池, 在动态insert/remove池的时候使用
    def run(self, pool_name):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not added in PAL" % pool_name)
            pool.run()
            pool.info_sync();
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 设置pool的dirty thresh
    def set_dirty_thresh(self, pool_name, lower, upper):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            platform.set_pool_thresh(pool_name, pypal.PAL_ATTR_POOL_DIRTY_THRESH, lower + (upper << 32))
        except Exception as e:
            return -1, str(e)
        return 0, ""
    
    # 设置脏数据刷新等级 
    def set_sync_level(self, pool_name, level):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            platform.set_pool_thresh(pool_name, pypal.PAL_ATTR_POOL_MAX_SYNC_IO,              SYNC_LEVEL[level][0])
            platform.set_pool_thresh(pool_name, pypal.PAL_ATTR_POOL_SYNC_FRONTEND_WAITING_MS, SYNC_LEVEL[level][1])
            platform.set_pool_thresh(pool_name, pypal.PAL_ATTR_POOL_SYNC_IO_SCAN_MS,          SYNC_LEVEL[level][2])
        except Exception as e:
            return -1, str(e)
        return 0, ""

class Target():
    # 获取target的状态
    def get_target_stat(self, target_name):
        target_name = str(target_name)
        state = {}
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            state['skip_thresh'] = int(platform.get_target_stat(target_name, pypal.PAL_ATTR_TARGET_SEQUENTIAL_IO))
        except Exception as e:
            return -1, str(e)
        return 0, state

    # 设置target的skip thresh
    def set_skip_thresh(self, target_name, skip_thresh):
        target_name = str(target_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            s = (skip_thresh<<10)/512
            platform.set_target_thresh(target_name, pypal.PAL_ATTR_TARGET_SEQUENTIAL_IO, s)
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 获取target列表
    def get_target_list(self): 
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            targets = platform.get_targets()
        except Exception as e:
            return -1, str(e)
        return 0, targets

    # 添加cache target
    def add_target_palcache(self, target_name, pool_name, md_path, mode=CACHE_MODE_WRITEBACK, mda=1024):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool   = platform.find_pool(pool_name)
            disk   = platform.find_disk(md_path)
            if pool == None:
                raise Exception("pool '%s' not exist" % pool_name)
            if disk == None:
                raise Exception("md '%s' not exist" % md_path)
            target = pypal.Platform_get_platform().create_and_add_cache(target_name)
            attr   = Cache_Attr(pool_name, md_path, mode, mda)
            attr.thisown = 0
            target.set_attr(attr)
            try:
                target.load()
                target.info_sync()
            except Exception as e:
                pypal.Platform_get_platform().del_and_destroy_target(target_name);
                raise e
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 添加raw target
    def add_target_palraw(self, target_name, md_path, alignment=1024):
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            disk   = platform.find_disk(md_path)
            if disk == None:
                raise Exception("md '%s' not exist" % md_path)
            target = pypal.Platform_get_platform().create_and_add_raw(target_name)
            attr   = Raw_Attr(disk, alignment)
            attr.thisown = 0
            target.set_attr(attr)
            try:
                target.load()
                target.info_sync()
            except Exception as e:
                pypal.Platform_get_platform().del_and_destroy_target(target_name);
                raise e
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 添加pmt target
    def add_target_palpmt(self, target_name, pool_name, size):
        pool_name = str(pool_name)
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            pool   = platform.find_pool(pool_name)
            if pool == None:
                raise Exception("pool '%s' not exist" % pool_name)
            target = pypal.Platform_get_platform().create_and_add_pmt(target_name)
            attr   = PMT_Attr(pool, (size<<30)/512)
            attr.thisown = 0
            target.set_attr(attr)
            try:
                target.load()
                target.info_sync()
            except Exception as e:
                pypal.Platform_get_platform().del_and_destroy_target(target_name);
                raise e
        except Exception as e:
            return -1, str(e)
        return 0, ""

    # 删除target
    def del_target(self, target_name):
        try:
            platform = pypal.Platform_get_platform()
            platform.scan(True)
            platform.del_and_destroy_target(target_name)
        except Exception as e:
            return -1, str(e)
        return 0, ""

if __name__ == "__main__":
    pass

    # ==================================
    # platform操作
    # ==================================
    # platform = Platform()
    # print platform.driver_configure_get_target_id()
    # print platform.driver_configure_set_target_id(100)

    # ==================================
    # target操作
    # ==================================
    # target = Target()
    # print target.get_target_list()
    # print dir(target.get_target_list()[1][0])
    # print target.get_target_stat("target01")
    # print target.get_target_list()[1][0].name()
    # print target.get_target_list()[1][0].id()
    # print target.get_target_list()[1][0].uuid()
    # print target.get_target_list()[1][0].type()
    # print target.get_target_list()[1][0].type_str()
    # print target.get_target_list()[1][0].state()
    # print target.get_target_list()[1][0].state_str()
    # print target.get_target_list()[1][0].capacity()
    # print target.get_target_list()[1][0].mode_str()
    # print target.get_target_list()[1][0].id()
    # print target.add_target_palcache("xx15", "p1", "/dev/sdo")
    # print target.add_target_palraw("xx", "/dev/sdb1")
    # print target.del_target("xx15")

    # ==================================
    # disk操作
    # ==================================
    # disk = Disk()
    # e, disk_list = disk.get_disk_list()
    # for disk in disk_list:
    #    print disk.path_name()
    # print disk.add_disk("/dev/sdq", False)
    # print disk.del_disk("/dev/sdx")
    # load磁盘是不分ssd/还是hdd的
    # 只有当pool下的所有ssd都load成功后,pool才能生效, 且是自动load
    # hddload成功后, target会建立成功
    # print disk.load_disk("/dev/sdi2")
    # 只有当pool下的所有target为load回来后, pool才会running
    # print disk.load_disk("/dev/sdc2", "cache", "pool01")

    # ==================================
    # pool操作
    # ==================================
    pool = Pool()
    print pool.get_pool_stat("pool01")
    # print pool.calc_max_pool_size(937698959)
    # for pool in pool.get_pool_list()[1]:
    #     print testBit(pool.state(), pypal.POOL_STATE_MIGRATE_START)
    # print p.state()
    # for p in  pool.get_pool_list()[1]:
        # print "%s : %s" % (p.name(), p.cache_per_disk())
    #     print p.get_disks()
    #     print p.cache_per_disk()
    # print pool.add_pool("pool01", 41943040, "pile")# 40*1024*1024*1024/512)
    # print pool.del_pool("p2")
    # 假如要动态更换ssd, 操作的过程如下, 先insert新的ssd,再remove老的ssd, 然后执行run, 当迁移完成后就2个盘就会真正替换
    # print pool.insert_ssd("pool01", "/dev/sdj1")
    # print pool.remove_ssd("p1", "/dev/sdd")
    # 当把pool下的所有ssdload起来的时候, pool会自动run
    # 当新建pool时, 创建完成后需要run下
    # 当执行remove/insert的后, 如果需要生效,必须执行run,否则盘没有生效,但是disk属性可以看到这个状态
    # print pool.run("pool01")
