#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

# 其他
from service_ios.base.common import get_os_version
e, s = get_os_version()
if e:
    PARTPROBE                   = "partprobe"
    PARTED                      = "parted"
    MODPROBE                    = "modprobe"    
    DMSETUP                     = "dmsetup"
    SMARTCACHE_CREATE           = "smartcache_create"
    SMARTCACHE_DESTORY          = "smartcache_destroy"
    SMARTCACHE_SETIOCTL         = "smartcache_setioctl"
else:
    if s == "systemv7":
        PARTPROBE                   = "/usr/sbin/partprobe"
        PARTED                      = "/usr/sbin/parted"
        MODPROBE                    = "/usr/sbin/modprobe"    
        DMSETUP                     = "/usr/sbin/dmsetup"
        SMARTCACHE_CREATE           = "/usr/sbin/smartcache_create"
        SMARTCACHE_DESTORY          = "/usr/sbin/smartcache_destroy"
        SMARTCACHE_SETIOCTL         = "/usr/sbin/smartcache_setioctl"
    else:
        PARTPROBE                   = "/sbin/partprobe"
        PARTED                      = "/sbin/parted"
        MODPROBE                    = "/sbin/modprobe"    
        DMSETUP                     = "/sbin/dmsetup"
        SMARTCACHE_CREATE           = "/sbin/smartcache_create"
        SMARTCACHE_DESTORY          = "/sbin/smartcache_destroy"
        SMARTCACHE_SETIOCTL         = "/sbin/smartcache_setioctl"
# SmartCache相关操作
SMARTCACHE_LOAD             = "/opt/smartmgr/scripts/smartcache_load"
