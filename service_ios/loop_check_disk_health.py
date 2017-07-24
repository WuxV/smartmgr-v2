# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time
from pdsframe import *
from service_ios import g
from service_ios.base.apismartctl import SmartAPI
from service_ios.base.smartflash import SmartFlashApi

# 健康状态每2小时检查一次
MAX_UPDATE_TIME = 2*3600

class LoopCheckDiskHealthMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME        = 20
    # 最后更新时间
    LAST_UPDATE_TIME = 0

    def INIT(self):
        if g.is_ready == False:
            logger.run.debug("HeartBeatDiskList IOS service is not ready")
            return MS_FINISH

        if int(time.time()) - LoopCheckDiskHealthMachine.LAST_UPDATE_TIME < MAX_UPDATE_TIME:
            return MS_FINISH
        
        self.curr_disk_count = len(g.todo_check_disk)
        if self.curr_disk_count == 0:
            return MS_FINISH

        # 执行健康检查
        for disk in g.todo_check_disk:
            logger.run.info("Start check disk %s health" % disk['dev_name'])
            if disk['drive_type'] == "nvme" or disk['drive_type'] == "df_pcie":
                self.LongWork(self.get_nvme_health, disk, self.Entry_HeartbeatDiskH, 30)
            else:
                self.LongWork(self.get_disk_health, disk, self.Entry_HeartbeatDiskH, 30)
        return MS_CONTINUE

    def get_nvme_health(self,disk):
        flash = SmartFlashApi()
        e, msg =flash.get_flash_info(disk['dev_name'],disk['drive_type'])
        if not e:
            disk["life"]      = msg["life"]
            disk["totallife"] = msg["totallife"]
            disk["health"]    = msg["health"]
            if msg.has_key("media_status"):
                disk["media_status"] = msg["media_status"]
        else:
           disk["life"]      = -1
           disk["totallife"] = -1
        return (0,disk)

    def get_disk_health(self, disk):
        smartdisk      = SmartAPI()
        disk_did       = disk['did']
        disk_raid_type = disk['raid_type'] 

        if disk_did != None and disk_raid_type != None:
            e,msg,health = smartdisk.get_disk_smartinfo(disk['dev_name'],did=disk_did,raidtype=disk_raid_type)
        else:
            e,msg,health = smartdisk.get_disk_smartinfo(disk['dev_name'])
        if not e:
            for k in msg.keys():
                disk[k] = msg[k]
            disk['health'] = str(health)
        else:
            logger.run.error("Get disk health failed %s" %msg)
        return (0, disk)

    def Entry_HeartbeatDiskH(self, result):
        _, disk = result

        logger.run.info("Stop disk health : %s" % disk['dev_name'])
        g.cache_disk_list_healthy[disk['dev_name']] = {}
        g.cache_disk_list_healthy[disk['dev_name']]['disk']   = disk
        g.cache_disk_list_healthy[disk['dev_name']]['c_time'] = int(time.time())
        self.curr_disk_count -= 1
        if self.curr_disk_count == 0:
            logger.run.info("Get disk health end")
            LoopCheckDiskHealthMachine.LAST_UPDATE_TIME = int(time.time())
            return MS_FINISH
        return MS_CONTINUE
