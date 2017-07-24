# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import time, os, pyudev, json
from pdsframe import *
from pdsframe.common.long_work import command
from service_ios import g
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
from service_ios.base.common import get_os_version
from service_ios.base.apismartscsi import APISmartScsi

e, s = get_os_version()
if e:
    DMSETUP = "dmsetup"    
else:
    if s == "systemv6":
        DMSETUP = "/sbin/dmsetup"
    else:
        DMSETUP = "/usr/sbin/dmsetup"

# 最长等待清除周期
MAX_CLEAN_TIME = 60

class LoopCheckUdevMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 10
    TODO_CLEAN_MP = {}
    TODO_CLEAN_AD = {}

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH

        if g.platform['sys_mode'] == "storage":
            return MS_FINISH

        if config.safe_get('model-config', 'auto-check-udev').lower() != "true":
            return MS_FINISH

        try:
            self.CheckUdev()
        except Exception as e:
            logger.run.error("Check udev error:%s" % e)
        return MS_FINISH

    def CheckUdev(self):
        context = pyudev.Context()

        e, out = command("%s table --target=multipath" % DMSETUP)
        if e:
            logger.run.error("get multipath failed:%s" % out)
            return MS_FINISH

        # 获取当前认到的所有mp列表
        mp_list = {}
        for line in out.splitlines():
            items = line.split()
            mp_name = items[0].split(":")[0]
            try:
                d  = pyudev.Devices.from_device_file(context, '/dev/mapper/%s' % mp_name)
                mp_list[mp_name] = {}
                mp_list[mp_name]['mm'] = "%s:%s" % (os.major(d.device_number), os.minor(d.device_number)) 
                mp_list[mp_name]['nr_path'] = 0
                if len(items) >= 11:
                    mp_list[mp_name]['nr_path'] = int(items[10])
            except:
                pass

        # 获取当前认到的所有asmdisk列表
        lun_list = APISmartScsi().get_lun_list()
        lun_mms  = []
        for lun_detail_info in lun_list.values():
            lun_info = lun_detail_info['attrs']
            lun_d    = pyudev.Devices.from_device_file(context, lun_info['filename'])
            lun_mms.append("%s:%s" % (os.major(lun_d.device_number), os.minor(lun_d.device_number)))

        ad_list = {}
        if os.path.exists('/dev/asmdisks'):
            asmdisks = os.listdir('/dev/asmdisks')
            for ad_name in asmdisks:
                try:
                    asm_d  = pyudev.Devices.from_device_file(context, '/dev/asmdisks/%s' % ad_name)
                    asm_mm = "%s:%s" % (os.major(asm_d.device_number), os.minor(asm_d.device_number)) 
                    # 过滤掉本地smartscsi映射的磁盘
                    if asm_mm in lun_mms:
                        continue
                    ad_list[ad_name] = {}
                    ad_list[ad_name]['mm'] = asm_mm
                except pyudev.DeviceNotFoundByNumberError as e:
                    if str(e).startswith("No block device with number"):
                        logger.run.info("Rm no block device:%s" % ad_name)
                        os.remove(os.path.join("/dev/asmdisks", ad_name))
                except Exception as e:
                    pass

        # 删掉失效mp, 或者已经有路径的mp
        for mp_name in LoopCheckUdevMachine.TODO_CLEAN_MP.keys():
            if mp_name not in mp_list.keys() or mp_list[mp_name]['nr_path'] != 0:
                LoopCheckUdevMachine.TODO_CLEAN_MP.pop(mp_name)

        # 删掉失效ad, 或者已经有对应mp的ad
        for ad_name, ad_info in LoopCheckUdevMachine.TODO_CLEAN_AD.items():
            if ad_name not in ad_list.keys() or ad_info['info']['mm'] in [mp_info['mm'] for mp_info in mp_list.values()]:
                LoopCheckUdevMachine.TODO_CLEAN_AD.pop(ad_name)

        # 获取需要清除的mp
        todo_clean_mp = []
        for mp_name, mp_info in mp_list.items():
            if mp_info['nr_path'] > 0:
                continue
            if mp_name not in LoopCheckUdevMachine.TODO_CLEAN_MP.keys():
                LoopCheckUdevMachine.TODO_CLEAN_MP[mp_name] = {}
                LoopCheckUdevMachine.TODO_CLEAN_MP[mp_name]['time'] = int(time.time())
                LoopCheckUdevMachine.TODO_CLEAN_MP[mp_name]['info'] = mp_info
            if int(time.time()) - LoopCheckUdevMachine.TODO_CLEAN_MP[mp_name]['time'] > MAX_CLEAN_TIME:
                todo_clean_mp.append(mp_name)

        # 获取需要清除的ad
        todo_clean_ad = []
        for ad_name, ad_info in ad_list.items():
            if ad_info['mm'] in [mp_info['mm'] for mp_info in mp_list.values()]:
                continue
            if ad_name not in LoopCheckUdevMachine.TODO_CLEAN_AD.keys():
                LoopCheckUdevMachine.TODO_CLEAN_AD[ad_name] = {}
                LoopCheckUdevMachine.TODO_CLEAN_AD[ad_name]['time'] = int(time.time())
                LoopCheckUdevMachine.TODO_CLEAN_AD[ad_name]['info'] = ad_info
            if int(time.time()) - LoopCheckUdevMachine.TODO_CLEAN_AD[ad_name]['time'] > MAX_CLEAN_TIME:
                todo_clean_ad.append(ad_name)

        for mp in todo_clean_mp:
            logger.run.info("Start auto dmsetup remove %s" % mp)
            e, out = command("%s remove %s" % (DMSETUP,mp))
            if e: logger.run.error("dmsetup remove failed:%s" % out)

        for ad in todo_clean_ad:
            logger.run.info("Start auto rm asmdisk %s" % ad)
            try:
                os.remove(os.path.join("/dev/asmdisks", ad))
            except Exception as e:
                if e: logger.run.error("remove asmdisk failed:%s" % e)

        return MS_FINISH
