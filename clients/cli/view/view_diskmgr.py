# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from view.baseview import *
import time
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds

class ViewDiskMgr(BaseView):
    def __init__(self, srv):
        self.detail   = srv['cli_config']['detail']
        self.platform = srv['platform']

    # Disk list
    def cli_list(self, request, response):
        out  = []
        # 补充系统能认到的盘
        for disk_info in response.body.Extensions[msg_mds.get_disk_list_response].disk_infos:
            info = {}
            info["dev_name"]        = disk_info.dev_name
            info["uuid"]            = disk_info.header.uuid
            info["size"]            = disk_info.size
            info["free_size"]       = disk_info.Extensions[msg_mds.ext_diskinfo_free_size]

            if disk_info.HasField('raid_disk_info'):
                info['slot']       = "%s:%s:%s" % (disk_info.raid_disk_info.ctl, disk_info.raid_disk_info.eid, disk_info.raid_disk_info.slot)
                info['drive_type'] = disk_info.raid_disk_info.drive_type.upper()
                info['model']      = disk_info.raid_disk_info.model
                info['protocol']   = disk_info.raid_disk_info.protocol
                info['state']      = disk_info.raid_disk_info.state
                if disk_info.raid_disk_info.raid_type == msg_pds.RAID_TYPE_SAS2RAID:   info['raid_type'] = "SAS2Raid" 
                elif disk_info.raid_disk_info.raid_type == msg_pds.RAID_TYPE_MEGARAID: info['raid_type'] = "MegaRaid" 
                elif disk_info.raid_disk_info.raid_type == msg_pds.RAID_TYPE_HPSARAID: info['raid_type'] = "HPSARaid" 

            info['disk_type'] = ""
            if disk_info.disk_type == msg_pds.DISK_TYPE_HDD:
                info['disk_type'] = "HDD"
            if disk_info.disk_type == msg_pds.DISK_TYPE_SSD:
                info['disk_type'] = "SSD"

            if disk_info.disk_name == "":
                info["disk_name"]   = ""
                info["actual_state"] = "ONLINE"
                info["part_count"]   = ""
            else:
                info["disk_name"]   = disk_info.disk_name
                info["part_count"]   = len(disk_info.diskparts)
                if disk_info.actual_state == True: info['actual_state'] = "ONLINE"
                else: info['actual_state'] = "MISSING"
            if disk_info.HasField("raid_disk_info") and not disk_info.HasField("nvme_diskhealth_info") \
                and disk_info.raid_disk_info.HasField("health"):
                info["health"] = disk_info.raid_disk_info.health    
            elif disk_info.HasField("nvme_diskhealth_info") and not disk_info.HasField("raid_disk_info") \
                and disk_info.nvme_diskhealth_info.HasField("health"):
                info["health"] = disk_info.nvme_diskhealth_info.health
            else:
                info["health"] = "--"

            # 补充raid信息
            if disk_info.HasField('raid_disk_info'):
                raid_disk_info = disk_info.raid_disk_info
                info['drive_type']   = "%s/%s" % (raid_disk_info.drive_type.upper(), raid_disk_info.protocol.upper())
                info['slot']         = "%s:%s:%s" % (raid_disk_info.ctl, raid_disk_info.eid, raid_disk_info.slot) 
                info['model']        = raid_disk_info.model 
                info['raid_state']   = raid_disk_info.state 
                info['raid_size']    = raid_disk_info.size
                if raid_disk_info.raid_type == msg_pds.RAID_TYPE_SAS2RAID:
                    info['raid_size']    = self.format_disk_size_sector(raid_disk_info.size)
                info["uuid"] = disk_info.header.uuid

            out.append(info)

        if self.platform == "pbdata":
            # 补充仅raid卡能认到的盘
            for raid_disk_info in response.body.Extensions[msg_mds.get_disk_list_response].raid_disk_infos:
                info = {}
                info['disk_name']   = "" 
                info['dev_name']     = "--" 
                info['size']         = "--" 
                info['free_size']    = "--" 
                info['part_count']   = "" 
                info['actual_state'] = "ONLINE" 
                info['drive_type']   = "%s/%s" % (raid_disk_info.drive_type.upper(), raid_disk_info.protocol.upper())
                info['slot']         = "%s:%s:%s" % (raid_disk_info.ctl, raid_disk_info.eid, raid_disk_info.slot) 
                info['model']        = raid_disk_info.model 
                info['raid_state']   = raid_disk_info.state 
                info['raid_size']    = raid_disk_info.size
                if raid_disk_info.raid_type == msg_pds.RAID_TYPE_SAS2RAID:
                    info['raid_size']    = self.format_disk_size_sector(raid_disk_info.size)
                info['uuid']         = "--"
                if raid_disk_info.raid_type == msg_pds.RAID_TYPE_SAS2RAID:   info['raid_type'] = "SAS2Raid" 
                elif raid_disk_info.raid_type == msg_pds.RAID_TYPE_MEGARAID: info['raid_type'] = "MegaRaid" 
                elif raid_disk_info.raid_type == msg_pds.RAID_TYPE_HPSARAID: info['raid_type'] = "HPSARaid" 
                out.append(info)

        tbl_th  = ['Disk Name','Dev Name','Size','Free Size','Part Count','Disk Type', 'State']
        tbl_key = ['disk_name','dev_name','size','free_size','part_count','disk_type', 'actual_state']
        if self.platform == "pbdata":
            tbl_th.extend( ['Raid.Addr', 'Raid.size', 'Raid.Med',   'Health'])
            tbl_key.extend(['slot',      'raid_size', 'drive_type', 'health'])

        if self.detail == True:
            tbl_th.extend( ['Raid.type',"Raid State", "Disk Model"])
            tbl_key.extend(['raid_type',"state",      "model"])

        formats = {}
        formats['size'] = {}
        formats['size']['fun'] = "disk_size_sector"
        formats['size']['params'] = {'cl':True}
        formats['free_size'] = {}
        formats['free_size']['fun'] = "disk_size_sector"
        formats['free_size']['params'] = {'cl':True}
        formats['actual_state'] = {}
        formats['actual_state']['fun'] = "online_state"
        formats['actual_state']['params'] = {"cl":True}

        return self.common_list(tbl_th, tbl_key, idx_key='disk_name', data=out, formats=formats, count=True)

    # Disk list 分区显示形式
    def cli_list_by_part(self, request, response):
        out  = []
        diskpart_to_lun_name = {}
        for disk_info in response.body.Extensions[msg_mds.get_disk_list_response].disk_infos:
            for _diskpart_to_lun_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name]:
                diskpart_to_lun_name[_diskpart_to_lun_name.key] = _diskpart_to_lun_name.value
        diskpart_to_lun_name_smartcache = {}
        for disk_info in response.body.Extensions[msg_mds.get_disk_list_response].disk_infos:
            for _diskpart_to_lun_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name_smartcache]:
                diskpart_to_lun_name_smartcache[_diskpart_to_lun_name.key] = _diskpart_to_lun_name.value
        diskpart_to_pool_name = {}
        for disk_info in response.body.Extensions[msg_mds.get_disk_list_response].disk_infos:
            for _diskpart_to_pool_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_pool_name]:
                diskpart_to_pool_name[_diskpart_to_pool_name.key] = _diskpart_to_pool_name.value

        for disk_info in filter(lambda disk_info:disk_info.disk_name != "", response.body.Extensions[msg_mds.get_disk_list_response].disk_infos):
            for diskpart in disk_info.diskparts:
                info = {}
                info["disk_part_id"]    = "%sp%s" % (disk_info.disk_name, diskpart.disk_part)
                info["size"]            = diskpart.size

                info['disk_type'] = ""
                if disk_info.disk_type == msg_pds.DISK_TYPE_HDD:
                    info['disk_type'] = "HDD"
                if disk_info.disk_type == msg_pds.DISK_TYPE_SSD:
                    info['disk_type'] = "SSD"

                if disk_info.actual_state == True:
                    info['actual_state'] = "ONLINE"
                else:
                    info['actual_state'] = "MISSING"

                if disk_info.dev_name == "":
                    info['dev_name'] = ""
                else:
                    info['dev_name'] = diskpart.dev_name

                disk2part = "%s.%s" % (disk_info.header.uuid, diskpart.disk_part)
                info['used_by_lun'] = "--"
                if disk2part in diskpart_to_lun_name.keys():
                    info['used_by_lun'] = "%s" % diskpart_to_lun_name[disk2part]
                info['used_by_pool'] = "--"
                if disk2part in diskpart_to_pool_name.keys():
                    info['used_by_pool'] = "%s" % diskpart_to_pool_name[disk2part]
                info['used_by_smartcache'] = "--"
                if disk2part in diskpart_to_lun_name_smartcache.keys():
                    info['used_by_smartcache'] = "%s" % diskpart_to_lun_name_smartcache[disk2part]

                out.append(info)

        formats = {}
        formats['size'] = {}
        formats['size']['fun'] = "disk_size_sector"
        formats['size']['params'] = {'cl':True}
        formats['actual_state'] = {}
        formats['actual_state']['fun'] = "online_state"
        formats['actual_state']['params'] = {"cl":True}

        tbl_th  = ['DiskPart Name', 'Dev Name', 'Size', 'Disk Type', 'As Lun',      'As PalPool',   'As SmartCache',      'State']
        tbl_key = ['disk_part_id',  'dev_name', 'size', 'disk_type', 'used_by_lun', 'used_by_pool', 'used_by_smartcache', 'actual_state']
        return self.common_list(tbl_th, tbl_key, idx_key='disk_part_id', data=out, formats=formats, count=True)

    def cli_list_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Disk add
    def cli_add(self, request, response):
        return "Success : add disk success"

    def cli_add_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    #disk info
    def cli_info_error(self,request,response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    def cli_info(self,request,response):
        disk_info = response.body.Extensions[msg_mds.get_disk_info_response].disk_info
        out  = []
        out += [{"name":"DiskName", "value":disk_info.disk_name}]
        if disk_info.disk_type == msg_pds.DISK_TYPE_HDD:
            out += [{"name":"Device",   "value":"HDD"+" "+disk_info.dev_name+" "+  self.format_disk_size_sector(disk_info.size)}]
        elif disk_info.disk_type == msg_pds.DISK_TYPE_SSD:
            out += [{"name":"Device",   "value":"SDD"+" "+disk_info.dev_name+" "+  self.format_disk_size_sector(disk_info.size)}]
        else:
            out += [{"name":"Device",   "value":" "+" "+disk_info.dev_name+" "+ self.format_disk_size_sector(disk_info.size)}]

        if self.platform == "pbdata":
            out += [{"name":"Address",  "value":"%s:%s:%s" % (disk_info.raid_disk_info.ctl, disk_info.raid_disk_info.eid,
          disk_info.raid_disk_info.slot)}]
        
        if disk_info.actual_state == True:
            out += [{"name":"State",    "value":"Online"}]
        else:
            out += [{"name":"State",    "value":"Missing"}]

        part_num = len(disk_info.diskparts)
        diskpart_to_lun_name = {}
        for _diskpart_to_lun_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name]:
            diskpart_to_lun_name[_diskpart_to_lun_name.key] = _diskpart_to_lun_name.value
        diskpart_to_lun_name_smartcache = {}
        for _diskpart_to_lun_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_lun_name_smartcache]:
            diskpart_to_lun_name_smartcache[_diskpart_to_lun_name.key] = _diskpart_to_lun_name.value
        diskpart_to_pool_name = {}
        for _diskpart_to_pool_name in disk_info.Extensions[msg_mds.ext_diskinfo_diskpart_to_pool_name]:
            diskpart_to_pool_name[_diskpart_to_pool_name.key] = _diskpart_to_pool_name.value 
        if part_num != 0:
            out += [{"name":"Parts", "value":"%-13s %-5s %-5s %-6s %s" % ("Name", "Size", "Lun","Pool","SmartCache")}]
            for part in disk_info.diskparts:

                disk2part = "%s.%s" % (disk_info.header.uuid, part.disk_part)
                info = {}
                info['used_by_lun'] = "--"
                if disk2part in diskpart_to_lun_name.keys():
                    info['used_by_lun'] = "%s" % diskpart_to_lun_name[disk2part]
                info['used_by_pool'] = "--"
                if disk2part in diskpart_to_pool_name.keys():
                    info['used_by_pool'] = "%s" % diskpart_to_pool_name[disk2part]
                info['used_by_smartcache'] = "--"
                if disk2part in diskpart_to_lun_name_smartcache.keys():
                    info['used_by_smartcache'] = "%s" % diskpart_to_lun_name_smartcache[disk2part]
                out += [{"name":"", "value":"%-13s %-5s %-5s %-6s %s" % (part.dev_name, self.format_disk_size_sector(part.size), 
                info['used_by_lun'],info['used_by_pool'],info['used_by_smartcache'])}]

        out += [{"name":"Health", "value":"%-25s %-10s" % ("ATTR","Status")}]
        if disk_info.HasField('nvme_diskhealth_info') and not disk_info.HasField('raid_disk_info'):
            nvme_health_info = disk_info.nvme_diskhealth_info
            if nvme_health_info.HasField("life") and nvme_health_info.life > 0:
                out += [{"name":"", "value":"%-25s %-10s" % ("Life",nvme_health_info.life)}]
            else:
                out += [{"name":"", "value":"%-25s %-10s" % ("Life","Unknown")}]
            if nvme_health_info.HasField("totallife") and nvme_health_info.totallife > 0:
                out += [{"name":"", "value":"%-25s %-10s" % ("TotalLife",nvme_health_info.totallife)}]
            else:
                out += [{"name":"", "value":"%-25s %-10s" % ("TotalLife","Unknown")}]
            if nvme_health_info.HasField("media_status"):
                out += [{"name":"", "value":"%-25s %-10s" % ("media_status",nvme_health_info.media_status)}]
        elif disk_info.HasField('raid_disk_info') and not disk_info.HasField('nvme_diskhealth_info'):
            if self.platform == "pbdata":
                if disk_info.disk_type == msg_pds.DISK_TYPE_SSD and disk_info.raid_disk_info.HasField("ssd_diskhealth_info"):
                    disk_healthy_info = disk_info.raid_disk_info.ssd_diskhealth_info
                    if disk_healthy_info.HasField("life"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Life",disk_healthy_info.life)}]
                    if disk_healthy_info.HasField("offline_uncorrectable"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Offline_Uncorrectable",disk_healthy_info.offline_uncorrectable)}]
                    if disk_healthy_info.HasField("reallocated_event_count"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Reallocated_Event_Count",disk_healthy_info.reallocated_event_count)}]
                    if disk_healthy_info.HasField("reallocated_sector_ct"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Reallocated_Sector_Ct",disk_healthy_info.reallocated_sector_ct)}]
                    if disk_healthy_info.HasField("power_on_hours"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Power_On_Hours",disk_healthy_info.power_on_hours)}]
                    if disk_healthy_info.HasField("temperature_celsius"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Temperature_Celsius",disk_healthy_info.temperature_celsius)}]
                    if disk_healthy_info.HasField("raw_read_error_rate"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Raw_Read_Error_Rate",disk_healthy_info.raw_read_error_rate)}]
                    if disk_healthy_info.HasField("totallife"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("TotalLife",disk_healthy_info.totallife)}]
                    if disk_healthy_info.HasField("media_wearout_indicator"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Media_Wearout_Indicator",disk_healthy_info.media_wearout_indicator)}]
                    if disk_healthy_info.HasField("spin_retry_count"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Spin_Retry_Count",disk_healthy_info.spin_retry_count)}]
                    if disk_healthy_info.HasField("command_timeout"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Command_Timeout",disk_healthy_info.command_timeout)}]
                    if disk_healthy_info.HasField("uncorrectable_sector_ct"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Uncorrectable_Sector_Ct",disk_healthy_info.uncorrectable_sector_ct)}]
                    if disk_healthy_info.HasField("ssd_life_left"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("SSD_Life_Left",disk_healthy_info.ssd_life_left)}]
                elif disk_info.disk_type == msg_pds.DISK_TYPE_HDD and disk_info.raid_disk_info.HasField("hdd_diskhealth_info"):
                    disk_healthy_info = disk_info.raid_disk_info.hdd_diskhealth_info
                    if disk_healthy_info.HasField("verifies_gb"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Verifies_GB",disk_healthy_info.verifies_gb)}]
                    if disk_healthy_info.HasField("life_left"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Life_Left",disk_healthy_info.life_left)}]
                    if disk_healthy_info.HasField("uncorrected_reads"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Uncorrected_Reads",disk_healthy_info.uncorrected_reads)}]
                    if disk_healthy_info.HasField("uncorrected_verifies"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Uncorrected_Verifies",disk_healthy_info.uncorrected_verifies)}]
                    if disk_healthy_info.HasField("corrected_reads"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Corrected_Reads",disk_healthy_info.corrected_reads)}]
                    if disk_healthy_info.HasField("writes_gb"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Writes_GB",disk_healthy_info.writes_gb)}]
                    if disk_healthy_info.HasField("load_cycle_pct_left"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Load_Cycle_Pct_Left",disk_healthy_info.load_cycle_pct_left)}]
                    if disk_healthy_info.HasField("load_cycle_count"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Load_Cycle_Count",disk_healthy_info.load_cycle_count)}]
                    if disk_healthy_info.HasField("reallocated_sector_ct"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Reallocated_Sector_Ct",disk_healthy_info.reallocated_sector_ct)}]
                    if disk_healthy_info.HasField("power_on_hours"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Power_On_Hours",disk_healthy_info.power_on_hours)}]

                    if disk_healthy_info.HasField("corrected_writes"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Corrected_Writes",disk_healthy_info.corrected_writes)}]
                    if disk_healthy_info.HasField("non_medium_errors"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Non_Medium_Errors",disk_healthy_info.non_medium_errors)}]
                    if disk_healthy_info.HasField("reads_gb"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Reads_GB",disk_healthy_info.reads_gb)}]
                    if disk_healthy_info.HasField("load_cycle_spec"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Load_Cycle_Spec",disk_healthy_info.load_cycle_spec)}]
                    if disk_healthy_info.HasField("start_stop_pct_left"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Start_Stop_Pct_Left",disk_healthy_info.start_stop_pct_left)}]
                    if disk_healthy_info.HasField("uncorrected_writes"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Uncorrected_Writes",disk_healthy_info.uncorrected_writes)}]
                    if disk_healthy_info.HasField("start_stop_spec"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Start_Stop_Spec",disk_healthy_info.start_stop_spec)}]
                    if disk_healthy_info.HasField("corrected_verifies"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Corrected_Verifies",disk_healthy_info.corrected_verifies)}]
                    if disk_healthy_info.HasField("start_stop_cycles"):
                        out += [{"name":"", "value":"%-25s %-10s" % ("Start_Stop_Cycles",disk_healthy_info.start_stop_cycles)}]
        tbl_th  = ['Keys', 'Values']
        tbl_key = ['name',  'value']
        return self.common_list(tbl_th=tbl_th, tbl_key=tbl_key, data=out, sort=False)

    # Disk drop
    def cli_drop(self, request, response):
        return "Success : drop disk success"

    def cli_drop_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Disk led
    def cli_led(self, request, response):
        action = "off"
        if request.body.Extensions[msg_mds.disk_led_request].is_on:
            action = "on"
        return "Success : set disk ligth to '%s' success" % action

    def cli_led_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Quality test
    def cli_quality_test(self, request, response):
        return "Success : disk quality test task has been accepted!"

    def cli_qualityt_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
    
    # Quality info
    def cli_quality_info(self, request, response):
        out = []
        for device in response.body.Extensions[msg_mds.get_disk_quality_info_response].disk_quality_info.quality_test_result:
            info = {}
            if device.HasField('randread_iops'): 
                info['randread-iops'] = device.randread_iops
            else:
                info['randread-iops'] = "--"
            if device.HasField('read_bw'): 
                info['read-bw']       = "%s KB/s" % device.read_bw
            else:
                info['read-bw']       = "--"
            if device.HasField('name'): 
                info['name']          = device.name
            else:
                info['name']          = "--"
            if device.HasField('path'): 
                info['path']          = device.path
            else:
                info['path']          =  "--"
            out.append(info)

        tbl_th  = ['Name', 'Path', 'RandRead-IOPS', 'Read-BW']
        tbl_key = ['name', 'path', 'randread-iops', 'read-bw']
        return self.common_list(tbl_th, tbl_key, data=out, idx_key='name', count=True)
    
    #  Quality list
    def cli_quality_list(self, request, response):
        out = []
        for result in response.body.Extensions[msg_mds.get_disk_quality_list_response].disk_quality_infos:
            info = {}
            if result.curr_test:
                info['t_time']     = time.strftime('%Y-%m-%d.%H:%M:%S (testing...)', time.localtime(result.t_time))  
            else:
                info['t_time']     = time.strftime('%Y-%m-%d.%H:%M:%S', time.localtime(result.t_time))  
            info['disk_count'] = "%s" % str(result.disk_count)
            info['ioengine']   = "%s" % str(result.ioengine)
            info['runtime']    = "%s" % str(result.run_time)
            info['bs']         = "%s" % str(result.block_size)
            info['numjobs']    = "%s" % str(result.num_jobs)
            info['iodepth']    = "%s" % str(result.iodepth)
            out.append(info)
        tbl_th  = ['Test time', 'Disk count', 'Attr.IOengine', 'Attr.Runtime', 'Attr.BlockSize', 'Attr.Numjobs', 'Attr.IOdepth']
        tbl_key = ['t_time',    'disk_count', 'ioengine',      'runtime',      'bs',             'numjobs',      'iodepth']
        return self.common_list(tbl_th, tbl_key, data=out, idx_key='t_time', count=True)

    def cli_quality_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))

    # Disk replace
    def cli_replace(self, request, response):
        return "Success : replace disk success"

    def cli_replace_error(self, request, response):
        retcode = response.rc.retcode
        message = response.rc.message
        return self.out_error("Error [%s]: %s!" % (retcode, message))
