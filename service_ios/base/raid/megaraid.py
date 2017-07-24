#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import parted, time, json, pyudev, os, re
from pdsframe import *
from service_ios import g
from service_ios.base.cmdlist import *
from service_ios.base.common import is_dell_perc

# 判断是否是dell机器
if is_dell_perc():
    STORCLI = "/opt/MegaRAID/perccli/perccli64"
else:
    STORCLI = "/opt/smartmgr/scripts/storcli64"

MEGACLI = '/opt/MegaRAID/MegaCli/MegaCli64'

# 最长需要2小时更新
MAX_UPDATE_TIME = 2*3600

def prefix_lineno(lines, prefix):
    lineno = []
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lineno.append(i)
    return lineno

class MegaRaid():
    # 最后更新时间
    LAST_UPDATE_TIME = 0
    # 磁盘列表缓存
    CACHE_DISK_LIST  = []
    # 最后事件序号
    LAST_SEQ_NUM     = None

    def __fix_pci_addr(self, pci_addr):
        # 00:04:00:00 => 0000:04:00.0
        items = pci_addr.lower().split(':')
        return "%s:%s:%s.0" % (items[0].rjust(4, "0"), items[1], items[2])

    def __get_vd(self, raids, dg):
        for raid in raids:
            if int(raid['dg']) == dg:
                return raid['vd']
        return None

    # 获取所有megaraid的raid卡列表
    def __get_ctl_list(self):
        ctls = []
        e, out = command("%s show J" % STORCLI)
        if e: return e, out
        out = json.loads(out)
        if out['Controllers'][0]['Command Status']['Status']  != "Success":
            return -1, "Get megaraid ctl list error"
        if out['Controllers'][0]['Response Data']['Number of Controllers'] == 0:
            return 0, {}
        for ctl in out['Controllers'][0]['Response Data']['System Overview']:
            ctl_info = {}
            ctl_info["index"] = ctl['Ctl']
            ctl_info["model"] = ctl['Model']
            ctls.append(ctl_info)
        return 0, ctls

    # 获取指定控制器下的磁盘列表
    def __get_ctl_disk_list(self, ctl):
        disks = []
        raids = []
        e, out = command("%s /c%s show J" % (STORCLI, ctl))
        if e: return e, out
        out = json.loads(out)
        if out['Controllers'][0]['Command Status']['Status']  != "Success":
            return -1, "Get megaraid ctl list error"
        pci_addr = self.__fix_pci_addr(out['Controllers'][0]['Response Data']['PCI Address'])
        if out['Controllers'][0]['Response Data'].has_key('VD LIST'):
            for raid in out['Controllers'][0]['Response Data']['VD LIST']:
                raid_info = {}
                raid_info["dg"]    = raid['DG/VD'].split('/')[0]
                raid_info["vd"]    = raid['DG/VD'].split('/')[1]
                raid_info["type"]  = raid['TYPE']
                raid_info["state"] = raid['State']
                raid_info["Size"]  = raid['Size']
                raids.append(raid_info)
        # print json.dumps(raids, indent=4)

        if out['Controllers'][0]['Response Data'].has_key('PD LIST'):
            for disk in out['Controllers'][0]['Response Data']['PD LIST']:
                disk_info = {}
                disk_info["pci_addr"] = pci_addr
                disk_info["ctl"]      = ctl
                disk_info["eid"]      = disk['EID:Slt'].split(":")[0]
                disk_info["slot"]     = disk['EID:Slt'].split(":")[1]
                disk_info["state"]    = disk['State']
                disk_info["dg"]       = disk['DG']
                disk_info["vd"]       = self.__get_vd(raids, disk_info["dg"])
                disk_info["size"]     = disk['Size']
                disk_info["intf"]     = disk['Intf']
                disk_info["med"]      = disk['Med']
                disk_info["model"]    = disk['Model'].strip()
                disk_info['did']      = disk['DID']
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
            if device.find_parent('scsi') == None:
                continue
            disk_info = {}
            disk_info['dev_name']    = device['DEVNAME']
            disk_info['pic_address'] = device.sys_path.split("/")[5]
            disk_info['vd']          = os.path.basename(device.find_parent('scsi').sys_path).split(":")[2]
            disks.append(disk_info)
        return 0, disks

    # ./storcli64 /c0/e30/s10 show J
    # 获取指定ces的raid状态
    def __get_ces_state(self, ctl, eid, slot):
        e, out = command("%s /c%s/e%s/s%s show J" % (STORCLI, ctl, eid, slot))
        if e: return e, out
        out = json.loads(out)
        if out['Controllers'][0]['Command Status']['Status']  != "Success":
            return -1, "Get ces raid state error"
        return 0, out['Controllers'][0]['Response Data']['Drive Information'][0]['State']

    # ./storcli64 /c0/e30/s4 set good J
    # 修改硬盘状态信息为 unconfigrue good
    def __set_good(self, ctl, eid, slot):
        return command("%s /c%s/e%s/s%s set good J" % (STORCLI, ctl, eid, slot))

    def __del_foreign(self, ctl):
        return command("%s /c%s/fall del" % (STORCLI, ctl))

    # 清除指定卡上的保存的cache，由在线拔盘导致
    def __delete_preservedcache(self, ctl):
        e, res = command("%s -GetPreservedCacheList -a%s" % (MEGACLI, ctl))
        if e: return e, res
        vds = []
        for l in res.splitlines():
            m = re.search("^Virtual Drive\(Target ID (\d+)\)",l)
            if m != None and len(m.groups()) > 0: vds.append(int(m.groups()[0]))

        for vd in vds:
            e, res = command("%s -DiscardPreservedCache -L%s -force -a%s" % (MEGACLI, vd, ctl))
            if e: return e, res
        return 0, ''

    # 做raid0
    def make_raid(self, ces_addr):
        ctl  = ces_addr.split(":")[0]
        eid  = ces_addr.split(":")[1]
        slot = ces_addr.split(":")[2]
        e, res = self.__delete_preservedcache(ctl)
        if e: return e, res

        self.__set_good(ctl, eid, slot)
        self.__del_foreign(ctl)

        e, state = self.__get_ces_state(ctl, eid, slot)
        if e: return e, state

        if state == "Onln":
            return 0, ''
               
        # 其他状态不支持
        if state != "UGood":
            return -1, "Unsupport raid state of ces %s:%s:%s, state:%s" % (ctl, eid, slot, state)

        e, res = command("%s /c%s add vd type=raid0 drives=%s:%s J" % (STORCLI, ctl, eid, slot))
        if e: return e, res
        res = json.loads(res)
        if res['Controllers'][0]['Command Status']['Status'] != "Success":
            return -1, "Get preserved cache failed"

        # 重新获取磁盘列表, 用于做完raid后, 系统不能及时拿到dev-name
        dev_name  = None
        try_times = 8
        while try_times > 0:
            try_times -= 1
            time.sleep(1)
            e, disk_list = self.get_disk_list(True)
            if e: continue
            for disk in disk_list:
                if "%s:%s:%s" % (disk['ctl'], disk['eid'], disk['slot']) == ces_addr and disk['dev_name'] != "":
                    dev_name = disk['dev_name']
                    break
            if dev_name != None:
                break
        if dev_name != None:
            return 0, dev_name
        return -1, 'Get dev name failed'

    def __get_last_seq_num(self):
        e, res = command("%s /call show events type=latest=1 filter=info" % STORCLI)
        if e: return e, res

        seq = []
        lines = res.splitlines()
        for line in lines:
            if not line.strip().startswith("seqNum"):
                continue
            items = line.split()
            if len(items) == 2:
                seq.append(items[1])
        return 0, "".join(seq)

    # 获取megaraid所有控制器下的所有磁盘的汇总信息
    def get_disk_list(self, force=False):
        # 通用机型不获取raid卡信息
        if g.platform['platform'] == "generic":
            return 0, []

        # 获取最后事件序列号
        e, seq_num = self.__get_last_seq_num()
        if e: return e, seq_num
        if force == False and seq_num == MegaRaid.LAST_SEQ_NUM and int(time.time()) - MegaRaid.LAST_UPDATE_TIME < MAX_UPDATE_TIME:
            return 0, MegaRaid.CACHE_DISK_LIST

        e, udev_disks = self.__get_udev_disk_list()
        if e: return e, udev_disks
        addr_to_udev = {}
        for udev_disk in udev_disks:
            addr_to_udev["%s-%s" % (udev_disk['pic_address'], udev_disk['vd'])] = udev_disk

        e, ctls = self.__get_ctl_list()
        if e: return e, ctls
        disks = []
        for ctl in ctls:
            e, _disks = self.__get_ctl_disk_list(ctl['index'])
            if e: continue
            disks.extend(_disks)

        for disk in disks:
            addr = "%s-%s" % (disk['pci_addr'], disk['vd']) 
            if addr in addr_to_udev.keys():
                disk['dev_name'] = addr_to_udev[addr]['dev_name']
        # 返回值矫正
        disk_list = []
        for disk in disks:
            disk_info = {}
            disk_info['ctl']        = int(disk['ctl'])
            disk_info['eid']        = int(disk['eid'])
            disk_info['slot']       = int(disk['slot'])
            disk_info['drive_type'] = disk['med'].lower()
            disk_info['protocol']   = disk['intf'].lower()
            disk_info['pci_addr']   = disk['pci_addr']
            disk_info['size']       = disk['size']
            disk_info['model']      = disk['model']
            disk_info['state']      = disk['state']
            disk_info['dev_name']   = disk.has_key('dev_name') and disk['dev_name'] or ""
            disk_info['did']        = disk['did']
            disk_list.append(disk_info)
        # print json.dumps(disk_list, indent=4)

        MegaRaid.LAST_SEQ_NUM     = seq_num
        MegaRaid.LAST_UPDATE_TIME = int(time.time())
        MegaRaid.CACHE_DISK_LIST  = disk_list

        return 0, MegaRaid.CACHE_DISK_LIST

    #MegaCli  -AdpSetProp UseDiskActivityforLocate 0 -a0 
    def __mega_init(self, ctl):
        e, res = command("%s %s %s %s %s %s" % (MEGACLI, '-AdpSetProp', 'UseDiskActivityforLocate', '0', ctl, '-NoLog'))
        if e: return e, res
        lines = res.splitlines()

        if 'Exit Code' in lines[-1]:
            line = lines[-1].split(':')
            if '0x00' in line[1]:
                return 0, ""
            else:
                return -1, "Unknown failed reason"

    #MegaCli  -PdLocate  -start  –physdrv[E:S]  -a0  让硬盘LED灯闪烁
    def led(self, ces_addr, is_on):
        ctl  = ces_addr.split(":")[0]
        eid  = ces_addr.split(":")[1]
        slot = ces_addr.split(":")[2]

        ctl = "-a"+str(ctl)

        e, res = self.__mega_init(ctl)
        if e: return e, res

        if is_on:
            action = "-start"
        else:
            action = "-stop"
       
        e, res = command("%s %s %s %s %s %s" % (MEGACLI, '-pdLocate', action, "-physdrv["+eid+":"+slot+"]", ctl, '-NoLog'))
        if e: return e, res

        lines = res.splitlines()
        if 'Exit Code' in lines[-1]:
            line = lines[-1].split(':')
            if '0x00' in line[1]:
                return 0, ""
        return -1, ""
