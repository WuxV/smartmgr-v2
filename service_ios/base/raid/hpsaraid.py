#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import parted, time, json, pyudev, os
from pdsframe import *
from service_ios import g
from service_ios.base.cmdlist import *

HPSSACLI = "/usr/sbin/hpssacli"

# 由于hpraid没有有效的方法获取到插拔盘的事件，因此无法控制缓存，因此暂时关闭缓存功能
MAX_UPDATE_TIME = 10

def prefix_lineno(lines, prefix, start=None, end=None):
    lineno = []
    for i, line in enumerate(lines[start:end]):
        if line.startswith(prefix):
            if start == None:
                _i = i
            else:
                _i = start+i
            lineno.append(_i)
    return lineno

class HPSARaid():
    # 最后更新时间
    LAST_UPDATE_TIME = 0
    # 磁盘列表缓存
    CACHE_DISK_LIST  = []
    # 最后事件序号
    LAST_SEQ_NUM     = None

    # 获取所有hpsaraid的raid卡列表
    def __get_ctl_list(self):
        ctls = []
        e, out = command("%s ctrl all show" % HPSSACLI)
        if e: 
            if e == 256: return (0, "")
            return (1, out)
        out = [out.strip() for out in out.splitlines() if out.strip() != ""] 
        ctl_lineno = prefix_lineno(out, "Smart Array")
        for lineno in ctl_lineno:
            items=out[lineno].split()
            ctl_info = {}
            ctl_info['index']    = int(items[5])
            ctls.append(ctl_info)
        return 0, ctls

    def __get_last_seq_num(self):
        try:
            f = open('/sys/kernel/uevent_seqnum', 'r')
            seq = int(f.read())
            f.close()
        except Exception as e:
            return -1, str(e)
        return 0, seq

    # 获取指定控制器下的磁盘列表
    def __get_ctl_disk_list(self, ctl):
        disks = []
        e, out = command("%s ctrl slot=%s show config detail" % (HPSSACLI, ctl))
        if e: return e, out
        out = [out.strip() for out in out.splitlines() if out.strip() != ""] 

        # 获取pci地址
        pci_addr = out[prefix_lineno(out, "PCI Address")[0]].split()[3]

        # 获取所有已经配置raid的盘
        array_lineno = prefix_lineno(out, "Array:")
        for i, lineno in enumerate(array_lineno):
            if i+1 == len(array_lineno):
                unassigned_lineno = prefix_lineno(out, "unassigned")
                if len(unassigned_lineno) != 0:
                    end = unassigned_lineno[0]
                else:
                    end = None
            else:
                end = array_lineno[i+1]
            # 获取logicaldrive名称
            logicaldrive = out[prefix_lineno(out, "Logical Drive:", start=lineno, end=end)[0]].split(":")[1].strip()
            # 获取磁盘名称
            disk_name = out[prefix_lineno(out, "Disk Name:", start=lineno, end=end)[0]].split(":")[1].strip()
            # 获取磁盘的raid状态
            disk_rd_state = out[prefix_lineno(out, "Status:", start=lineno, end=end)[1]].split(":")[1].strip()
            # 获取物理磁盘地址
            physicaldrive_lineno = prefix_lineno(out, "physicaldrive", start=lineno, end=end)
            for lineno in physicaldrive_lineno:
                # 过滤掉在Logical Drive下的物理设备
                if out[lineno].count("port"):
                    continue
                disk = {}
                if disk_rd_state.lower() == "ok":
                    disk['dev_name']  = disk_name
                disk['ctl']           = "%s:%s" % (ctl, out[lineno+1].split(":")[1].strip())
                disk['eid']           = int(out[lineno+2].split(":")[1].strip())
                disk['slot']          = int(out[lineno+3].split(":")[1].strip())
                disk['state']         = out[lineno+4].split(":")[1].strip()
                disk['drive_type']    = out[lineno+6].split(":")[1].count("Solid") == 0 and "HDD" or "SSD"
                disk['protocol']      = out[lineno+6].split(":")[1].count("SATA") == 0  and "SAS" or "STAT"
                disk['size']          = out[lineno+7].split(":")[1].strip()
                if disk['protocol'] == "SAS":
                    disk['Serial']        = out[lineno+12].split(":")[1].strip()
                    disk['model']         = out[lineno+13].split(":")[1].strip()
                else:
                    disk['Serial']        = out[lineno+11].split(":")[1].strip()
                    disk['model']         = out[lineno+12].split(":")[1].strip()
                disk['pci_addr']      = pci_addr
                disk['logicaldrive']  = logicaldrive
                disk['disk_rd_state'] = disk_rd_state
                # 过滤掉state不是"OK"的盘，目前已知的是Failed状态的盘是已经被拔掉的盘,但是raid信息还在导致可以list获取
                if disk['state'].lower() != "ok":
                    continue
                disks.append(disk)

        # 获取没有配置过raid的盘
        unassigned_lineno = prefix_lineno(out, "unassigned")
        if len(unassigned_lineno) != 0:
            physicaldrive_lineno = prefix_lineno(out, "physicaldrive", unassigned_lineno[0])
            for lineno in physicaldrive_lineno:
                disk = {}
                disk['ctl']        = "%s:%s" % (ctl, out[lineno+1].split(":")[1].strip())
                disk['eid']        = int(out[lineno+2].split(":")[1])
                disk['slot']       = int(out[lineno+3].split(":")[1])
                disk['state']      = out[lineno+4].split(":")[1].strip()
                disk['drive_type'] = out[lineno+6].split(":")[1].count("Solid") == 0 and "HDD" or "SSD"
                disk['protocol']   = out[lineno+6].split(":")[1].count("SATA") == 0  and "SAS" or "STAT"
                disk['size']       = out[lineno+7].split(":")[1].strip()
                disk['model']      = out[lineno+12].split(":")[1].strip()
                disk['pci_addr']   = pci_addr
                disks.append(disk)
        # print json.dumps(disks, indent=4)
        return 0, disks

    def __delete_old_raid(self, addr):
        e, _disks = self.__get_ctl_disk_list(addr[0])
        if e: return e, _disks

        logicaldrive = None
        for _disk in _disks:
            if "%s:%s:%s" % (_disk['ctl'], _disk['eid'], _disk['slot']) == ":".join(addr) and _disk.has_key('logicaldrive'):
                logicaldrive = _disk['logicaldrive']
                break
        if logicaldrive != None:
            command("%s ctrl slot=%s logicaldrive %s delete forced" % (HPSSACLI, addr[0], logicaldrive))
        return

    def make_raid(self, ces_addr):
        addr = ces_addr.split(":")

        self.__delete_old_raid(addr)

        # hpssacli ctrl slot=0 create type=ld drives=1I:3:3 raid=0 forced
        e, out = command("%s ctrl slot=%s create type=ld drives=%s raid=0 forced" % (HPSSACLI, addr[0], ":".join(addr[1:])))
        if e: return e, out

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

    def get_disk_list(self, force=False):
        # 通用机型不获取raid卡信息
        if g.platform['platform'] == "generic":
            return 0, []

        # 获取最后事件序列号
        e, seq_num = self.__get_last_seq_num()
        if e: return e, seq_num
        if seq_num == HPSARaid.LAST_SEQ_NUM and int(time.time()) - HPSARaid.LAST_UPDATE_TIME < MAX_UPDATE_TIME:
            return 0, HPSARaid.CACHE_DISK_LIST

        e, ctls = self.__get_ctl_list()
        if e: return e, ctls
        disk_list = []
        for ctl in ctls:
            e, _disks = self.__get_ctl_disk_list(ctl['index'])
            if e: continue
            disk_list.extend(_disks)

        # 由于每次执行一次hpssacli都会触发seq变更，因此seq的更新需要再重新获取一次
        e, seq_num = self.__get_last_seq_num()
        if e: return e, seq_num
        HPSARaid.LAST_SEQ_NUM     = seq_num
        HPSARaid.LAST_UPDATE_TIME = int(time.time())
        HPSARaid.CACHE_DISK_LIST  = disk_list

        return 0, HPSARaid.CACHE_DISK_LIST

    def led(self, ces_addr, is_on):
        addr = ces_addr.split(":")
        # hpssacli ctrl slot=0 pd 1I:3:4 modify led=off
        return command("%s ctrl slot=%s pd %s modify led=%s" % (HPSSACLI, addr[0], ":".join(addr[1:]), is_on and "on" or "off"))

if __name__ == "__main__":
    # print HPSARaid().get_disk_list()
    print HPSARaid().make_raid("0:2I:3:5")
    # print json.dumps(HPSARaid().get_disk_list(), indent=4)
