# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
import time
from pdsframe import *
from service_ios import g
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds

LSPCI = "/usr/sbin/lspci"
DMIDECODE = "/usr/sbin/dmidecode"
SHANNON_STATUS = "/usr/bin/shannon-status"
MSECLI = "/opt/smartmgr/scripts/msecli"
HUAWEI = "/opt/smartmgr/scripts/hioadm"

class HeartBeatDiskListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        if g.is_ready == False:
            logger.run.debug("HeartBeatSlotList IOS service is not ready")
            return MS_FINISH

        self.mds_request = MakeRequest(msg_mds.HEARTBEAT_SLOT_LIST_REQUEST)

        # 获取槽位列表比较耗时, 需要放到线程操作
        self.LongWork(self.get_slot_list, {}, self.Entry_GetSlotList)
        return MS_CONTINUE

    def get_slot_list(self, params={}):
        rc = msg_pds.ResponseCode()

        # 获取槽位、bus address列表
        ret, slot_address = self.get_slot_address()
        if ret:
            rc.retcode = msg_ios.RC_IOS_GET_SLOT_LIST_FAILED
            rc.message = "Get slot list failed: %s" % slot_address
            return rc, None

        # 分别获取宝存卡、镁光ssd设备名、raid卡、华为nvme和对应的bus address
        ret1, address_device_shannon = self.get_shannon_address_device()
        ret2, address_device_micron = self.get_micron_address_device()
        ret3, address_device_raid = self.get_raid_address_device()
        ret4, address_device_huawei = self.get_huawei_address_device()

        slot_list = []
        for slot, address in slot_address.items():
            slot_info = msg_pds.SlotInfo()
            slot_info.slot_id = slot
            slot_info.bus_address = address
            if not ret1 and address in address_device_shannon:
                slot_info.dev_name = address_device_shannon[address]
            if not ret2 and address in address_device_micron:
                slot_info.dev_name = address_device_micron[address]
            if not ret3 and address in address_device_raid:
                slot_info.dev_name = address_device_raid[address]
            if not ret4 and address in address_device_huawei:
                slot_info.dev_name = address_device_huawei[address]

            slot_list.append(slot_info)

        return rc, slot_list

    def Entry_GetSlotList(self, result):
        rc, slot_list = result
        if rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("Get slot list failed %s:%s" % (rc.retcode, rc.message))
            return MS_FINISH

        for slot_info in slot_list:
            self.mds_request.body.Extensions[msg_mds.heartbeat_slot_list_request].slot_infos.add().CopyFrom(slot_info)

        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, self.mds_request, self.Entry_HeartBeatSlotList)
        return MS_CONTINUE

    
    # 支持主板类型: S2600CW S2600CWR S2600WT2R S2600WTT 'Topdata Blood G2' 0WCJNT
    def get_slot_address(self):
        cmd_str = "%s -t slot|grep -E 'Bus|Designation'" % DMIDECODE
        e, out = command(cmd_str)
        if e:
            return (e, out)

        slot_list = []
        slot_address = {}
        txt = out.splitlines()
        for line in txt:
            result = re.search(r'\s*Designation:\s\w+\s-\sPCIe\sSlot\s(\d)$', line)
            if result:
                slot_list.append(result.group(1))
                continue

            result = re.search(r'\s*Designation:\s\w+\s-\sRiser\s(\d+),\sslot\s(\d)$', line)
            if result:
                slot_list.append(result.group(1)+'-'+result.group(2))
                continue

            result = re.search(r'\s*Designation:\sPCIE(\d+)$', line)
            if result:
                slot_list.append(result.group(1))
                continue

            result = re.search(r'\s*Designation:\sPCIe\sSlot\s(\d)$', line)
            if result:
                slot_list.append(result.group(1))
                continue

            if not slot_list:
                return (-1, "Not support the machine board type")

            if line.strip().split(':')[0] == "Bus Address":
                slot_address[slot_list[-1]] = line.split(':', 1)[1].strip()
    
        for slot_id in slot_list:
            if slot_id not in slot_address:
                slot_address[slot_id] = ''
        return (0, slot_address)

    # 获取宝存卡
    def get_shannon_address_device(self):
        cmd_str = "%s -a" % SHANNON_STATUS
        e, out = command(cmd_str)
        if e:
            return (e, out)

        device_list = []
        address_list = []
        if out:
            txt = out.splitlines()
            for line in txt:
                if line.split(':')[0] == "Block Device Node":
                    device_list.append(line.split(':')[1].strip())
                    continue
                if line.split(':')[0] == "PCI Bus Address":
                    ces = line.split(':',1)[1].strip().split(':')
                    content = "\[%s\]----%s\.%s" % (ces[0],ces[1],ces[2])
                    cmd_str = "%s -tvv |grep '%s'" % (LSPCI, content)
                    e, out = command(cmd_str)
                    if e:
                        return (e, out)
                    try:
                        result = re.search(r'\s\+\-\[(\d+:\d+)\]\-\+\-(\w+\.\d+)', out)
                        address_list.append(result.group(1) + ':' + result.group(2))
                    except:
                        result = re.search(r'\s*\+\-\d+.\d+\-\[(\d+)\]\-+(\w+\.\d+)', out)
                        address_list.append('0000:' + result.group(1) + ':' + result.group(2))

        address_device = dict(zip(address_list, device_list))        
        return (0, address_device)

    # 获取镁光ssd
    def get_micron_address_device(self):
        cmd_str = "%s -L" % MSECLI
        e, out = command(cmd_str)
        if e:
            return (e, out)

        device_list = []
        address_list = []
        if out:
            txt = out.splitlines()
            for line in txt:
                if line.split(':')[0].strip() == "OS Device":
                    device_list.append(line.split(':')[1].strip())
                    continue
                if line.split(' :')[0].strip() == "PCI Path (B:D.F)":
                    address_list.append('0000:' + line.split(' :')[1].strip())

        address_device = dict(zip(address_list, device_list))        
        return (0, address_device)

    # 获取raid卡
    def get_raid_address_device(self):
        cmd_str = "%s -m |grep -i raid" % LSPCI
        e, out = command(cmd_str)
        if e:
            return (e, out)

        address_device = {}
        txt = out.splitlines()
        for line in txt:
            pci_addr = line.split(' "')[0]
            device = line.split(' "')[-1].rstrip('"')
            
            ces = re.split(':|\.', pci_addr)
            content = "\[%s\]----%s\.%s" % (ces[0],ces[1],ces[2])
            cmd_str = "%s -t|grep -E '0000|%s' |grep '%s' -B1" % (LSPCI, content, content)
            e, out = command(cmd_str)
            if e:
                return (e, out)
            try:
                result1 = re.search(r'\s.\-\[(\w+:\w+)\].*', out.split('\n')[0])
                result2 = re.search(r'\s.\s+\+\-(\w+\.\w+).*', out.split('\n')[1])
                bus_address = result1.group(1) + ':' + result2.group(1)
            except:
                bus_address =  ""
            address_device[bus_address] = device

        return (0, address_device)

    # 获取华为nvme
    def get_huawei_address_device(self):
        cmd_str = "%s info" % HUAWEI
        e, out = command(cmd_str)
        if e:
            return (e, out)

        l = []
        txt = out.splitlines()
        for line in txt:
            result = re.search(r'\s+\|-+\s(\w+)\s.*', line)
            if result:
                l.append(result.group(1))

        device_list = []
        pci_list = []
        # 通过镁光工具获取华为nvme pci地址
        for device_name in l:
            cmd_str = "%s -L -a |grep '%s' -B2" % (MSECLI, device_name)
            e, out = command(cmd_str)
            if e:
                return (e, out)

            txt = out.splitlines()
            for line in txt:
                if line.startswith('PCI Path'):
                    pci_list.append(line.split(' :')[1].strip())
                if line.startswith('OS Device'):
                    device_list.append(line.split(':')[1].strip())

        # 通过lspci转换为bus address
        address_list = []
        for pci_addr in pci_list:
            ces = re.split(':|\.', pci_addr)
            content = "\[%s-?\w*\]----%s\.%s" % (ces[0],ces[1],ces[2])
            cmd_str = "%s -t|grep -E '0000|%s' |grep -E '%s' -B1" % (LSPCI, content, content)
            e, out = command(cmd_str)
            if e:
                return (e, out)
            try:
                result1 = re.search(r'\s.\-\[(\w+:\w+)\].*', out.split('\n')[0])
                result2 = re.search(r'\s.\s+\+\-(\w+\.\w+).*', out.split('\n')[1])
                bus_address = result1.group(1) + ':' + result2.group(1)
            except:
                bus_address =  ""
            address_list.append(bus_address)

        address_device = dict(zip(address_list, device_list))        
        return (0, address_device)


    def Entry_HeartBeatSlotList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error("%d %s" % (response.rc.retcode, response.rc.message))
        return MS_FINISH
