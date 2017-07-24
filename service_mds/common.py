# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import netifaces, struct, re, base64, fcntl, struct
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

SRBDDISK = "/dev/srbd1"
PCS = "/usr/sbin/pcs"

# 根据node_index获取uuid
def GetUUIDFromIndex(node_index):
    for node in g.nsnode_conf_list.nsnode_infos:
        if node.node_info.node_index == node_index:
            return (0,node.node_uuid)
    return (1,None)

# 根据uuid获取node_index
def GetIndexFromUUID(node_uuid):
    for node in g.nsnode_conf_list.nsnode_infos:
        if node.node_info.node_uuid == node_uuid:
            return (0,node.node_info.node_index)
    return (1,None)


# 根据group name 获取group info
def GetGroupInfoFromName(group_name):
    for group_info in g.group_list.groups:
        if group_name == group_info.group_name:
            return (0,group_info)
    return (1,None)

#判断本机是否安装smartmon-server rpm的依据
SMARTMON_SERVER = "smartmon-server-mysql"

# 获取指定网卡的ip地址
def get_ip_address(ifname):
    try:
        return netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']
    except:
        return None

# 获取license信息
def load_license():
    e, lic_info = License().licmgr_info()
    if e == -1:
        logger.run.error("*** License can not use, please use \"#smartmgrcli license info\" to check license ***")
        sys.exit(-1)
    return lic_info

# 获取平台信息
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

# ========================================
# 创建disk/pool/lun/palcache/palraw/palpmt资源名称
# ========================================

def NewDiskName(disk_type):
    ids = []
    if disk_type == msg_pds.DISK_TYPE_SSD:
        prefix = "sd"
    else:
        prefix = "hd"

    for disk in [disk_info for disk_info in g.disk_list.disk_infos if disk_info.disk_type == disk_type]:
        disk_name = disk.disk_name
        ids.append(int(disk_name.split(prefix)[1]))
    ids.sort()
    for i in range(len(ids)):
        if i == ids[i]-1:
            continue
        return "%s%s" % (prefix, str(i+1).rjust(2, '0'))
    return "%s%s" % (prefix, str(len(ids)+1).rjust(2, '0'))

def NewNodeName():
    ids = []
    prefix = "node"
    for node in g.nsnode_conf_list.nsnode_infos:
        if node.node_info.HasField("node_index"):
            ids.append(int(node.node_info.node_index.split(prefix)[1]))
    ids.sort()
    for i in range(len(ids)):
        if i == ids[i]-1:
            continue
        return "%s%s" % (prefix, str(i+1).rjust(2, '0'))
    return "%s%s" % (prefix, str(len(ids)+1).rjust(2, '0'))

def NewLunName():
    ids = []
    prefix = "lun"
    for lun in g.lun_list.lun_infos:
        if lun.lun_name.startswith("lvvote"):
            continue
        lun_name = lun.lun_name
        ids.append(int(lun_name.split(prefix)[1]))
    ids.sort()
    for i in range(len(ids)):
        if i == ids[i]-1:
            continue
        return "%s%s" % (prefix, str(i+1).rjust(2, '0'))
    return "%s%s" % (prefix, str(len(ids)+1).rjust(2, '0'))

def NewPoolName():
    ids = []
    prefix = "pool"
    for pool in g.pool_list.pool_infos:
        pool_name = pool.pool_name
        ids.append(int(pool_name.split(prefix)[1]))
    ids.sort()
    for i in range(len(ids)):
        if i == ids[i]-1:
            continue
        return "%s%s" % (prefix, str(i+1).rjust(2, '0'))
    return "%s%s" % (prefix, str(len(ids)+1).rjust(2, '0'))

