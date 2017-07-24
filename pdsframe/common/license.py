# -*- coding: utf-8 -*
#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import base64
import sys
import tempfile
import os, re, time
import ctypes
from ctypes import *
import unicodedata

from pdsframe.common.logger import logger
from pdsframe.common.config import config

NAME_MAX_LONG = 2048
SYSTEM_UUID_LENGTH = 36

LICENSE_PATH     = "/opt/smartmgr/files/conf/pbdata.lic"
LICENSE_PATH_BAK = "/opt/smartmgr/files/conf/pbdata.lic_bak"
Time             = "/var/log/smartmon/cputime"

PBLIC_MODE_DATE     = 1   #时间段
PBLIC_MODE_TIME_LONG= 2   #时间长
PBLIC_MODE_FOREVER  = 3   #永久性
PBLIC_IS_INIT       = 4   #初始License
PBLIC_NOTIS_INIT    = 5   #外来License

LICENSE_SMARTMGR_SUPPORT    = 0x00000001
LICENSE_SMARTMON_SUPPORT    = 0x00000002
LICENSE_SMARTSTORE_SUPPORT  = 0X00000004
LICENSE_SMARTCACHE_SUPPORT  = 0x00000008
LICENSE_SMARTSNMP_SUPPORT   = 0x00000010
LICENSE_SMARTQoS_SUPPORT    = 0x00000020
LICENSE_PAL_SUPPORT         = 0x00000040
LICENSE_ALL_SUPPORT         = 0xFFFFFFFF


class sys_info(Structure):
    _fields_ = [
           ("lic_init_mode", c_uint32),
           ("lic_mode", c_uint32),
           ("lic_days", c_uint32),
           ("install_time",c_uint64 ),
           ("authorize_time", c_uint64),
           ("last_time", c_uint64),
           ("sys_uuid", c_char * SYSTEM_UUID_LENGTH),
            ]
    
    def __init__(self):
         pass

class lic_info(Structure):
    _fields_ = [
            ("product", c_char*NAME_MAX_LONG),
            ("company", c_char*NAME_MAX_LONG),
            ("prjname", c_char*NAME_MAX_LONG),
            ("contract_num", c_char*NAME_MAX_LONG),
            ("module", c_uint),
            ("fun", c_uint),
            ]

    def __init__(self):
        pass


class pb_lic(Structure):
    _fields_ = [
            ("lic_init_mode", c_uint32),
            ("lic_mode", c_uint32),
            ("lic_days", c_uint32),
            ("install_time", c_uint64),
            ("authorize_time", c_uint64),
            ("last_time", c_uint64),
            ("sys_uuid", c_char * SYSTEM_UUID_LENGTH),
            ("product", c_char*2048),
            ("company", c_char*2048),
            ("prjname", c_char*2048),
            ("contract_num", c_char*2048),
            ("module", c_uint32),
            ("fun", c_uint32),
             ]

