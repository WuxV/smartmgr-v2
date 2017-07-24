# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import re
from pdsframe import *
from service_mds import g
from base import asm
from base.asm import OraSQLPlus
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class RefreshASMDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 1

    def INIT(self):
        mds_storage_request = MakeRequest(msg_mds.HEARTBEAT_ASMDISK_LIST_REQUEST)

        if g.is_ready == False:
            logger.run.debug("HeartBeatASMDiskList MDS service is not ready")
            return MS_FINISH

        if g.platform['sys_mode'] == "storage":
            return MS_FINISH

        ret, dbs = asm.get_grid_env()
        if ret:
            logger.run.error("Parse oratab env failed: %s" %dbs)
            return self.refresh_empty_asmdisk()

        if dbs.has_key("grid_home"):
            self.grid_home = dbs["grid_home"]
        else:
            logger.run.error("Can not find Oracle grid home")
            return self.refresh_empty_asmdisk()

        self.ip          = g.listen_ip
        self.port        = config.safe_get('oracle', 'port')
        self.uid         = config.safe_get('oracle', 'user')
        self.passwd      = config.safe_get('oracle', 'password')
        self.servicename = config.safe_get('oracle', 'servicename')
        sql = OraSQLPlus(self.servicename, self.ip, self.port, self.uid, self.passwd)
        ret, disk_list = sql.list_asm_disks()
        if ret:
            logger.run.error("Get asm disklist failed: %s" % disk_list)
            return self.refresh_empty_asmdisk()

        # 获取asmdisk_name为空的asmdisk对应的dskname
        dsk = []
        for disk in disk_list:
            if disk["name"]:
                continue
            e, info = self.get_info_by_kfed(disk['path'])
            if e:
                logger.run.error("Command kfed failed: %s" % info)
                return MS_FINISH
            if info and info["kfbh_type"] == "KFBTYP_DISKHEAD":
                found = False
                for i, dsk_info in enumerate(dsk):
                    # 相同dskname的asmdisk则取crestmp_hi和crestmp_lo较大的
                    if info["dskname"] == dsk_info["dskname"]:
                        found = True
                        if int(info["crestmp_hi"]) > int(dsk_info["crestmp_hi"]) and int(info["crestmp_lo"] > int(dsk_info["crestmp_lo"])):
                            del dsk[i]
                            dsk_info = {}
                            dsk_info["path"] = disk["path"]
                            dsk_info["dskname"] = info["dskname"]
                            dsk_info["crestmp_hi"] = info["crestmp_hi"]
                            dsk_info["crestmp_lo"] = info["crestmp_lo"]
                            dsk.append(dsk_info)
                if not found:
                    dsk_info = {}
                    dsk_info["path"] = disk["path"]
                    dsk_info["dskname"] = info["dskname"]
                    dsk_info["crestmp_hi"] = info["crestmp_hi"]
                    dsk_info["crestmp_lo"] = info["crestmp_lo"]
                    dsk.append(dsk_info)
        for disk in disk_list:
            for dsk_info in dsk:
                if disk["path"] == dsk_info["path"]:
                    disk["dskname"] = dsk_info["dskname"]

        # 更新asmdisk列表
        g.asmdisk_list.Clear()
        for disk in disk_list:
            asmdisk_info = msg_pds.ASMDiskInfo()
            asmdisk_info.asmdisk_name = disk["name"] or ""
            asmdisk_info.asmdisk_id   = str(disk["disk_number"])
            asmdisk_info.diskgroup_id = str(disk["group_number"])
            asmdisk_info.state        = disk["state"]
            asmdisk_info.mode_status  = disk["mode_status"]
            asmdisk_info.path         = disk["path"] or ""
            asmdisk_info.failgroup    = disk["failgroup"] or ""
            asmdisk_info.total_mb     = int(disk["total_mb"])
            asmdisk_info.free_mb      = int(disk["free_mb"])

            if disk.has_key("dskname"):
                asmdisk_info.dskname = disk["dskname"]

            g.asmdisk_list.asmdisk_infos.add().CopyFrom(asmdisk_info)
            mds_storage_request.body.Extensions[msg_mds.heartbeat_asmdisk_list_request].asmdisk_infos.add().CopyFrom(asmdisk_info)

        mds_storage_request.body.Extensions[msg_mds.heartbeat_asmdisk_list_request].node_name = g.node_info.node_name
        # 向集群内的所有存储节点发送
        for node_info in g.nsnode_list.nsnode_infos:
            if node_info.sys_mode != "database":
                self.SendRequest(node_info.listen_ip, node_info.listen_port, mds_storage_request, self.Entry_HeartbeatASMDiskList)

        ret, diskgroup_list = sql.list_asm_group()
        if ret:
            logger.run.error("Get asm diskgroup failed: %s" % diskgroup_list)
            return MS_FINISH
        # 更新磁盘组列表 
        g.diskgroup_list.Clear()
        for dg in diskgroup_list:
            diskgroup_info = msg_pds.DiskgroupInfo()
            diskgroup_info.diskgroup_name = dg["name"]  
            diskgroup_info.diskgroup_id   = str(dg["group_number"])
            diskgroup_info.type           = dg["type"] or ""
            diskgroup_info.state          = dg["state"]
            diskgroup_info.offline_disks  = int(dg["offline_disks"])
            diskgroup_info.total_mb       = int(dg["total_mb"])
            diskgroup_info.free_mb        = int(dg["free_mb"])
            diskgroup_info.usable_file_mb = int(dg["usable_file_mb"])
            g.diskgroup_list.diskgroup_infos.add().CopyFrom(diskgroup_info)

        return MS_CONTINUE

    # 集群关闭或者获取不到asm实例或者获取asm失败，需向存储节点通信，发送空的asm，以便更新状态
    def refresh_empty_asmdisk(self):
        mds_storage_request = MakeRequest(msg_mds.HEARTBEAT_ASMDISK_LIST_REQUEST)
        mds_storage_request.body.Extensions[msg_mds.heartbeat_asmdisk_list_request].node_name = g.node_info.node_name
        # 向集群内的所有存储节点发送
        for node_info in g.nsnode_list.nsnode_infos:
            if node_info.sys_mode != "database":
                self.SendRequest(node_info.listen_ip, node_info.listen_port, mds_storage_request, self.Entry_HeartbeatASMDiskList)

        return MS_CONTINUE

    def get_info_by_kfed(self, asmdisk_path):
        e, out = command("%s read %s" % (os.path.join(self.grid_home, 'bin/kfed'),asmdisk_path))
        if e == -2:
            return e, out
        asmdisk_info = {}
        txt = out.splitlines()
        pattern = r'(.*):\s+([0-9a-zA-Z\_]*)\s;\s\w+:\s([0-9a-zA-Z\_]+)'
        for k in range(len(txt)):
            result = re.search(pattern, txt[k])
            if result: 
                if result.group(1) == "kfbh.type":
                    asmdisk_info["kfbh_type"] = result.group(3)
                if result.group(1) == "kfdhdb.dskname":
                    asmdisk_info["dskname"] = result.group(2)
                if result.group(1) == "kfdhdb.crestmp.hi":
                    asmdisk_info["crestmp_hi"] = result.group(2)
                if result.group(1) == "kfdhdb.crestmp.lo":
                    asmdisk_info["crestmp_lo"] = result.group(2)
        return (0, asmdisk_info)

    def Entry_HeartbeatASMDiskList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error(response.rc.message)
        return MS_FINISH