def NewTargetName():
    ids = []
    prefix = "target"
    for palcache in g.palcache_list.palcache_infos:
        palcache_name = palcache.palcache_name
        ids.append(int(palcache_name.split(prefix)[1]))
    for palraw in g.palraw_list.palraw_infos:
        palraw_name = palraw.palraw_name
        ids.append(int(palraw_name.split(prefix)[1]))
    for palpmt in g.palpmt_list.palpmt_infos:
        palpmt_name = palpmt.palpmt_name
        ids.append(int(palpmt_name.split(prefix)[1]))
    ids.sort()
    for i in range(len(ids)):
        if i == ids[i]-1:
            continue
        return "%s%s" % (prefix, str(i+1).rjust(2, '0'))
    return "%s%s" % (prefix, str(len(ids)+1).rjust(2, '0'))

# ========================================
# 索引
# ========================================

def GetBaseDevInfoById(basedev_id):
    for basedev_info in g.basedev_list.basedev_infos:
        if basedev_info.basedev_id == basedev_id:
            return basedev_info
    return None

def GetBaseDiskInfoById(basedisk_id):
    for basedisk_info in g.basedisk_list.basedisk_infos:
        if basedisk_info.basedisk_id == basedisk_id:
            return basedisk_info
    return None

def GetSmartCacheInfoById(smartcache_id):
    for smartcache_info in g.smartcache_list.smartcache_infos:
        if smartcache_info.smartcache_id == smartcache_id:
            return smartcache_info
    return None

def GetPalCacheInfoById(palcache_id):
    for palcache_info in g.palcache_list.palcache_infos:
        if palcache_info.palcache_id == palcache_id:
            return palcache_info
    return None

def GetPalRawInfoById(palraw_id):
    for palraw_info in g.palraw_list.palraw_infos:
        if palraw_info.palraw_id == palraw_id:
            return palraw_info
    return None

def GetPalPmtInfoById(palpmt_id):
    for palpmt_info in g.palpmt_list.palpmt_infos:
        if palpmt_info.palpmt_id == palpmt_id:
            return palpmt_info
    return None

def GetPoolInfoByName(pool_name):
    for pool_info in g.pool_list.pool_infos:
        if pool_info.pool_name == pool_name:
            return pool_info
    return None

def GetPoolInfoById(pool_id):
    for pool_info in g.pool_list.pool_infos:
        if pool_info.pool_id == pool_id:
            return pool_info
    return None

def GetDiskInfoByName(disk_name):
    for disk_info in g.disk_list.disk_infos:
        if disk_info.disk_name == disk_name:
            return disk_info
    return None

def GetDiskInfoByID(uuid):
    for disk_info in g.disk_list.disk_infos:
        if disk_info.header.uuid == uuid:
            return disk_info
    return None

def GetDiskPartByID(disk_id, disk_part):
    for disk_info in g.disk_list.disk_infos:
        if disk_info.header.uuid == disk_id:
            for diskpart in disk_info.diskparts:
                if diskpart.disk_part == disk_part:
                    return diskpart
    return None

def GetLunInfoByName(lun_name):
    for lun_info in g.lun_list.lun_infos:
        if lun_info.lun_name == lun_name:
            return lun_info
    return None

def GetLunInfoByID(lun_id):
    for lun_info in g.lun_list.lun_infos:
        if lun_info.lun_id == lun_id:
            return lun_id
    return None

def GetQosTemplateInfoByName(template_name):
    for qos_template_info in g.qos_template_list.qos_template_infos:
        if qos_template_info.template_name == template_name:
            return qos_template_info
    return None

def GetQosTemplateInfoById(template_id):
    for qos_template_info in g.qos_template_list.qos_template_infos:
        if qos_template_info.template_id == template_id:
            return qos_template_info
    return None

def GetLunNameListByTemplateId(template_id):
    lun_names = []
    for lun_info in g.lun_list.lun_infos:
        if lun_info.qos_template_id == template_id:
            lun_names.append(lun_info.lun_name)
    return lun_names

# ========================================
# 获取磁盘或磁盘分区和lun/pool的引用关系
# ========================================

