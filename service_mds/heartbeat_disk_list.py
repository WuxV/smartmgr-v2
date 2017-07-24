# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class HeartBeatDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.HEARTBEAT_DISK_LIST_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.HEARTBEAT_DISK_LIST_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.heartbeat_disk_list_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        g.disk_list_all.Clear()
        g.raid_disk_list_all.Clear()

        # 将心跳上来的所有raid磁盘更新
        dev_to_raids = {}
        for rdisk in self.request_body.raid_disk_infos:
            rdisk.last_heartbeat_time = int(time.time())
            g.raid_disk_list_all.raid_disk_infos.add().CopyFrom(rdisk)
            if rdisk.HasField('dev_name') and rdisk.dev_name != "":
                dev_to_raids[rdisk.dev_name] = rdisk

        # 将心跳上来的所有磁盘更新
        uuid_to_disks = {}
        for disk in self.request_body.disk_infos:
            if disk.dev_name in dev_to_raids.keys():
                disk.raid_disk_info.CopyFrom(dev_to_raids[disk.dev_name])
            disk.last_heartbeat_time = int(time.time())
            g.disk_list_all.disk_infos.add().CopyFrom(disk)
            uuid_to_disks[disk.header.uuid] = disk

        # 更新磁盘状态
        for disk_info in g.disk_list.disk_infos:
            if disk_info.header.uuid in uuid_to_disks.keys():
                if disk_info.actual_state == False:
                    logger.run.info('[DISK STATE]: change disk %s   actual state to True' % disk_info.header.uuid)
                disk_info.dev_name            = uuid_to_disks[disk_info.header.uuid].dev_name
                disk_info.actual_state        = True
                disk_info.last_heartbeat_time = int(time.time())
                if uuid_to_disks[disk_info.header.uuid].HasField('raid_disk_info'):
                    disk_info.raid_disk_info.CopyFrom(uuid_to_disks[disk_info.header.uuid].raid_disk_info)
                if uuid_to_disks[disk_info.header.uuid].HasField('nvme_diskhealth_info'):
                    disk_info.nvme_diskhealth_info.CopyFrom(uuid_to_disks[disk_info.header.uuid].nvme_diskhealth_info)
                # 更新磁盘分区状态
                for diskpart in disk_info.diskparts:
                    if diskpart.disk_part in [_diskpart.disk_part for _diskpart in uuid_to_disks[disk_info.header.uuid].diskparts]:
                        for _diskpart in uuid_to_disks[disk_info.header.uuid].diskparts:
                            if _diskpart.disk_part == diskpart.disk_part:
                                diskpart.dev_name = _diskpart.dev_name
                        if diskpart.actual_state == False:
                            logger.run.info('[PART STATE]: change part %s:%s actual state to True' % (disk_info.header.uuid, diskpart.disk_part))
                        diskpart.actual_state        = True
                        diskpart.last_heartbeat_time = int(time.time())
        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
