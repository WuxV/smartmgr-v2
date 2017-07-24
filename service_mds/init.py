# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, netifaces
from pdsframe import *
from pdsframe.common import dbclient
import message.pds_pb2 as msg_pds
from service_mds import g
from service_mds import common
from service_mds import pb2dict_proxy

def INIT():
    check_netconfig()

    g.license  = common.load_license()
    g.platform = common.load_platform()
    g.ibguids = common.list_ports()
    g.is_smartmon = common.is_smartmon()

    load_nodeinfo()
    load_disk()
    load_basedisk()
    load_basedev()
    load_smartcache()
    load_palcache()
    load_palraw()
    load_palpmt()
    load_pool()
    load_lun()
    load_node_list()
    load_group_list()
    load_qos_template_list()
    load_second_backup_ip()
    g.is_ready = False

    if License().support_license_time() == 0:
        g.is_ready = True
    else:
        logger.run.error("*** License can not use, please use \"#smartmgrcli license info\" to check license ***")

def check_netconfig():
    listen_ip = config.safe_get('network', 'listen-ip')

    ips = [] 
    for i in netifaces.interfaces(): 
        info = netifaces.ifaddresses(i) 
        if netifaces.AF_INET not in info: 
            continue 
        ips.append(info[netifaces.AF_INET][0]['addr']) 
    if listen_ip not in ips:
        logger.run.error("listen-ip '%s' not available, check config : service.mds.ini" % listen_ip)
        sys.exit(1)

def load_nodeinfo():
    e, node_info = dbservice.srv.get("/node_info")
    if e and e != dbclient.RC_ERR_NODE_NOT_EXIST:
        logger.run.error("Load node info faild : %s" % e)
        sys.exit(-1)
    if node_info != None:
        node_info.update({"node_uuid":g.node_uuid})
        g.node_info.CopyFrom(pb2dict_proxy.dict2pb("node_info", node_info))
    else:
        # XXX:正常流程不会出现获取不到node-name的过程
        g.node_info.node_name = "su000"
        g.node_info.node_uuid = "su000"
    logger.run.info("Load node name: %s" % g.node_info.node_name)

def load_node_list():
    e, node_list = dbservice.srv.get("/node_list")
    if e and e != dbclient.RC_ERR_NODE_NOT_EXIST:
        logger.run.error("Load node info faild : %s" % e)
        sys.exit(-1)
    if node_list != None:
        g.nsnode_conf_list.Clear()
        for k in node_list.keys():
            lst = g.nsnode_conf_list.nsnode_infos.add()
            lst.node_uuid = k
            node = lst.node_info
            node.CopyFrom(pb2dict_proxy.dict2pb("nsnode_info", node_list[k]))
    else:
        g.nsnode_conf_list.Clear()
    logger.run.info("Load node list count : %d" % len(g.nsnode_conf_list.nsnode_infos))
 
def load_group_list():
    e, group_list = dbservice.srv.get("/group_list")
    if e and e != dbclient.RC_ERR_NODE_NOT_EXIST:
        logger.run.error("Load group info faild : %s" % e)
        sys.exit(-1)
    if group_list != None:
        g.group_list.Clear()
        for k in group_list.keys():
            lst = g.group_list.groups.add()
            lst.CopyFrom(pb2dict_proxy.dict2pb("group_info", group_list[k]))
    else:
        g.group_list.Clear()
    logger.run.info("Load group list count : %d" % len(g.group_list.groups))
   
def load_disk():
    e, disk_list = dbservice.srv.list("/disk/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load disk faild : %s" % e)
        sys.exit(-1)
    if disk_list != None:
        for _disk_info in disk_list.values():
            disk_info = g.disk_list.disk_infos.add()
            disk_info.CopyFrom(pb2dict_proxy.dict2pb("disk_info", _disk_info))
    logger.run.info("Load disk count : %s" % len(g.disk_list.disk_infos))

def load_lun():
    e, lun_list = dbservice.srv.list("/lun/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load lun faild : %s" % e)
        sys.exit(-1)
    if lun_list != None:
        for _lun_info in lun_list.values():
            lun_info = g.lun_list.lun_infos.add()
            lun_info.CopyFrom(pb2dict_proxy.dict2pb("lun_info", _lun_info))
    logger.run.info("Load lun count : %s" % len(g.lun_list.lun_infos))