# 获取被指定磁盘分区引用的lun
def GetLunInfoByDiskPart(disk_id, disk_part):
    for lun_info in g.lun_list.lun_infos:
        if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            basedisk_info = GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
            if  disk_id == basedisk_info.disk_id and basedisk_info.disk_part == disk_part:
                return lun_info
        elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            smartcache_info = GetSmartCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
            if smartcache_info.data_disk_id == disk_id and smartcache_info.data_disk_part == disk_part:
                return lun_info
            if smartcache_info.cache_disk_id == disk_id and smartcache_info.cache_disk_part == disk_part:
                return lun_info
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_info = GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
            if palcache_info.disk_id == disk_id and palcache_info.disk_part == disk_part:
                return lun_info
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            palraw_info = GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
            if palraw_info.disk_id == disk_id and palraw_info.disk_part == disk_part:
                return lun_info
        elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            pass
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            pass
        else:
            assert(0)
    return None
        
# 获取被指定磁盘引用的lun列表
def GetLunInfoByDiskID(disk_id):
    lun_infos = []
    for lun_info in g.lun_list.lun_infos:
        if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
            basedisk_info = GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
            if  basedisk_info.disk_id == disk_id:
                lun_infos.append(lun_info)
        elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
            smartcache_info = GetSmartCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id])
            if smartcache_info.data_disk_id == disk_id:
                lun_infos.append(lun_info)
            if smartcache_info.cache_disk_id == disk_id:
                lun_infos.append(lun_info)
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_info = GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
            if palcache_info.disk_id == disk_id:
                lun_infos.append(lun_info)
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
            palraw_info = GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
            if palraw_info.disk_id == disk_id:
                lun_infos.append(lun_info)
        elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
            pass
        elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            pass
        else:
            assert(0)
    return lun_infos

# 获取被指定磁盘分区引用的pool
def GetPoolInfoByDiskPart(disk_id, disk_part):
    for pool_info in g.pool_list.pool_infos:
        for pool_disk_info in pool_info.pool_disk_infos:
            if pool_disk_info.disk_id == disk_id and pool_disk_info.disk_part == disk_part:
                return pool_info
    return None

# 获取被指定磁盘引用的Pool列表
def GetPoolInfoByDiskID(disk_id):
    pool_infos = []
    for pool_info in g.pool_list.pool_infos:
        for pool_disk_info in pool_info.pool_disk_infos:
            if pool_disk_info.disk_id == disk_id:
                pool_infos.append(pool_info)
    return pool_infos

# 获取被指定pool引用的lun列表
def GetLunInfoByPoolID(pool_id):
    lun_infos = []
    for lun_info in g.lun_list.lun_infos:
        if lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
            palcache_info = GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
            if palcache_info.pool_id == pool_id:
                lun_infos.append(lun_info)
        if lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
            palpmt_info = GetPalPmtInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])
            if palpmt_info.pool_id == pool_id:
                lun_infos.append(lun_info)
    return lun_infos

# 存储节点:根据lun名称获取对应计算节点的asm磁盘信息
def GetASMDiskInfoByLunName(lun_name):
    d = []
    for asmdisk_list in g.all_asmdisk_list.values():
        d.extend([asmdisk_info for asmdisk_info in asmdisk_list.asmdisk_infos if asmdisk_info.path.endswith(lun_name)])

    # 不同计算节点获取到的asmdisk_info不同时的取舍
    active_asmdisk_list = [asmdisk_info for asmdisk_info in d if asmdisk_info.asmdisk_name]
    inactive_asmdisk_list = [asmdisk_info for asmdisk_info in d if not asmdisk_info.asmdisk_name and asmdisk_info.dskname]
    if active_asmdisk_list:
        return active_asmdisk_list[0]
    elif inactive_asmdisk_list:
        return inactive_asmdisk_list[0]
    elif d:
        return d[0]

    return None

def GetASMDiskInfoByPath(path):
    for asmdisk_info in g.asmdisk_list.asmdisk_infos:
        if asmdisk_info.path == path:
            return asmdisk_info
    return None

