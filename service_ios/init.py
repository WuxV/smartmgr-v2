# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import sys, netifaces
from pdsframe import *
from service_ios import g

def INIT():
    check_netconfig()

    g.platform = load_platform()
    check_modules()

    g.is_ready = True

def check_netconfig():
    listen_ip = config.safe_get('network', 'listen-ip')

    ips = [] 
    for i in netifaces.interfaces(): 
        info = netifaces.ifaddresses(i) 
        if netifaces.AF_INET not in info: 
            continue 
        ips.append(info[netifaces.AF_INET][0]['addr']) 
    if listen_ip not in ips:
        logger.run.error("listen-ip '%s' not available, check config : service.ios.ini" % listen_ip)
        sys.exit(1)

def load_platform():
    try:
        f = open("/boot/installer/platform", 'r')
        c = f.read()
        f.close()
    except:
        print "Load /boot/installer/platform failed!"
        sys.exit(1)
    kvs = {}
    for line in c.splitlines():
        item = line.split()
        kvs[item[0].lower()] = item[1].lower()
    return kvs

def check_modules():
    if g.platform['sys_mode'] == "database":
        return

    with open("/proc/modules", 'r') as pmodules:
        modules   = [module.split()[0] for module in pmodules.read().strip().splitlines()]
        miss_list = []
        for r_m in ["smartscsi", "ib_srpt", "smartscsi_vdisk"]:
            if r_m not in modules:
                miss_list.append(r_m)

        if len(miss_list) != 0:
            logger.run.error("Miss module : %s" % ",".join(miss_list))
            sys.exit(-1)
    return

INIT()
