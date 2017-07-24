#!/usr/bin/env python
# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Python built-ins
'''
Created on 2016年5月23日

@author: qing_wang
'''
import string
import ctypes
import json
import os
import re  
import platform
from subprocess import Popen, PIPE
from service_ios.base.common import SSD_LIFE_MAX
from pdsframe import *

type_tools ={
        "intel":"/usr/bin/isdct",
        "micron":"/opt/smartmgr/scripts/msecli",
        "huawei":"/opt/smartmgr/scripts/hioadm"
}
SHANNON_STATUS = "/usr/bin/shannon-status"

class SmartFlashApi:
    def __init__(self):
        pass

    def docmd(self,args, log = True):
        return command(" ".join(args))

    def check_tool(self,tool):
        if not os.path.exists(tool):
            return 1,"not find tool in %s" % tool
        return 0,""

    #当有其他类型的flash卡时增加脚本，但方法名相同(现在flash卡有df类型的pcie保存卡，nvme盘有intel和micron两种)
    def get_flash_info(self,device_path=None,drive_type=None):
        if not device_path:
            return 1,"not give device path parameters"

        if drive_type == "df_pcie":
            e,info = self.get_baocun_sensor_info(device_path)
            if e:
                return 1,info
            return 0,info
        else:
            flashtype ,index, device_status = self.get_flash_index_id(device_path)
            if not flashtype:
                return 1,index
            e, info = self.get_flash_sensor_info(index_id=index,flashtype=flashtype)
            if e:
                return 1,info
            if flashtype == "intel":
                if device_status == "Healthy":
                    info["health"] = "PASS"
                else:
                    info["health"] = "WARN"
            return 0,info

    def get_flash_index_id(self,device_path=None):
        if not device_path:
            return 1,"not give device path parameters ",""
        for k in type_tools.keys():
            if self.check_tool(type_tools[k]):
                func_name = "get_" + k + "_index_id"
                obj = getattr(self,func_name)
                if not obj:
                    logger.run.debug("Not find function %s" % func_name)
                    continue
                e,index,device_status = obj(type_tools[k],device_path)
                if e:
                    continue
                return (k,index,device_status)
                
        return (None,"Not find flash index id with %s" % device_path,"")


    def get_flash_sensor_info(self,index_id,flashtype=None):
        if not flashtype:
            return 1,"flashtype is None"

        func_name = "get_" + flashtype + "_sensor_info"

        obj = getattr(self,func_name)
        if not obj:
            return 1,"Not find function %s" % func_name

        tool = type_tools[flashtype]

        e, info = obj(tool,index_id)
        if e:
            return 1,info

        return 0, info
        
    # 分类型接口,获取华为nvme盘信息
    def get_huawei_index_id(self,tool,device_path):
        # hioadm info
        #cmd = tool + " info"
        e,msgs = self.docmd([tool, ' info'], log=True)
        if e:
            return 1,"",""
        found = False
        device_name = None
        for i in msgs.strip().splitlines():
            result1 = re.search(r'\|-+\s(\w+)\s.*', i)
            result2 = re.search(r'\s+\|-+\s(\w+)\s.*', i)
            if result1:
                device_name = result1.group(1)
            if result2 and device_path.endswith(result2.group(1)):
                found = True
                break
                
        if not found:
            return 1,"not find disk device name",""
        else:
            return 0,device_name,""

    def get_huawei_sensor_info(self,tool,device_name):
        # hioadm info -d device_name
        #cmd = tool + " info -d " + device_name
        e, info = self.docmd([tool, ' info -d ' ,str(device_name)], log=True)
        if e:
            return 1,""

        device_status  = None
        for i in info.strip().splitlines():
            if i.startswith("device status"):
                device_status = i.split(':')[1].strip()

        # hioadm info -d device_name -s
        #cmd = tool + " info -d " + device_name + ' -s'
        e, info = self.docmd([tool, ' info -d ' ,str(device_name), ' -s'], log=True)
        if e:
            return 1,""
        power_on_hours = None
        ssd_life_left  = None
        found = 0
        for i in info.strip().splitlines():
            if i.startswith("percentage used"):
                ssd_life_left  = int(100-int(i.split(':')[1].strip().rstrip(' %')))
            if i.startswith("power on hours"):
                power_on_hours = int(i.split(':')[1].strip().rstrip(' h'))
            if ssd_life_left and power_on_hours:
                found = found + 1
                
        if found < 1:
            logger.run.error("not find percentage used or power on hours")
            return 1,None
        res,ret = self.get_disk_life(power_on_hours,ssd_life_left)
        if res:
            return 1,ret

        if device_status == None:
            ret["health"] = "--"
        elif device_status != None and device_status == "healthy":
            ret["health"] = "PASS"
        else:
            ret["health"] = "WARN"
        return 0,ret

    # 分类型接口,获取美光盘信息
    def get_micron_index_id(self,tool,device_path):
        #msecli -L 
        #cmd = tool +" -L"
        e,msgs = self.docmd([tool, ' -L'], log=True)
        if e:
            return 1,"",""
        disk_list = []
        for i in msgs.strip().split('\n\n'):
            if i.startswith("Device Name"):
                disk = {}
                for j in i.splitlines():
                    item = j.split(':')
                    if len(item) == 2:
                        disk[item[0].strip()] = item[1].strip()
                disk_list.append(disk)        
        device_name = None
        for disk in disk_list:
            if disk.has_key("OS Device") and disk["OS Device"] == device_path:
                device_name = disk["Device Name"]
        if device_name == None:
            return 1,"not find disk device name",""
        else:
            return 0,device_name,""

    def get_micron_sensor_info(self,tool,device_name):
        #msecli -L -n device_name
        #cmd = tool + " -L -n device_name -J"
        e, info = self.docmd([tool, '-L -n' ,str(device_name), '-J' ], log=True)
        if e:
            return 1,""

        find_json = re.match(r'(.*)Device Name(.*)',info,re.S)
        info = json.loads(find_json.group(1))
        device_status  = None
        power_on_hours = None
        ssd_life_left  = None
        found = 0
        if isinstance(info,dict):
            for i in info["drives"]:
                if "deviceStatus" in i.keys():
                    device_status = i["deviceStatus"]
                if "smartData" in i.keys():
                    for j in i["smartData"]:
                        if "powerOnHours" in j.keys() and "percentLifeUsed" in j.keys():
                            power_on_hours = int(j["powerOnHours"])
                            ssd_life_left  = int(100-int(j["percentLifeUsed"]))
                            found = found + 1
        else:
            return 1,None

        if found < 1:
            logger.run.error("not find PowerOnHours or PercentageUsed")
            return 1,None
        res,ret = self.get_disk_life(power_on_hours,ssd_life_left)
        if res:
            return 1,ret

        if device_status == None:
            ret["health"] = "--"
        elif device_status != None and device_status == "Drive is in good health":
            ret["health"] = "PASS"
        else:
            ret["health"] = "WARN"
        return 0,ret

    # 分类型接口,获取intel信息
    def get_intel_index_id(self,tool,device_path):
        #isdct show -o json -intelssd
        #cmd = tool +" show -o json -intelssd"
        e,msgs = self.docmd([tool, ' show -o json -intelssd'], log=True)
        if e:
            return 1,"",""
        decoded_msgs = json.loads(msgs)
        for  msg in decoded_msgs.keys():
            #print decoded_msgs[msg].keys()
            if "DevicePath" in decoded_msgs[msg].keys() and "Index" in decoded_msgs[msg].keys() and "DeviceStatus" in decoded_msgs[msg].keys():
                if decoded_msgs[msg]["DevicePath"] == device_path:
                    return (0,decoded_msgs[msg]["Index"],str(decoded_msgs[msg]["DeviceStatus"]))

        return 1,"not find index for %s"%device_path,""

    def get_intel_sensor_info(self,tool,index_id):
        #isdct show -a -o json -intelssd 0  -sensor
        #cmd = tool + " show -a -o json -intelssd " + str(index_id) + " -sensor"
        e, info = self.docmd([tool, 'show -a -o json -intelssd', str(index_id), '-sensor'], log=True)
        if e:
            return 1,""

        decoded_info = json.loads(info)
        found = 0
        for k in decoded_info.keys():
            #print decoded_info[k].keys()
            if "PowerOnHours" in  decoded_info[k].keys() and "PercentageUsed" in  decoded_info[k].keys():
                power_on_hours = int(decoded_info[k]["PowerOnHours"],16)
                ssd_life_left = int(100-decoded_info[k]["PercentageUsed"])
                found=found+1
        if found < 1:
            logger.run.error("not find PowerOnHours or PercentageUsed")
            return 1,None

        res,ret = self.get_disk_life(power_on_hours,ssd_life_left)
        if res:
            return 1,ret
        #print ret
        return 0,ret

    def get_baocun_sensor_info(self,device_name=None):
        # /usr/bin/shannon-status  -p -a   
        e, info = self.docmd([SHANNON_STATUS, ' -p -a'], log=True)
        if e:
            return 1,info
        disk_list = []
        for i in info.strip().split('\n\n'):
            if i.startswith("control_device_node"):
                disk = {}
                for j in i.splitlines():
                    item = j.split('=')
                    if len(item) == 2:
                        disk[item[0].strip()] = item[1].strip()
                disk_list.append(disk)        
        found = False
        for disk in disk_list:
            if disk.has_key("block_device_node") and disk["block_device_node"] == device_name:
                found = True
                if disk.has_key("estimated_life_left"):
                    ssd_life_left = float(disk["estimated_life_left"].strip()[:-1])
                if disk.has_key("power_on_time"):
                    power_on_hours = int(disk["power_on_time"].strip().split()[0])
                if disk.has_key("media_status"):
                    health = disk["media_status"]
        if found == False:
            return 1,"not found %s"%device_name
        res,ret = self.get_disk_life(power_on_hours,ssd_life_left)
        if res:
            return 1,ret
        if health == "Healthy":
            ret["health"] = "PASS"
        else:
            ret["health"] = "WARN"
        ret["media_status"] = health
        return 0,ret

    def get_disk_life(self,power_on_hours=None,ssd_life_left=None):
        if power_on_hours == None or ssd_life_left == None:
            return 1,"missing parameter power_on_hours or ssd_life_left"
        ret = {}
        if ssd_life_left==100:
            if SSD_LIFE_MAX != "MAX":
                ret["life"] =  str(int(SSD_LIFE_MAX)*365*24)
                ret["totallife"] = str(int(SSD_LIFE_MAX)*365*24)
            else:
                ret["life"] =  SSD_LIFE_MAX
                ret["totallife"] =  SSD_LIFE_MAX
        else:
            lifehours = power_on_hours/(100-ssd_life_left)*100 - power_on_hours
            if SSD_LIFE_MAX != "MAX"  and lifehours > int(SSD_LIFE_MAX)*365*24:
                ret["life"] =  str(int(SSD_LIFE_MAX)*365*24)
                ret["totallife"] = str(int(SSD_LIFE_MAX)*365*24)
            else:
                ret["life"] =  str(lifehours)
                ret["totallife"] = str(power_on_hours/(100-ssd_life_left))
        return 0,ret