def GetASMDiskInfoByName(asmdisk_name):
    for asmdisk_info in g.asmdisk_list.asmdisk_infos:
        if asmdisk_info.asmdisk_name == asmdisk_name.upper():
            return asmdisk_info
    return None

def GetDiskgroupInfoByID(diskgroup_id):
    for diskgroup_info in g.diskgroup_list.diskgroup_infos:
        if diskgroup_info.diskgroup_id == diskgroup_id:
            return diskgroup_info
    return None

def GetDiskgroupInfoByName(diskgroup_name):
    for diskgroup_info in g.diskgroup_list.diskgroup_infos:
        if diskgroup_info.diskgroup_name == diskgroup_name.upper():
            return diskgroup_info
    return None

# 获取IB卡 port guid
class IBNode:
    IB_SYS_ROOT = "/sys/class/infiniband"
    SYS_HOST_ROOT = "/sys/class/scsi_host"
    def __init__(self):
        pass

    def __fetch_host_attrs(self, shost_dir):
        host_attr = {}
        for file in os.listdir(shost_dir):
            path = os.path.join(shost_dir, file)
            if file == "dgid":
                f = open(path, 'r')
                if f:
                    try:
                        value = f.readline().strip()
                        if len(value) == 39:
                            host_attr["rport"] = value[20:]
                        else:
                            logger.run.error("Invalid dgid: %s!" %value)
                        f.close()
                    except:
                        f.close()
            if file == "local_ib_device":
                f = open(path, 'r')
                if f:
                    try:
                        value = f.readline().strip()
                        host_attr["local_ib"] = value
                        f.close()
                    except:
                        f.close()
            if file == "local_ib_port":
                f = open(path, 'r')
                if f:
                    try:
                        value = f.readline().strip()
                        host_attr["local_ib_port"] = value
                        f.close()
                    except:
                        f.close()
        return host_attr

    def __fetch_host_devices(self, devs_dir):
         devices = []
         reg = ur"^(\d+):(\d+):(\d+):(\d+)$"
         for file in os.listdir(devs_dir):
             if re.search(reg, file):
                 devices.append(file)
         return devices

    def __fetch_hosts(self, device_dir):
        hosts = {}
        for sub in os.listdir(device_dir):
            host_dir = os.path.join(device_dir, sub)
            if sub.startswith("host") and os.path.isdir(host_dir):
                host_attrs = {}
                shost_dir = os.path.join(IBNode.SYS_HOST_ROOT, sub)
                if not os.path.exists(shost_dir):
                    logger.run.error("Path %s not exist!" %shost_dir)
                    continue
                host_attrs = self.__fetch_host_attrs(shost_dir)
                host_attrs["devices"] = {}
                for subsub in os.listdir(host_dir):
                    if subsub.startswith("target"):
                        host_attrs["devices"] = self.__fetch_host_devices(os.path.join(host_dir,subsub))
                hosts[sub] = host_attrs
        return hosts
                 
    def fetch_list_ibnodes(self, with_devs = 0):
        if not os.path.exists(IBNode.IB_SYS_ROOT):
            return (-1, "No Kernel IB module loaded")
        entries = os.listdir(IBNode.IB_SYS_ROOT)
        ibs = {}
        for entry in entries:
            ibnode_path = os.path.join(IBNode.IB_SYS_ROOT, entry)
            if not os.path.isdir(ibnode_path):
                continue
            ib_attrs = {}
            ib_attrs["name"] = entry
            device_dir = os.path.join(ibnode_path, "device")

            for attr in os.listdir(ibnode_path):
                filters = ["uevent", "cmd_n", "cmd_avg", "cmd_perf", "vsd"]
                #attes: board_id, fw_ver, hw_rev, node_desc, node_guid, node_type, sys_image_guid
                attr_file = os.path.join(ibnode_path, attr)
                if  os.path.isfile(attr_file) and attr not in filters:
                    f = open(attr_file, 'r')
                    if f:
                        try:
                            id_str = f.readline().strip()
                            ib_attrs[attr] = id_str
                            f.close()
                        except:
                            f.close()
                else:
                    if attr == "ports":
                        ports_dir = os.path.join(ibnode_path, attr)
                        ib_attrs["ports"] = {}
                        for port in os.listdir(ports_dir):
                            port_dir = os.path.join(ports_dir, port)
                            filters = ["sm_sl", "lid_mask_count", "cap_mask"]
                            port_attrs = {}
                            port_attrs["num"] = port
                            for attr in os.listdir(port_dir):
                                port_attr_file = os.path.join(port_dir, attr)
                                if  os.path.isfile(port_attr_file) and attr not in filters:
                                    f = open(port_attr_file, 'r')
                                    if f:
                                        try:
                                            value = f.readline().strip()
                                            port_attrs[attr] = value
                                            f.close()
                                        except:
                                            f.close()
                            gid_file = os.path.join(port_dir, "gids/0")
                            if os.path.exists(gid_file):
                                f = open(gid_file, 'r')
                                if f:
                                    try:
                                        value = f.readline().strip()
                                        port_attrs["def_gid"] = value
                                        key = value[20:]
                                        ib_attrs["ports"][key] = port_attrs
                                        f.close()
                                    except:
                                        f.close()

            if with_devs and os.path.exists(device_dir):
                hosts = self.__fetch_hosts(device_dir)
                for port in ib_attrs["ports"].keys():
                    if not ib_attrs["ports"][port].has_key("hosts"):
                        ib_attrs["ports"][port]["hosts"] = {}
                    for host in hosts.keys():
                        if ib_attrs["ports"][port]["num"] == hosts[host]["local_ib_port"]:
                            ib_attrs["ports"][port]["hosts"][host] = hosts[host]

            if ib_attrs.has_key("node_guid"):
                key = ib_attrs["node_guid"]
                del(ib_attrs["node_guid"])
                ibs[key] = ib_attrs
            else:
                return (-1, "No node_guid attr found")
        return (0, ibs)

