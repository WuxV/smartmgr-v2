#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

import re, pyudev, psutil
import ConfigParser
from pdsframe import *
import platform

FLASH_PREFIX       = config.safe_get('model-config', 'flash-prefix')
SMARTCACHE_BLOCKSZ = config.safe_get('model-config', 'smartcache-blocksz', '8k').lower()

# 通过/dev/XXXN获取分区的index号
def get_disk_disk_part(dev_name):
    e = ur".*\D+?(\d+)$"
    result = re.search(e, dev_name).groups()
    if result == None:
        return None
    return result[0]

# 获取所有挂载点
def get_mount_list():
    mount_list = {}
    for p in psutil.disk_partitions():
        mount_list[p.device] = p.mountpoint
    return mount_list

# 根据盘符判断是否是flash
def is_flash(path):
    label = path.split('/dev/')[1]
    for prefix in FLASH_PREFIX.split(','):
        if label.startswith(prefix):
            return True
    return False

# 根据判断是否是nvme盘
def is_nvme(path):
    label = path.split('/dev/')[1]
    if label.startswith("nvme"):
        return True
    else:
        return False

# 判断是否是df保存卡
def is_df(path):
    label = path.split('/dev/')[1]
    if label.startswith("df"):
        return True
    else:
        return False

# 判断磁盘raid卡是否是dell机器
def is_dell_perc():
    is_dell = False
    if os.path.exists('/proc/scsi/scsi'):
        with open("/proc/scsi/scsi") as f:
            for line in f.readlines():
                s = re.search(r"Model: PERC",line)
                if s:
                    is_dell = True
                    break
    return is_dell

#ssd质保年限
try:
    SSD_LIFE_MAX =config.safe_get_int('model-config', 'ssdlife', 3) 
except ConfigParser.NoSectionError:
    logger.run.error("options ssdlife not find")
    SSD_LIFE_MAX="MAX"

def get_os_release():
    release =  platform.release()

    if os.path.exists('/etc/system-release'):
        with open("/etc/system-release") as f:
            for line in f.readlines():
                system_config =  line
    else:
        logger.run.error("not find /etc/system-release")
        return (None,None)

    #print system_config
    if system_config:
        logger.run.debug("system-release read = [%s]" % system_config)

    #print release
    if  release:
        logger.run.debug('release=[%s]' % release)

    if release > "3":
        logger.run.debug("system release is %s is well be redhat70,redhat72,oracle70,centos70,oracle72" % release)
        #CentOS Linux release 7.0.1406 (Core)
        #('CentOS', '7.0.1406')
        sysconf = re.search(r'^([Cc]ent[Oo][S,])+.*(7.0.1406)+.*',system_config)
        if sysconf:
            return ('centos70',sysconf.group(2))
        
        #Oracle Linux Server release 7.0
        #('Oracle', '7.0')
        sysconf = re.search(r'^([Oo]racle)+.*(7.0)$',system_config)
        if sysconf:
            return ('oracle70',sysconf.group(2))

        #('Oracle', '7.2')
        sysconf = re.search(r'^([Oo]racle)+.*(7.2)$',system_config)
        if sysconf:
            return ('oracle72',sysconf.group(2))

        sysconf = re.search(r'^(Red Hat)+.*(7.0)+.*',system_config)
        if sysconf:
            return ('redhat70',sysconf.group(2))
        sysconf = re.search(r'^(Red Hat)+.*(7.2)+.*',system_config)
        if sysconf:
            return ('redhat72',sysconf.group(2))

        #FIXME:需要添加其他版本判断        

    if release > "2" and release < "3":
        logger.run.debug("system release is %s is well be redhat65,redhat66,redhat67,redhat68,racle65,centos63" % release)
        #Oracle Linux Server release 6.5
        if re.search(r'^([O,o]racle)+.*(6.5)$' , system_config):
            return ("oracle65",'')
        #Oracle Linux Server release 6.6
        if re.search(r'^([O,o]racle)+.*(6.6)$' , system_config):
            return ("oracle66",'')
        #CentOS release 6.3 (Final)
        if re.search(r'^([C,c]ent[O,o][S,s])+.*(6.3)+.*',system_config):
            return ("centos63","")

        #Red Hat Enterprise Linux Server release 6.5 (Santiago)
        if re.search(r'^(Red Hat)+.*(6.5)+.*',system_config):
            return ("redhat65","")

        #Red Hat Enterprise Linux Server release 6.6 (Santiago)
        if re.search(r'^(Red Hat)+.*(6.6)+.*',system_config):
            return ("redhat66","")

        #Red Hat Enterprise Linux Server release 6.7 (Santiago)
        if re.search(r'^(Red Hat)+.*(6.7)+.*',system_config):
            return ("redhat67","")

        #Red Hat Enterprise Linux Server release 6.8 (Santiago)
        if re.search(r'^(Red Hat)+.*(6.8)+.*',system_config):
            return ("redhat68","")

        #FIXME:需要添加其他版本判断 
    
    #SmartStore release 3.1.0-013
    sysconf = re.search(r'^([Ss]mart[Ss]tor)+',system_config)
    if sysconf:
        os_info = system_config.strip().split()
        if len(os_info) < 3:
             return (-1, "Unsupport system")
        info = {}
        info['name']    = os_info[0].upper()
        info['version'] = os_info[2].upper()
        return (info['name'],info['version'])

    return (None,None)

 
def get_os_version():
    name, version = get_os_release()
    if not name: 
        return (-1,"get system release error")

    if name == "oracle70" or name == "oracle72" or name == "centos70" or name == "redhat70" or name == "redhat72":
        return (0,"systemv7")

    if name == "oracle65" or name == "oracle66" or name == "centos63" or name == "redhat65" or name == "redhat66" or name == "redhat67" or name == "redhat68":
        return (0,"systemv6")

    # smartstore 系统
    if name == "SMARTSTORE":
        if version.startswith("3"):
            return (0,"systemv7")
        elif version.startswith("2"):
            return (0,"systemv6")
        else:
            return (-1, "system release not support")
    return (-1, "system release not support")