def load_basedisk():
    e, basedisk_list = dbservice.srv.list("/basedisk/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load basedisk faild : %s" % e)
        sys.exit(-1)
    if basedisk_list != None:
        for _basedisk_info in basedisk_list.values():
            basedisk_info = g.basedisk_list.basedisk_infos.add()
            basedisk_info.CopyFrom(pb2dict_proxy.dict2pb("basedisk_info", _basedisk_info))
    logger.run.info("Load basedisk count : %s" % len(g.basedisk_list.basedisk_infos))

def load_basedev():
    e, basedev_list = dbservice.srv.list("/basedev/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load basedev faild : %s" % e)
        sys.exit(-1)
    if basedev_list != None:
        for _basedev_info in basedev_list.values():
            basedev_info = g.basedev_list.basedev_infos.add()
            basedev_info.CopyFrom(pb2dict_proxy.dict2pb("basedev_info", _basedev_info))
    logger.run.info("Load basedev count : %s" % len(g.basedev_list.basedev_infos))

def load_smartcache():
    e, smartcache_list = dbservice.srv.list("/smartcache/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load smartcache faild : %s" % e)
        sys.exit(-1)
    if smartcache_list != None:
        for _smartcache_info in smartcache_list.values():
            smartcache_info = g.smartcache_list.smartcache_infos.add()
            smartcache_info.CopyFrom(pb2dict_proxy.dict2pb("smartcache_info", _smartcache_info))
    logger.run.info("Load smartcache count : %s" % len(g.smartcache_list.smartcache_infos))

def load_pool():
    e, pool_list = dbservice.srv.list("/pool/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load pool faild : %s" % e)
        sys.exit(-1)
    if pool_list != None:
        for _pool_info in pool_list.values():
            pool_info = g.pool_list.pool_infos.add()
            pool_info.CopyFrom(pb2dict_proxy.dict2pb("pool_info", _pool_info))
    logger.run.info("Load pool count : %s" % len(g.pool_list.pool_infos))

def load_palcache():
    e, palcache_list = dbservice.srv.list("/palcache/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load palcache faild : %s" % e)
        sys.exit(-1)
    if palcache_list != None:
        for _palcache_info in palcache_list.values():
            palcache_info = g.palcache_list.palcache_infos.add()
            palcache_info.CopyFrom(pb2dict_proxy.dict2pb("palcache_info", _palcache_info))
    logger.run.info("Load palcache count : %s" % len(g.palcache_list.palcache_infos))

def load_palraw():
    e, palraw_list = dbservice.srv.list("/palraw/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load palraw faild : %s" % e)
        sys.exit(-1)
    if palraw_list != None:
        for _palraw_info in palraw_list.values():
            palraw_info = g.palraw_list.palraw_infos.add()
            palraw_info.CopyFrom(pb2dict_proxy.dict2pb("palraw_info", _palraw_info))
    logger.run.info("Load palraw count : %s" % len(g.palraw_list.palraw_infos))

def load_palpmt():
    e, palpmt_list = dbservice.srv.list("/palpmt/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load palpmt faild : %s" % e)
        sys.exit(-1)
    if palpmt_list != None:
        for _palpmt_info in palpmt_list.values():
            palpmt_info = g.palpmt_list.palpmt_infos.add()
            palpmt_info.CopyFrom(pb2dict_proxy.dict2pb("palpmt_info", _palpmt_info))
    logger.run.info("Load palpmt count : %s" % len(g.palpmt_list.palpmt_infos))

def load_qos_template_list():
    e, template_list = dbservice.srv.list("/qostemplate/")
    if e and e != dbclient.RC_ERR_PARENT_NOT_EXIST:
        logger.run.error("Load QoS template faild : %s" % e)
        sys.exit(-1)
    if template_list != None:
        for _template_info in template_list.values():
            template_info = g.qos_template_list.qos_template_infos.add()
            template_info.CopyFrom(pb2dict_proxy.dict2pb("template_info", _template_info))
    logger.run.info("Load QoS template count : %s" % len(g.qos_template_list.qos_template_infos))

def load_second_backup_ip():
    if not os.path.exists(g.second_storage_ip_file):
        g.second_storage_ip = None
    else:
        with open(g.second_storage_ip_file,'rb') as f:
            g.second_storage_ip = f.read()
        f.close()

INIT()
