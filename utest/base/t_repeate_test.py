# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time, json

sys.path.append(os.path.abspath(os.path.join(__file__, '../../')))

from pdsframe.common.config import init_config, config
init_config('../files/conf/test/service.mds.215.ini')

import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

if __name__ == "__main__":
    lun_info = msg_pds.LunInfo()
    lun_info.lun_name = "name"
    lun_export_info = msg_pds.LunExportInfo()
    lun_export_info.lun_name = "xx"
    lun_info.Extensions[msg_mds.ext_luninfo_lun_export_info].CopyFrom(lun_export_info)
    print dir(lun_info)
    print lun_info
    lun_info.ClearExtension(msg_mds.ext_luninfo_lun_export_info)
    print lun_info



    # print lun_info.HasExtension(msg_pds.ext_luninfo_basedisk_id)
    # print dir(lun_info)

    # disk_info = msg_pds.DiskInfo()
    # disk_info.dev_name = "/dev/x"
    # disk_info.raid_disk_info.raid_type = msg_pds.RAID_TYPE_MEGARAID
    # disk_info.raid_disk_info.ctl = 2
    # disk_info.raid_disk_info.eid = 3
    # disk_info.raid_disk_info.slot = 4
    # disk_info.raid_disk_info.drive_type = "x"
    # disk_info.raid_disk_info.protocol = "xx"
    # disk_info.raid_disk_info.pci_addr = "xxx"
    # disk_info.raid_disk_info.size = "xxxx"
    # disk_info.raid_disk_info.model = "xxxxx"
    # disk_info.raid_disk_info.state = "xxxxxx"
    # disk_info.Extensions[msg_mds.ext_diskinfo_node_disk_name] = "node"
    # disk_info.Extensions[msg_mds.ext_diskinfo_pool_name] = "p1"
    # disk_info.Extensions[msg_mds.ext_diskinfo_free_size] = 123

    # print dir(disk_info)
    # kv = disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_osdid].add()
    # kv.key   = "b"
    # kv.value = "c"
    # kv = disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_osdid].add()
    # kv.key   = "b2"
    # kv.value = "c2"