def list_ports():
    ibhdl = IBNode()
    e,ibs = ibhdl.fetch_list_ibnodes()
    if e:
        return None
    ids = []
    for ib in ibs.keys():
        for port in ibs[ib]["ports"].keys():
            ids.append(port.replace(":",""))
    return ids

#判断是否是smartmon
def is_smartmon():
    cmd_str = "rpm -q %s" % SMARTMON_SERVER
    e, out = command(cmd_str)
    if e:
        return False
    else:
        return True

# umount srbd1
def _umount():
    cmd_str = "umount %s" % SRBDDISK
    e,out = command(cmd_str)
    if e:
        if re.search(r'umount(.*)not (found|mounted)',out):
            pass
        else:
            return e,out
    return 0,"umount srbd1 success"

def stonith_info():
    stonith_infos = []
    cmd_str = "%s stonith" % PCS
    e,out = command(cmd_str)
    if e:
        if re.search(r'(.*)cluster is not currently running(.*)',out):
            return 1,"cluster not running"
        else:
            return e,out
    for line in out.splitlines():
        stonith_info = {}
        st = line.split()
        stonith_info['stonith_name'] = st[0]
        stonith_info['stonith_status'] = st[-1]
        stonith_infos.append(stonith_info)
    return 0, stonith_infos

    # 配置srbd conf的信息
def write_config(config, filename):
    try:
        with open(filename, "w") as f:
            config.write(f)
            f.close()
        return 0, "config set success"
    except :
        return 1,"set config failed:%s" % str(e)

    # srbd 通过ssh协议，获取对方的hostname
def config_nodename(srbd_ip):
    cmd_str = "ssh %s hostname" % srbd_ip
    e,out = command(cmd_str)
    if e:
         return e,out
    try:
        config.safe_set('node2', 'node2_hostname', out) 
    except e:
        return 1, "confing node2 hostname failed"
    e, res = write_config(config, g.srbd_conf) 
    if e:
        return e, res
    return 0, "success"

