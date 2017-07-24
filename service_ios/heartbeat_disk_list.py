# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_ios import g
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
from service_ios.base.apidisk import APIDisk
from service_ios.base.raid.megaraid import MegaRaid
from service_ios.base.raid.sas2raid import SAS2Raid
from service_ios.base.raid.hpsaraid import HPSARaid

class HeartBeatDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        self.mds_request       = MakeRequest(msg_mds.HEARTBEAT_DISK_LIST_REQUEST)

        if g.is_ready == False:
            logger.run.debug("HeartBeatDiskList IOS service is not ready")
            return MS_FINISH

        if g.platform['sys_mode'] == "database":
            return MS_FINISH

        # 获取磁盘列表比较耗时, 需要放到线程操作
        self.LongWork(self.get_disk_list, {}, self.Entry_GetDiskList)
        return MS_CONTINUE

    def get_disk_list(self, params={}):
        todo_check_disk = []
        rc = msg_pds.ResponseCode()

        # 获取megaraid磁盘列表
        e, disk_list = MegaRaid().get_disk_list()
        if e:
            rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            rc.message = "Get megaraid disk list failed : %s" % disk_list
            return rc, ''

        for disk in disk_list:
            raid_disk_info = msg_pds.RaidDiskInfo()
            raid_disk_info.raid_type  = msg_pds.RAID_TYPE_MEGARAID
            raid_disk_info.ctl        = str(disk['ctl'])
            raid_disk_info.eid        = disk['eid']
            raid_disk_info.slot       = disk['slot']
            raid_disk_info.drive_type = disk['drive_type']
            raid_disk_info.protocol   = disk['protocol']
            raid_disk_info.pci_addr   = disk['pci_addr']
            raid_disk_info.size       = disk['size']
            raid_disk_info.model      = disk['model']
            raid_disk_info.state      = disk['state']
            if disk.has_key('dev_name') and disk['dev_name'] != "":
                raid_disk_info.dev_name = disk['dev_name']
                _disk = {}
                _disk['did']            = disk['did']
                _disk['raid_type']      = "megaraid"
                _disk['dev_name']       = disk['dev_name']
                _disk['drive_type']     = disk['drive_type']
                todo_check_disk.append(_disk)
            _raid_disk_info = self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].raid_disk_infos.add()
            _raid_disk_info.CopyFrom(raid_disk_info)

        # 获取sas2raid磁盘列表
        e, disk_list = SAS2Raid().get_disk_list()
        if e:
            rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            rc.message = "Get sas2raid disk list failed : %s" % disk_list
            return rc, ''
        for disk in disk_list:
            raid_disk_info = msg_pds.RaidDiskInfo()
            raid_disk_info.raid_type  = msg_pds.RAID_TYPE_SAS2RAID
            raid_disk_info.ctl        = str(disk['ctl'])
            raid_disk_info.eid        = disk['eid']
            raid_disk_info.slot       = disk['slot']
            raid_disk_info.drive_type = disk['drive_type']
            raid_disk_info.protocol   = disk['protocol']
            raid_disk_info.pci_addr   = disk['pci_addr']
            raid_disk_info.size       = disk['size']
            raid_disk_info.model      = disk['model']
            raid_disk_info.state      = disk['state']
            if disk.has_key('dev_name') and disk['dev_name'] != "":
                raid_disk_info.dev_name = disk['dev_name']
                _disk = {}
                _disk['raid_type']      = "sas2raid"
                _disk['did']            = None
                _disk['dev_name']       = disk['dev_name']
                _disk['drive_type']     = disk['drive_type']
                todo_check_disk.append(_disk)
            _raid_disk_info = self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].raid_disk_infos.add()
            _raid_disk_info.CopyFrom(raid_disk_info)

        # 获取hpsaraid磁盘列表
        e, disk_list = HPSARaid().get_disk_list()
        if e:
            rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            rc.message = "Get hpsaraid disk list failed : %s" % disk_list
            return rc, ''
        Suffix=1
        for disk in disk_list:
            raid_disk_info = msg_pds.RaidDiskInfo()
            raid_disk_info.raid_type  = msg_pds.RAID_TYPE_HPSARAID
            raid_disk_info.ctl        = disk['ctl']
            raid_disk_info.eid        = disk['eid']
            raid_disk_info.slot       = disk['slot']
            raid_disk_info.drive_type = disk['drive_type']
            raid_disk_info.protocol   = disk['protocol']
            raid_disk_info.pci_addr   = disk['pci_addr']
            raid_disk_info.size       = disk['size']
            raid_disk_info.model      = disk['model']
            raid_disk_info.state      = disk['state']
            if disk.has_key('dev_name') and disk['dev_name'] != "":
                raid_disk_info.dev_name = disk['dev_name']
                # 判断是否逻辑盘符相同
                same_name = False
                for d in todo_check_disk:
                    if d['dev_name'] == disk['dev_name']:
                       same_name = True
                _disk = {}
                if same_name == True:
                    _disk['dev_name']   = "%s%s" % (disk['dev_name'],Suffix)
                    Suffix              = Suffix + 1
                else:
                    _disk['dev_name']   = disk['dev_name']
                _disk['raid_type']      = "cciss"
                _disk['did']            = disk['slot'] -1
                _disk['slot']           = disk['slot']
                _disk['drive_type']     = disk['drive_type']
                _disk['serial1']        = disk['Serial']
                todo_check_disk.append(_disk)
            _raid_disk_info = self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].raid_disk_infos.add()
            _raid_disk_info.CopyFrom(raid_disk_info)

        # 获取系统认到的磁盘列表
        e, disk_list  = APIDisk().get_disk_list()
        if e:
            rc.retcode = msg_ios.RC_IOS_GET_DISK_LIST
            rc.message = "Get disk list failed : %s" % disk_list
            return rc, ''
        for disk in disk_list:
            disk_info = self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].disk_infos.add()
            if disk.has_key('DEVNAME') and disk['DEVNAME'] != "":
                if disk.has_key('drive_type') and disk['drive_type'] == "nvme":
                    _disk = {}
                    _disk['dev_name']                  = disk['DEVNAME']
                    _disk['drive_type']                = disk['drive_type']
                    todo_check_disk.append(_disk)
                if disk.has_key('drive_type') and disk['drive_type'] == "df_pcie":
                    _disk = {}
                    _disk['dev_name']                  = disk['DEVNAME']
                    _disk['drive_type']                = disk['drive_type']
                    todo_check_disk.append(_disk)
                disk_info.dev_name  = disk['DEVNAME']
            disk_info.size      = disk['SIZE']
            if disk.has_key('HEADER'):
                disk_info.header.uuid = disk['HEADER']['uuid']
            for part in disk['PARTS']:
                diskpart = disk_info.diskparts.add()
                diskpart.disk_part  = int(part['INDEX'])
                diskpart.size       = part['SIZE']
                diskpart.dev_name   = part['DEVNAME']
        return rc, todo_check_disk

    def Entry_GetDiskList(self, result):
        rc, todo_check_disk = result
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Get disk list failed %s:%s" % (rc.retcode, rc.message))
            return MS_FINISH

        # 更新需要检查的磁盘列表
        g.todo_check_disk = todo_check_disk

        # 补充健康检查结果
        return self.HeartbeatDiskList()

    def match_disk(self):
        # hp磁盘检测的结果可能不匹配，匹配正确的磁盘检测结果
        for dev_name1,health_info1 in g.cache_disk_list_healthy.items():
            if health_info1['disk'].has_key('serial1') and health_info1['disk']['serial1'] == health_info1['disk']['serial2']:
                continue
            for dev_name2,health_info2 in g.cache_disk_list_healthy.items():
                if health_info2['disk'].has_key('serial1') and health_info1['disk']['serial1'] == health_info2['disk']['serial2']:
                    g.cache_disk_list_healthy[dev_name2]['disk']['serial1'],g.cache_disk_list_healthy[dev_name1]['disk']['serial1'] = \
                            g.cache_disk_list_healthy[dev_name1]['disk']['serial1'] ,g.cache_disk_list_healthy[dev_name2]['disk']['serial1']
                    g.cache_disk_list_healthy[dev_name2]['disk']['dev_name'],g.cache_disk_list_healthy[dev_name1]['disk']['dev_name'] = \
                            g.cache_disk_list_healthy[dev_name1]['disk']['dev_name'],g.cache_disk_list_healthy[dev_name2]['disk']['dev_name']
                    g.cache_disk_list_healthy[dev_name2]['disk']['drive_type'],g.cache_disk_list_healthy[dev_name1]['disk']['drive_type'] = \
                            g.cache_disk_list_healthy[dev_name1]['disk']['drive_type'],g.cache_disk_list_healthy[dev_name2]['disk']['drive_type']
                    g.cache_disk_list_healthy[dev_name2]['disk'],g.cache_disk_list_healthy[dev_name1]['disk'] = \
                            g.cache_disk_list_healthy[dev_name1]['disk'],g.cache_disk_list_healthy[dev_name2]['disk']
                    break
        for dev_name1,health_info1 in g.cache_disk_list_healthy.items():
            if health_info1['disk'].has_key('serial1') and health_info1['disk']['serial1'] != health_info1['disk']['serial2']:
                g.cache_disk_list_healthy[dev_name1]['disk'] = {}

    def HeartbeatDiskList(self):
        self.match_disk()
        for dev_name, health_info in g.cache_disk_list_healthy.items():
            if health_info['disk']:
                disk_info = health_info['disk']
                if disk_info['drive_type'].lower() == "ssd":
                    for raid_disk_info in self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].raid_disk_infos:
                        if raid_disk_info.dev_name == disk_info['dev_name']:
                            ssd_disk_health = msg_pds.SsdDiskHealthInfo()
                            ssd_disk_health.dev_name = disk_info['dev_name']
                            if disk_info.has_key('health'):
                                raid_disk_info.health = disk_info['health']
                            if disk_info.has_key('Life'):
                                ssd_disk_health.life = disk_info['Life']  
                            if disk_info.has_key('Offline_Uncorrectable'):
                                ssd_disk_health.offline_uncorrectable = disk_info['Offline_Uncorrectable']
                            if disk_info.has_key('Reallocated_Event_Count'):
                                ssd_disk_health.reallocated_event_count = disk_info['Reallocated_Event_Count']
                            if disk_info.has_key('Reallocated_Sector_Ct'):
                                ssd_disk_health.reallocated_sector_ct = disk_info['Reallocated_Sector_Ct']
                            if disk_info.has_key('Power_On_Hours'):
                                ssd_disk_health.power_on_hours = disk_info['Power_On_Hours'];
                            if disk_info.has_key('Temperature_Celsius'):
                                ssd_disk_health.temperature_celsius = disk_info['Temperature_Celsius']
                            if disk_info.has_key('Raw_Read_Error_Rate'):
                                ssd_disk_health.raw_read_error_rate = disk_info['Raw_Read_Error_Rate']
                            if disk_info.has_key('TotalLife'):
                                ssd_disk_health.totallife = disk_info['TotalLife'];
                            if disk_info.has_key('Media_Wearout_Indicator'):
                                ssd_disk_health.media_wearout_indicator = disk_info['Media_Wearout_Indicator']
                            if disk_info.has_key('Spin_Retry_Count'):
                                ssd_disk_health.spin_retry_count = disk_info['Spin_Retry_Count']
                            if disk_info.has_key('Command_Timeout'):
                                ssd_disk_health.command_timeout = disk_info['Command_Timeout']
                            if disk_info.has_key('Uncorrectable_Sector_Ct'):
                                ssd_disk_health.uncorrectable_sector_ct = disk_info['Uncorrectable_Sector_Ct']
                            if disk_info.has_key('SSD_Life_Left'):
                                ssd_disk_health.ssd_life_left = disk_info['SSD_Life_Left']
                            raid_disk_info.ssd_diskhealth_info.CopyFrom(ssd_disk_health)
                elif disk_info['drive_type'].lower() == "hdd":
                    for raid_disk_info in self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].raid_disk_infos:
                        if raid_disk_info.dev_name == disk_info['dev_name']:
                            hdd_disk_health = msg_pds.HddDiskHealthInfo()
                            if disk_info.has_key('health'):
                                raid_disk_info.health = disk_info['health']
                            if disk_info.has_key('Verifies_GB'):
                                hdd_disk_health.verifies_gb = disk_info['Verifies_GB']  
                            if disk_info.has_key('Life_Left'):
                                hdd_disk_health.life_left = disk_info['Life_Left']
                            if disk_info.has_key('Uncorrected_Reads'):
                                hdd_disk_health.uncorrected_reads = disk_info['Uncorrected_Reads']
                            if disk_info.has_key('Uncorrected_Verifies'):
                                hdd_disk_health.uncorrected_verifies = disk_info['Uncorrected_Verifies']
                            if disk_info.has_key('Corrected_Reads'):
                                hdd_disk_health.corrected_reads = disk_info['Corrected_Reads']
                            if disk_info.has_key('Writes_G'):
                                hdd_disk_health.writes_gb = disk_info['Writes_G']
                            if disk_info.has_key('Load_Cycle_Pct_Left'):
                                hdd_disk_health.load_cycle_pct_left = disk_info['Load_Cycle_Pct_Left']
                            if disk_info.has_key('Load_Cycle_Count'):
                                hdd_disk_health.load_cycle_count = disk_info['Load_Cycle_Count']
                            if disk_info.has_key('Corrected_Writes'):
                                hdd_disk_health.corrected_writes = disk_info['Corrected_Writes']
                            if disk_info.has_key('Non-Medium_Errors'):
                                hdd_disk_health.non_medium_errors = disk_info['Non-Medium_Errors']
                            if disk_info.has_key('Reads_GB'):
                                hdd_disk_health.reads_gb = disk_info['Reads_GB']
                            if disk_info.has_key('Load_Cycle_Spec'):
                                hdd_disk_health.load_cycle_spec = disk_info['Load_Cycle_Spec']
                            if disk_info.has_key('Start_Stop_Pct_Left'):
                                hdd_disk_health.start_stop_pct_left = disk_info['Start_Stop_Pct_Left']
                            if disk_info.has_key('Uncorrected_Writes'):
                                hdd_disk_health.uncorrected_writes = disk_info['Uncorrected_Writes']
                            if disk_info.has_key('Start_Stop_Spec'):
                                hdd_disk_health.start_stop_spec = disk_info['Start_Stop_Spec']
                            if disk_info.has_key('Corrected_Verifies'):
                                hdd_disk_health.corrected_verifies = disk_info['Corrected_Verifies']
                            if disk_info.has_key('Start_Stop_Cycles'):
                                hdd_disk_health.start_stop_cycles = disk_info['Start_Stop_Cycles']
                            raid_disk_info.hdd_diskhealth_info.CopyFrom(hdd_disk_health)
                elif disk_info['drive_type'] == "nvme" or disk_info['drive_type'] == "df_pcie":
                   for _disk_info in self.mds_request.body.Extensions[msg_mds.heartbeat_disk_list_request].disk_infos:
                       if _disk_info.dev_name == disk_info['dev_name']:
                           nvme_disk_health = msg_pds.NvmeDiskHealthInfo()
                           if disk_info.has_key('totallife'):
                               nvme_disk_health.totallife = int(disk_info['totallife'])
                           if disk_info.has_key('life'):
                               nvme_disk_health.life = int(disk_info['life'])  
                           if disk_info.has_key('health'):
                               nvme_disk_health.health = disk_info['health']
                           if disk_info.has_key('media_status'):
                               nvme_disk_health.media_status = disk_info['media_status']
                           _disk_info.nvme_diskhealth_info.CopyFrom(nvme_disk_health)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, self.mds_request, self.Entry_HeartBeatDiskList)
        return MS_CONTINUE

    def Entry_HeartBeatDiskList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("%d %s" % (response.rc.retcode, response.rc.message))
        return MS_FINISH
