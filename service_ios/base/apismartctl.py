#!/usr/bin/env python
# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
'''
Created on 2016年5月23日

@author: qing_wang
'''

# Python built-ins
import ctypes
import os
import platform
import warnings
import re  # Don't delete this 'un-used' import
from service_ios.base.common import SSD_LIFE_MAX
from common import logger

from smartctl import Device

class SmartAPI:

    def __init__(self):
        self.smartdsk = None
        self.raidtype = ["megaraid","cciss"]
        pass

    def get_disk_smarthealth(self,path,did=None,raidtype=None):
        #FIXME:当做不是直通卡时需要传入device id/DID
        #FIXME:现在支持storcli64和hpssacli可读的raid卡
        if did !=None and raidtype:
            if raidtype not in self.raidtype:
                return (1,"raidtype[%s] not in [%s]" % (raidtype,self.raidtype))
            self.smartdsk = Device(path,did=did,raidtype=raidtype)#/dev/sda
        else:
            self.smartdsk = Device(path)#/dev/sda

        return 0,str(self.smartdsk.assessment)

    
    def get_disk_smartinfo(self,path,did=None,raidtype=None):
        #FIXME:当做不是直通卡时需要传入device id/DID
        #FIXME:现在支持storcli64和hpssacli可读的raid卡
        if did !=None and raidtype:
            if raidtype not in self.raidtype:
                return (1,"raidtype[%s] not in [%s]" % (raidtype,self.raidtype))
            self.smartdsk = Device(path,did=did,raidtype=raidtype)#/dev/sda
        else:
            self.smartdsk = Device(path)#/dev/sda
        logger.run.debug("[%s]disk_model:%s" % (path,self.smartdsk.model))
        logger.run.debug("[%s]device_in_database:%s" % (path,self.smartdsk.device_in_database)) 
        logger.run.debug("[%s]interface:%s" % (path,self.smartdsk.interface))

        health = self.smartdsk.assessment                

        if not self.smartdsk.device_in_database:
            e,msg = self.get_attr_not_in_database()
            if e:
                return (1,msg,health)
            msg['serial2'] = self.smartdsk.serial
            return (0,msg,health)
        else:
            e,msg = self.get_attr_in_database()
            if e:
                return (1,msg,health)
            msg['serial2'] = self.smartdsk.serial
            return (0,msg,health)

    def get_attr_with_scsi(self):
        #print "=++++++++++interface is scsi+++++++++++=="
        #print self.smartdsk.diags
        return 0,self.smartdsk.diags


    def get_attr_in_database(self):
        # print "=++++++++++in database+++++++++++=="
        msgs = self.smartdsk.all_attributes()
        if msgs is None:
            if self.smartdsk.interface == "scsi" and self.smartdsk.diags is not None:
                e,msg = self.get_attr_with_scsi()
                if e:
                    return 1,msg
                return 0,msg

        ret = {}
        for k in msgs:
            #print k["num"],k["name"],k["value"],k["worst"],k["thresh"],k["raw"]
            #FIXME:每个ID的坏盘判断方法不一定相同
            #底层数据读取错误率/Raw_Read_Error_Rate
            if k["num"] == "1":
                if int(k["value"]) == int(k["worst"]):
                    ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"

            #重定位磁区计数/Reallocated Sector Count
            if k["num"] == "5":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"

            #硬盘加电时间/Power_On_Hours_and_Msec
            if k["num"] == "9":
                ret[k["name"]] = str(k["raw"])

            #电机起转重试/Spin Retry Count
            if k["num"] == "10":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"
            #通信超时/Command Timeout
            if k["num"] == "188":
                if int(k["value"]) > 0:
                    ret[k["name"]] = "Dangerous"

            #温度/Temperature_Celsius
            if k["num"] == "194":
                ret[k["name"]] = k["raw"]

            #重定位事件计数/Reallocated_Event_Count
            if k["num"] == "196":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"


            #无法校正的扇区计数/Uncorrectable_Sector_Ct
            if k["num"] == "198":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"


            #ssd剩余寿命/SSD_Life_Left
            if k["num"] == "231" and k["name"] == "SSD_Life_Left":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"

                if ret[k["name"]] != "Healthy":
                
                    ssd_life_left = int(k["value"])
                    if "Power_On_Hours_and_Msec" in ret.keys():
                        if "h" in ret['Power_On_Hours_and_Msec']:
                            v = ret['Power_On_Hours_and_Msec'].split("h")
                            #print v[0]
                            power_on_hours = int(v[0])
                        else:
                            power_on_hours = int(ret['Power_On_Hours_and_Msec'])
                    else:
                        power_on_hours = 0

                    lifehours = power_on_hours/(100-ssd_life_left)*100 - power_on_hours
                    if SSD_LIFE_MAX != "MAX"  and lifehours > int(SSD_LIFE_MAX)*365*24:
                        ret["Life"] =  str(int(SSD_LIFE_MAX)*365*24)
                        ret["TotalLife"] = str(int(SSD_LIFE_MAX)*365*24)
                    else:
                        ret["Life"] =  str(lifehours)
                        ret["TotalLife"] = str(power_on_hours/(100-ssd_life_left))
                else:
                    if SSD_LIFE_MAX != "MAX":
                        ret["Life"] =  str(int(SSD_LIFE_MAX)*365*24)
                        ret["TotalLife"] = str(int(SSD_LIFE_MAX)*365*24)
                    else:
                        ret["Life"] =  SSD_LIFE_MAX
                        ret["TotalLife"] =  SSD_LIFE_MAX

            #介质耗损指标/Media Wearout Indicator
            elif k["num"] == "233" and k["name"] == "Media_Wearout_Indicator":
                if int(k["value"]) == int(k["worst"]):
                     ret[k["name"]] = "Healthy"
                if int(k["value"]) - int(k["thresh"]) >5:
                    ret[k["name"]] = "Healthy"
                if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                    ret[k["name"]] = "Dangerous"
                if  int(k["value"]) <= int(k["thresh"]):
                    ret[k["name"]] = "Bad"

                if ret[k["name"]] != "Healthy":
                
                    ssd_life_left = int(k["value"])
                    if "Power_On_Hours" in ret.keys():
                        if "h" in ret['Power_On_Hours']:
                            v = ret['Power_On_Hours'].split("h")
                            #print v[0]
                            power_on_hours = int(v[0])
                        else:
                            power_on_hours = int(ret['Power_On_Hours'])
                    else:
                        power_on_hours = 0

                    lifehours = power_on_hours/(100-ssd_life_left)*100 - power_on_hours
                    if SSD_LIFE_MAX != "MAX"  and lifehours > int(SSD_LIFE_MAX)*365*24:
                        ret["Life"] =  str(int(SSD_LIFE_MAX)*365*24)
                        ret["TotalLife"] = str(int(SSD_LIFE_MAX)*365*24)
                    else:
                        ret["Life"] =  str(lifehours)
                        ret["TotalLife"] = str(power_on_hours/(100-ssd_life_left))
                else:
                    if SSD_LIFE_MAX != "MAX":
                        ret["Life"] =  str(int(SSD_LIFE_MAX)*365*24)
                        ret["TotalLife"] = str(int(SSD_LIFE_MAX)*365*24)
                    else:
                        ret["Life"] =  SSD_LIFE_MAX
                        ret["TotalLife"] =  SSD_LIFE_MAX

        # print ret.keys()
        return 0,ret

    def get_attr_not_in_database(self):
        msgs = self.smartdsk.all_attributes()
        if msgs is None:
            if self.smartdsk.interface == "scsi" and self.smartdsk.diags is not None:
                e,msg = self.get_attr_with_scsi()
                if e:
                    return 1,msg
                return 0,msg

        for k in msgs:
            #print k["num"],k["name"],k["value"]
            ret = {}
            for k in msgs:
                #print k["num"],k["name"],k["value"],k["worst"],k["thresh"],k["raw"]
                #FIXME:每个ID的坏盘判断方法不一定相同
                #底层数据读取错误率/Raw_Read_Error_Rate
                if k["num"] == "1":
                    if int(k["value"]) == int(k["worst"]):
                        ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"

                #重定位磁区计数/Reallocated Sector Count
                if k["num"] == "5":
                    if int(k["value"]) == int(k["worst"]):
                         ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"

                #硬盘加电时间/Power_On_Hours_and_Msec/Power_On_Hours
                if k["num"] == "9":
                    ret[k["name"]] = str(k["raw"])

                #电机起转重试/Spin Retry Count
                if k["num"] == "10":
                    if int(k["value"]) == int(k["worst"]):
                         ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"
                #通信超时/Command Timeout
                if k["num"] == "188":
                    if int(k["value"]) > 0:
                        ret[k["name"]] = "Dangerous"

                #温度/Temperature_Celsius
                if k["num"] == "194":
                    ret[k["name"]] = k["raw"]

                #重定位事件计数/Reallocated_Event_Count
                if k["num"] == "196":
                    if int(k["value"]) == int(k["worst"]):
                         ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"


                #无法校正的扇区计数/Uncorrectable_Sector_Ct
                if k["num"] == "198":
                    if int(k["value"]) == int(k["worst"]):
                         ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"


                #ssd剩余寿命/SSD_Life_Left
                if k["num"] == "231" and k["name"] == "SSD_Life_Left":
                    if int(k["value"]) == int(k["worst"]):
                         ret[k["name"]] = "Healthy"
                    if int(k["value"]) - int(k["thresh"]) >5:
                        ret[k["name"]] = "Healthy"
                    if 0 < int(k["value"]) - int(k["thresh"]) <=5:
                        ret[k["name"]] = "Dangerous"
                    if  int(k["value"]) <= int(k["thresh"]):
                        ret[k["name"]] = "Bad"

                #介质耗损指标/Media Wearout Indicator
                if k["num"] == "233" and k["name"] == "Media_Wearout_Indicator":
                    ret["Life"] =  "-"
                    ret["TotalLife"] =  "-"
        #print ret
        return 0,ret
        pass
        
    def get_kingston_attr_not_in_database(self):
        ret={}
        msgs = self.smartdsk.all_attributes()
        # print msgs
        # print "----------"
        found=0
        for  msg in msgs:
            #print msg
            if msg.keys()[0] == "Media_Wearout_Indicator":
                ssd_life_left = int(msg["Media_Wearout_Indicator"][0])
                found=found+1

            if msg.keys()[0] == "Power_On_Hours":
                if "h" in msg['Power_On_Hours'][1]:
                    v = msg['Power_On_Hours'][1].split("h")
                    #print v[0]
                    power_on_hours = int(v[0])
                else:
                    power_on_hours = int(msg['Power_On_Hours'][1])
                
                found=found+1

        if found < 1:
            return (1,"not find Media_Wearout_Indicator or Power_On_Hours")

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
        return (0,ret)

    
    def get_kingston_attr_in_database(self):
        ret={}
        msgs = self.smartdsk.all_attributes()
        # print msgs
        # print "----------"
        found=0
        for  msg in msgs:
            if msg.keys()[0] == "SSD_Life_Left":
                ssd_life_left = int(msg["SSD_Life_Left"][0])
                found=found+1

            if msg.keys()[0] == "Power_On_Hours_and_Msec":
                if "h" in msg['Power_On_Hours_and_Msec'][1]:
                    v = msg['Power_On_Hours_and_Msec'][1].split("h")
                    #print v[0]
                    power_on_hours = int(v[0])
                else:
                    power_on_hours = int(msg['Power_On_Hours_and_Msec'][1])
                
                found=found+1

        if found < 1:
            return (1,"not find SSD_Life_Left or Power_On_Hours_and_Msec")

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
        return (0,ret)



if __name__=='__main__':
    print "----------------------------"
    sda = Device('/dev/sdl')
    #sda = Device('/dev/sdh')
    print "----------------------------"
    sda
    print "---device_in_database----------------------"
    print sda.device_in_database
    print "-----is_ssd-----------------------"
    print sda.is_ssd
    print "------model----------------------"
    print sda.model
    print "------assessment----------------------"
    print sda.assessment
    print "------name----------------------"
    print sda.name
    print "------supports_smart----------------------"
    print sda.supports_smart
    print "------interface----------------------"
    print sda.interface
    print "------attributes----------------------"
    print sda.attributes
    print "------capacity----------------------"
    print sda.capacity
    print "------supports_smart----------------------"
    print sda.supports_smart
    print "------tests----------------------"
    print sda.tests
    print "-----all-tests----------------------"
    sda.all_selftests()
    print "-----all_attributes----------------------"
    sda.all_attributes() 
    
