#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

import re, pyudev

from pdsframe.common.long_work import command
from service_ios.base.cmdlist import *

from service_ios.base.common import get_mount_list, is_flash, SMARTCACHE_BLOCKSZ

class APISmartCache:
    def list(self, params={}):
        e, out = command("%s ls --target=smartcache" % DMSETUP)
        if e:return e, out

        cachedevs = {}
        devreg = ur"(\S+)\s+\((\d+),\s+(\d+)\)"
        for row in out.splitlines():
            result = re.search(devreg, row)
            if result:
               name = result.group(1)
               cachedevs[name] = {}
               cachedevs[name]["major"] = result.group(2)
               cachedevs[name]["minor"] = result.group(3)

        mount_list = get_mount_list()

        # 补充udev信息
        context = pyudev.Context()
        disks =  context.list_devices(subsystem='block', DEVTYPE='disk')
        for disk in disks:
            if 'DM_NAME' in disk.keys() and disk['DM_NAME'] in cachedevs.keys():
                # XXX: 此处使用dev/mapper/XXX为设备名称，而没有使用DEVNAME
                # 原因是blkid命令下，看不到/dev/dm-X的uuid，且两边的uuid不同步
                cachedevs[disk['DM_NAME']]['DEVNAME'] = "/dev/mapper/%s" % str(disk['DM_NAME'])
                if cachedevs[disk['DM_NAME']]['DEVNAME'] in mount_list.keys():
                    cachedevs[disk['DM_NAME']]['MOUNT_POINT'] = mount_list[cachedevs[disk['DM_NAME']]['DEVNAME']]
        return 0, cachedevs

    def create(self, params={}):
        cache_name = params['cache_name']
        cache_dev  = params['cache_dev']
        data_dev   = params['data_dev']
        cmd = "%s -p back -b %s %s %s %s" % (SMARTCACHE_CREATE, SMARTCACHE_BLOCKSZ, cache_name, cache_dev, data_dev)
        return command(cmd)

    def destroy(self, params={}):
        cache_dev  = params['cache_dev']
        return command("%s %s -f" % (SMARTCACHE_DESTORY, cache_dev))

    def load(self, params={}):
        cache_dev = params['cache_dev']
        data_dev  = params['data_dev']
        cmd = "%s %s %s" % (SMARTCACHE_LOAD, cache_dev, data_dev)
        return command(cmd)

    def dm_remove(self, params={}):
        cache_name  = params['cache_name']
        return command("%s remove %s" % (DMSETUP, cache_name))

    def info(self, params={}):
        e, cache_list = self.list()
        if e: return e, cache_list

        if params['cache_name'] not in cache_list.keys():
            return -1, "Target cache is not exist"

        e, out = command("%s table %s" % (DMSETUP,params['cache_name']))
        if e: return e, out

        cache_info = cache_list[params['cache_name']]

        devreg = ur"\s+ssd dev \((\S+)\), disk dev \((\S+)\) cache mode\((\S+)\)"
        for line in out.splitlines():
            result = re.search(devreg, line)
            if result:
                cache_info["cache_dev"] = result.group(1)
                cache_info["data_dev"] = result.group(2)
                break
        return 0, cache_info