class License:
    def __init__(self):
        self.libc = cdll.LoadLibrary("/usr/lib64/libpblic.so")

    def __get_lic_info(self):
        lic = {}
        plic = pointer(lic_info()) 
        ret = self.libc.pbdata_get_lic_info(plic)
        if ret: return None

        lic["product"] = plic.contents.product
        lic["company"] = plic.contents.company
        lic["prjname"] = plic.contents.prjname
        lic["contract_num"] = plic.contents.contract_num
        lic["module"] = plic.contents.module
        lic["fun"] = plic.contents.fun
        return lic
   
    def __get_sys_info(self):
        plic = pointer(sys_info()) 
        ret = self.libc.pbdata_get_sys_info(plic)
        if ret: return None
        lic = {}
        lic["lic_init_mode"]  = plic.contents.lic_init_mode
        lic["lic_mode"]       = plic.contents.lic_mode
        lic["lic_days"]       = plic.contents.lic_days
        lic["install_time"]   = plic.contents.install_time
        lic["authorize_time"] = plic.contents.authorize_time
        lic["last_time"]      = plic.contents.last_time
        lic["sys_uuid"]       = plic.contents.sys_uuid
        return lic

    def __get_all_lic_info(self):
        sys_info = self.__get_sys_info()
        if not sys_info: return None

        lic_info = self.__get_lic_info()
        if not lic_info: return None

        sys_info.update(lic_info)
        return sys_info

    def __check_time_invalid(self,t):
        if not os.path.exists(Time):
            if not os.path.exists(os.path.dirname(Time)):
                os.makedirs(os.path.dirname(Time), 0755)
            try:
                f = open(Time,"w")
                f.write(str(1))
                f.close()
            except IOError,e:
                return -2
        else:
            try:
                f = open(Time,"r")
            except IOError,e:
                return -2
            t_tmp = f.read()
            if t_tmp != "":
                if float(t) < float(t_tmp):
                    return -1
                else:
                    return 0
            return 0

    def __display(self):
        info = self.__get_all_lic_info()
        if not info: return -1

        disp = {}
        
        if info["lic_init_mode"] == PBLIC_IS_INIT:
            disp["LicInitMode"] = "LocalLicense"
        elif info["lic_init_mode"] == PBLIC_NOTIS_INIT:
            disp["LicInitMode"] = "ForeignLicense"
        
        disp["InstTime"] =  time.strftime("%Y-%m-%d",time.localtime(info["install_time"]))
        disp["AuthTime"] =  time.strftime("%Y-%m-%d",time.localtime(info["authorize_time"]))
        disp["LastTime"] =  time.strftime("%Y-%m-%d",time.localtime(info["last_time"]))

        if info["lic_mode"] == PBLIC_MODE_DATE:
            disp["LicMode"] = "Date"
        elif info["lic_mode"] == PBLIC_MODE_TIME_LONG:
            disp['LicMode'] = "Days"
        elif info["lic_mode"] == PBLIC_MODE_FOREVER:
            disp['LicMode'] = "Forever"

        disp["SmartMgrSupport"]   = info["module"] & LICENSE_SMARTMGR_SUPPORT   and "Yes" or "No"
        disp["SmartCacheSupport"] = info["module"] & LICENSE_SMARTCACHE_SUPPORT and "Yes" or "No"
        disp["PALSupport"]        = info["module"] & LICENSE_PAL_SUPPORT        and "Yes" or "No"
        disp["SmartMonSupport"]   = info["module"] & LICENSE_SMARTMON_SUPPORT   and "Yes" or "No"
        disp["SmartStoreSupport"] = info["module"] & LICENSE_SMARTSTORE_SUPPORT and "Yes" or "No"
        disp["SmartSnmpSupport"]  = info["module"] & LICENSE_SMARTSNMP_SUPPORT  and "Yes" or "No"
        disp["SmartQoSSupport"]   = info["module"] & LICENSE_SMARTQoS_SUPPORT   and "Yes" or "No"
        return disp
            
    def support_smartmgr(self):
        ret = self.libc.pbdata_verify_smartmgr()
        if ret: return -1
        return 0

    def support_smartcache(self):
        ret = self.libc.pbdata_verify_smartcache()
        if ret: return -1
        return 0

    def support_pal(self):
        ret = self.libc.pbdata_verify_pal()
        if ret: return -1
        return 0

    def support_license_time(self):
        if self.libc.pbdata_license_disable():#license不启用
            PASSWD = config.safe_get('model-config', 'lic-pass')
            if self.libc.get_license_passwd() == int(PASSWD):
                return 0
            else:
                return -1
        if self.support_smartmgr():
            return -1
        sys = self.__get_sys_info()
        if not sys: return -1
        tm = time.time()
        
        if sys["lic_mode"] == PBLIC_MODE_FOREVER:
            return 0

        if tm < sys["authorize_time"]:
            if not os.path.exists(Time):
                if not os.path.exists(os.path.dirname(Time)):
                    os.makedirs(os.path.dirname(Time), 0755)
                try:
                    f = open(Time,"w")
                    f.close()
                except IOError,e:
                    return -2
            else:
                try:
                    f = open(Time,"w")
                    f.close()
                except IOError,e:
                    return -2
            return -1
        t = sys["last_time"] - sys["authorize_time"]
        ret = self.__check_time_invalid(t)
        if ret == -1:             return -1
        if tm > sys["last_time"]: return -1
        return 0

    def get_license_file(self):
        if not os.path.exists(LICENSE_PATH):
            if self.libc.pbdata_init_invalid_lic_file():
                return -1, "init invalid error"
        try:
            f = open(LICENSE_PATH, 'rb')
            content = f.read()
            f.close()
        except:
            return -1, "read license file failed"
        return 0, base64.b64encode(content)

    def put_license_file(self, license_base64):
        try:
            content = base64.b64decode(license_base64)
        except:
            return -1, "base64 decode failed"

        if os.path.exists(LICENSE_PATH):
            if os.path.exists(LICENSE_PATH_BAK):
                os.remove(LICENSE_PATH_BAK)
            os.rename(LICENSE_PATH,LICENSE_PATH_BAK)

        with open(LICENSE_PATH, "wb") as code:
            code.write(content)

        ret,msg = self.licmgr_info()
        if ret == -1:
            if os.path.exists(LICENSE_PATH_BAK):
                if os.path.exists(LICENSE_PATH):
                    os.remove(LICENSE_PATH)
                os.rename(LICENSE_PATH_BAK,LICENSE_PATH)
            return -1, "License is not for this node"

        if not os.path.exists(Time):
            if not os.path.exists(os.path.dirname(Time)):
                os.makedirs(os.path.dirname(Time), 0755)
            try:
                f = open(Time,"w")
                f.write(str(1))
                f.close()
            except IOError,e:
                return -1, e
        else:
            try:
                f = open(Time,"w")
                f.write(str(1))
                f.close()
            except IOError,e:
                return -1, e
        return 0,''

    #外部接口
    def licmgr_info(self,params={}):
        info = self.__display()
        if info == -1:
            return -1,{}
        status = {}
        ret = self.support_license_time()
        if ret == 0:
            status["Status"] = "Enable"
        elif ret == -1:
            status["Status"] = "Disable"
        info.update(status)
        return 0,info
