#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import parted, time, json, pyudev, os
from pdsframe import *
from service_ios import g
from service_ios.base.cmdlist import *

SAS2CLI = "/opt/smartmgr/scripts/sas2ircu"

# 最长需要2小时更新
MAX_UPDATE_TIME = 2*3600

def prefix_lineno(lines, prefix):
    lineno = []
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lineno.append(i)
    return lineno

class SAS2Raid():
    # 最后更新时间
    LAST_UPDATE_TIME = 0
    # 磁盘列表缓存
    CACHE_DISK_LIST  = []
    # 最后事件序号
    LAST_SEQ_NUM     = None

    def __fix_pci_addr(self, pci_addr):
        # 00h:04h:00h:00h => 0000:04:00.0
        items = pci_addr.lower().replace('h', '').split(':')
        return "%s:%s:%s.0" % (items[0].rjust(4, "0"), items[1], items[2])

    def __get_raid_wwid(self, raids, eid_slot):
        for raid in raids:
            if eid_slot in raid['phy_disk']:
                return "0x%s" % raid['Volume wwid']
        return None

    # 获取所有sas2raid的raid卡列表
    def __get_ctl_list(self):
        ctls = []
        e, out = command("%s list" % SAS2CLI)
        if e: 
            if e == 256: return (0, "")
            return (1, out)
        out = [out.strip() for out in out.splitlines() if out.strip() != ""] 
        ctl_lineno = prefix_lineno(out, "Index")
        for lineno in ctl_lineno:
            items=out[lineno+2].split()
            ctl_info = {}
            ctl_info['index']    = int(items[0])
            ctl_info['vendor']   = items[1]
            ctl_info['pci_addr'] = self.__fix_pci_addr(items[4])
            ctls.append(ctl_info)
        # print json.dumps(ctls, indent=4)
        return 0, ctls

    # 获取指定控制器下的磁盘列表
    def __get_ctl_disk_list(self, ctl, pci_addr):
        raids = []
        disks = []
        e, out = command("%s %s display" % (SAS2CLI, ctl))
        if e: return e, out
        out = [out.strip() for out in out.splitlines() if out.strip() != ""] 
        # 获取该raid下的raid配置列表
        raid_lineno = prefix_lineno(out, "IR volume")
        for lineno in raid_lineno:
            raid_info = {}
            raid_info['Volume ID']        = out[lineno+1].split(':')[1].strip()
            raid_info['Status of volume'] = out[lineno+2].split(':')[1].strip()
            raid_info['Volume wwid']      = out[lineno+3].split(':')[1].strip()
            raid_info['RAID level']       = out[lineno+4].split(':')[1].strip()
            raid_info['size']             = out[lineno+5].split(':')[1].strip()
            raid_info['phy_disk']         = []
            i = 0
            while True:
                if out[lineno+7+i].split(':')[0].strip().startswith('PHY'):
                    raid_info['phy_disk'].append(":".join(out[lineno+7+i].split(':')[1:]).strip())
                    i += 1
                else:
                    break
            raids.append(raid_info)
        # print json.dumps(raids, indent=4)

        # 获取disk列表
        disk_lineno = prefix_lineno(out, "Device is a Hard disk")
        for lineno in disk_lineno:
            disk_info = {}
            disk_info['pci_addr']     = pci_addr
            disk_info['ctl']          = ctl
            disk_info['eid']          = out[lineno+1].split(':')[1].strip()
            disk_info['slot']         = out[lineno+2].split(':')[1].strip()
            disk_info['sas_address']  = "0x%s" % out[lineno+3].split(':')[1].strip().replace('-', '')
            disk_info['state']        = out[lineno+4].split(':')[1].strip()
            if disk_info['state'].lower().find("missing") != -1:
                continue
            disk_info['size']         = out[lineno+5].split(':')[1].strip().split('/')[1]
            disk_info['model_number'] = out[lineno+7].split(':')[1].strip()
            disk_info['serial_no']    = out[lineno+9].split(':')[1].strip()
            disk_info['guid']         = out[lineno+10].split(':')[1].strip()
            disk_info['protocol']     = out[lineno+11].split(':')[1].strip()
            disk_info['drive_type']   = out[lineno+12].split(':')[1].strip().split('_')[1]
            disk_info['raid_wwid']    = self.__get_raid_wwid(raids, "%s:%s" % (disk_info['eid'], disk_info['slot']))
            disks.append(disk_info)
        # print json.dumps(disks, indent=4)
        return 0, disks

    # 获取udev下所有包含sas_address的磁盘列表
    def __get_udev_disk_list(self):
        disks = []
        context = pyudev.Context()
        devices = context.list_devices(subsystem='block', DEVTYPE='disk')
        for device in devices:
            major = os.major(device.device_number)
            if not major == 8 and not (65 <= major <= 71) and not (128 <= major <= 135):
                continue
            if device.parent.attributes.get('sas_address') != None:
                disk_info = {}
                disk_info['dev_name']    = device['DEVNAME']
                disk_info['sas_address'] = device.parent.attributes.get('sas_address')
                disk_info['pic_address'] = device.sys_path.split("/")[5]
                disks.append(disk_info)
        return 0, disks

    def __get_last_seq_num(self):
        try:
            f = open('/sys/kernel/uevent_seqnum', 'r')
            seq = int(f.read())
            f.close()
        except Exception as e:
            return -1, str(e)
        return 0, seq

    # 获取sas2raid所有控制器下的所有磁盘的汇总信息
    def get_disk_list(self):
        # 通用机型不获取raid卡信息
        if g.platform['platform'] == "generic":
            return 0, []

        # 获取最后事件序列号
        e, seq_num = self.__get_last_seq_num()
        if e: return e, seq_num
        if seq_num == SAS2Raid.LAST_SEQ_NUM and int(time.time()) - SAS2Raid.LAST_UPDATE_TIME < MAX_UPDATE_TIME:
            return 0, SAS2Raid.CACHE_DISK_LIST

        e, udev_disks = self.__get_udev_disk_list()
        if e: return e, udev_disks
        addr_to_udev = {}
        for udev_disk in udev_disks:
            addr_to_udev["%s-%s" % (udev_disk['pic_address'], udev_disk['sas_address'])] = udev_disk

        e, ctls = self.__get_ctl_list()
        if e: return e, ctls
        disks = []
        for ctl in ctls:
            e, _disks = self.__get_ctl_disk_list(ctl['index'], ctl['pci_addr'])
            if e: continue
            disks.extend(_disks)

        for disk in disks:
            if disk['raid_wwid'] == None:
                addr = "%s-%s" % (disk['pci_addr'], disk['sas_address']) 
            else:
                addr = "%s-%s" % (disk['pci_addr'], disk['raid_wwid']) 
            if addr in addr_to_udev.keys():
                disk['dev_name'] = addr_to_udev[addr]['dev_name']
        # print json.dumps(disks, indent=4)

        # 返回值矫正
        disk_list = []
        for disk in disks:
            disk_info = {}
            disk_info['ctl']        = int(disk['ctl'])
            disk_info['eid']        = int(disk['eid'])
            disk_info['slot']       = int(disk['slot'])
            disk_info['drive_type'] = disk['drive_type'].lower()
            disk_info['protocol']   = disk['protocol'].lower()
            disk_info['pci_addr']   = disk['pci_addr']
            disk_info['size']       = disk['size']
            disk_info['model']      = disk['model_number']
            disk_info['state']      = disk['state']
            disk_info['dev_name']   = disk.has_key('dev_name') and disk['dev_name'] or ""
            disk_list.append(disk_info)
        # print json.dumps(disk_list, indent=4)

        SAS2Raid.LAST_SEQ_NUM     = seq_num
        SAS2Raid.LAST_UPDATE_TIME = int(time.time())
        SAS2Raid.CACHE_DISK_LIST  = disk_list

        return 0, SAS2Raid.CACHE_DISK_LIST

    #./sas2ircu 1 LOCATE 1:5 off 关灯        
    def led(self, ces_addr, is_on):
        ctl  = ces_addr.split(":")[0]
        eid  = ces_addr.split(":")[1]
        slot = ces_addr.split(":")[2]

        if is_on:
            action = "on"
        else:
            action = "off"
        
        e, res = command("%s %s %s %s %s" % (SAS2CLI, ctl, 'locate', eid+":"+slot, action))
        if e: return e, res

        lines = res.splitlines()
        if 'Successfully' in lines[-1]:
            return 0, ""
        return -1, "Unknown failed reason"
