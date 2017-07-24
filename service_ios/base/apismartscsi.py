# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import re, os, json, stat, pyudev, pwd, grp

from pdsframe import *
from service_ios import g

SMARTSCSI_ROOT_DIR      = '/sys/kernel/scst_tgt/'
SMARTSCSI_DEVS_DIR      = SMARTSCSI_ROOT_DIR + 'devices'
SMARTSCSI_HANDLERS_DIR  = SMARTSCSI_ROOT_DIR + 'handlers'
SMARTSCSI_TARGETS_DIR   = SMARTSCSI_ROOT_DIR + 'targets'
SMARTSCSI_SRPT_DIR      =  SMARTSCSI_TARGETS_DIR + '/ib_srpt'
SMARTSCSI_VDISK         =  'vdisk_blockio'

class APISmartScsi:
    def __init__(self):
        self.ib_tgts = {}
        self.errmsg = ""

    # 获取device属性
    def __get_device_attrbutes(self, dev_sys_path):
        files = os.listdir(dev_sys_path)
        attrs = {}
        for file in files:
            if file == "filename":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    devname = f.readline().strip()
                    attrs[file] = devname
                    f.close()

            if file == "size_mb":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    size_mb = f.readline().strip()
                    attrs[file] = int(size_mb)
                    f.close()

            if file == "threads_pool_type":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    type = f.readline().strip()
                    attrs[file] = type
                    f.close()

            if file == "threads_num":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    num = f.readline().strip()
                    attrs[file] = int(num)
                    f.close()

            if file == "t10_dev_id":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    id_str = f.readline().strip()
                    attrs[file] = id_str
                    f.close()

            if file == "io_error":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    id_str = f.readline().strip()
                    attrs[file] = id_str
                    f.close()

            if file == "last_errno":
                f = open(os.path.join(dev_sys_path, file), 'r')
                if f:
                    id_str = f.readline().strip()
                    attrs[file] = id_str
                    f.close()

            if file == "exported":
                epts = os.listdir(os.path.join(dev_sys_path, file))
                ept_dict = {}
                exported = 0
                attrs["group_name"] = []
                for export in epts:
                    ept = os.readlink(os.path.join(dev_sys_path, file, export))
                    pths = ept.split("/")
                    if len(pths) > 8:
                        group = pths[-3]
                        target = pths[5]
                        attrs["group_name"].append(group)
                    else:
                        group = ""
                        target = pths[-3]

                    ept_dict[target] = pths[-1]
                    exported = 1
                if exported:
                    attrs[file] = ept_dict
        return attrs

    # 获取device列表, n:n:n:n=>attr
    def get_lun_list(self):
        if not os.path.exists(SMARTSCSI_DEVS_DIR):
            return {}

        mm2stat = {}
        try:
            f = open("/proc/diskstats", 'r')
            lines = f.readlines()
            f.close()
            for line in lines:
                fields = line.strip().split()
                mm = "%s.%s" % (fields[0], fields[1])
                mm2stat[mm] = {}
                mm2stat[mm]["rio"]     = fields[3]  # number of issued reads
                mm2stat[mm]["rmerge"]  = fields[4]  # number of reads merged
                mm2stat[mm]["rsect"]   = fields[5]  # number of sectors read
                mm2stat[mm]["ruse"]    = fields[6]  # number of millisecdonds spent reading
                mm2stat[mm]["wio"]     = fields[7]  # number of writes completed
                mm2stat[mm]["wmerge"]  = fields[8]  # number of writes merged
                mm2stat[mm]["wsect"]   = fields[9]  # number of sectors written
                mm2stat[mm]["wuse"]    = fields[10] # number of milliseconds spent writing
                mm2stat[mm]["running"] = fields[11] # instantaneous count of IOs currently in flight
                mm2stat[mm]["use"]     = fields[12] # number of milliseconds spent doing I/Os
                mm2stat[mm]["aveq"]    = fields[13] # weighted number of milliseconds spent doing I/Os
        except Exception as e:
            pass

        scsidevs = {}

        files = os.listdir(SMARTSCSI_DEVS_DIR)
        devreg = ur"^(\d+):(\d+):(\d+):(\d+)$"
        for file in files:
            if re.match(devreg, file):
                continue
            attrs = self.__get_device_attrbutes(SMARTSCSI_DEVS_DIR + "/" + file)
            stats = self.__get_device_stats(attrs['filename'], mm2stat)
            scsidevs[file] = {}
            scsidevs[file]['attrs'] = attrs
            scsidevs[file]['stats'] = stats
        return scsidevs

    def __get_device_stats(self, filename, mm2stat):
        if not os.path.exists(filename):
            return {}
        fstat = os.stat(os.path.realpath(filename))
        if not stat.S_ISBLK(fstat[stat.ST_MODE]):
            return {}
        mm = "%s.%s" % (os.major(fstat.st_rdev), os.minor(fstat.st_rdev))
        if mm not in mm2stat:
            return {}
        return mm2stat[mm]

    # 获取指定target的enabled属性
    def __get_target_attributes(self, tgt_sys_path):
        files = os.listdir(tgt_sys_path)
        attrs = {}
        for file in files:
            if file == "enabled":
                f = open(os.path.join(tgt_sys_path, file), 'r')
                if f:
                    enabled = f.readline().strip()
                    attrs[file] = int(enabled)
                    f.close()
        return attrs

    # 获取target列表
    def __get_ib_targets(self):
        self.ib_tgts.clear()
        files = os.listdir(SMARTSCSI_SRPT_DIR)
        for file in files:
            path = os.path.join(SMARTSCSI_SRPT_DIR, file)
            if os.path.isdir(path):
                self.ib_tgts[file] = self.__get_target_attributes(path)
        if len(files):
            return 0
        else:
            self.errmsg = "No ib targets found"
            return 1

    # 获取target=>lun=>device
    def __get_ib_target_luns(self,group=None):
        if self.__get_ib_targets():
            return 1

        for target in self.ib_tgts.keys():
            if group:
                lundir = os.path.join(SMARTSCSI_SRPT_DIR, target,"ini_groups",group,"luns")
            else:
                lundir = os.path.join(SMARTSCSI_SRPT_DIR, target, "luns")
            if not os.path.exists(lundir):
                self.errmsg = "Internal error: path %s not exists!" %lundir
                return 1
            luns = {}
            files = os.listdir(lundir)
            for file in files:
                lun_dir = os.path.join(lundir, file)
                if os.path.isdir(lun_dir):
                    device_name = os.path.basename(os.readlink(os.path.join(lun_dir, "device")))
                    luns[file] = device_name
            self.ib_tgts[target]["luns"] = luns
        return 0

    # 获取target=>group=>initiators
    def __get_ib_target_groups(self):
        if self.__get_ib_targets():
            return 1

        for target in self.ib_tgts.keys():
            groupdir = os.path.join(SMARTSCSI_SRPT_DIR, target, "ini_groups")
            if not os.path.exists(groupdir):
                self.errmsg = "Internal error: path %s not exists!" %groupdir
                return 1
            groups = {}
            inis = {}
            files = os.listdir(groupdir)
            for f in files:
                group_dir = os.path.join(groupdir, f)
                if os.path.isdir(group_dir):
                    groups[f] = group_dir
                    ini_dir = os.path.join(group_dir,"initiators")
                    ini_files = os.listdir(ini_dir)
                    for ini_f in ini_files:
                        if ini_f == "mgmt":
                            continue
                        inis[ini_f[1:]] = ini_f

            self.ib_tgts[target]["groups"] = groups
            self.ib_tgts[target]["inis"] = inis
        return 0

    # 检查指定的device是否有被打开
    def __is_dev_opened(self, devname):
        if os.path.exists(os.path.join(SMARTSCSI_DEVS_DIR, devname)):
            return 1
        return 0

    # 检查指定的device是否有被映射出去
    def __is_dev_exported(self, devname,group_name=None):
        if not self.__is_dev_opened(devname):
            return 0
        path = os.path.join(SMARTSCSI_DEVS_DIR, devname, "exported")
        exports = os.listdir(path)
        
        found=0
        for k in exports:
            lun_path=os.path.join(path,k)
            if os.path.islink(lun_path):
                link=os.readlink(lun_path)
                if "targets/copy_manager/copy_manager_tgt" in link:
                    continue
                pths = link.split("/")
                if len(pths) > 8:
                    group = pths[-3]
                else:
                    group = None
                if group_name and group_name == group:
                    return 1
                found += 1
        if not group_name and found >=1:
            return 1
        return 0

    # 添加device
    def __open_dev(self, params={}):
        try:
            # 打开设备
            mgmt = os.path.join(SMARTSCSI_HANDLERS_DIR, SMARTSCSI_VDISK, "mgmt")
            fobj = open(mgmt, 'w', 0)
            cmd = "add_device %s filename=%s" %(params["device_name"], params["path"])
            fobj.write(cmd)
            fobj.close()

            # 更新t10_dev_id
            t10_dev_id = os.path.join(SMARTSCSI_DEVS_DIR, params['device_name'], "t10_dev_id")
            fobj = open(t10_dev_id, 'w', 0)
            fobj.write(params['t10_dev_id'])
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1
        return 0

    # 关闭device
    def __close_dev(self, devname):
        if not self.__is_dev_opened(devname):
            return 0

        mgmt = os.path.join(SMARTSCSI_HANDLERS_DIR, SMARTSCSI_VDISK, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "del_device %s" %devname
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    # 添加lun
    def __add_lun(self, target, lun, params={},group=None):
        if group:
            _lundir = os.path.join(SMARTSCSI_SRPT_DIR, target,"ini_groups",group,"luns")
        else:
            _lundir = os.path.join(SMARTSCSI_SRPT_DIR, target, "luns")

        lundir = os.path.join(_lundir, str(lun))
        if os.path.exists(lundir):
            self.errmsg = "Target %s lun %s already exist, shouldn't be." %(target,lun)
            return 1
        
        mgmt = os.path.join(_lundir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "add %s %d" %(params["device_name"], lun)
        if params.has_key("read_only"):
            cmd += " read_only=%d" %params["read_only"]

        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    # 删除lun
    def __del_lun(self, target, lun,group=None):
        if target=="copy_manager_tgt":
            return 0
        
        if group:
            _lundir = os.path.join(SMARTSCSI_SRPT_DIR, target,"ini_groups",group,"luns")
        else:
            _lundir = os.path.join(SMARTSCSI_SRPT_DIR, target, "luns")

        lundir = os.path.join(_lundir, str(lun))
        if not os.path.exists(lundir):
            self.errmsg = "Target %s lun %s not exists" %(target,lun)
            return 1

        mgmt = os.path.join(_lundir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "del %d" %lun
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1
        return 0


    def add_lun(self,params={}):
        if not os.path.exists(SMARTSCSI_SRPT_DIR):
            self.errmsg = "ib-srpt not load"
            return 1

        if not params.has_key("path"):
            self.errmsg = "Invalid argument, device path needed"
            return 1

        if not params.has_key("device_name"):
            self.errmsg = "Invalid argument, device name needed"
            return 1

        if params.has_key("group_name"):
            group_name = params["group_name"]
        else:
            group_name = None

        if group_name:
            for group in group_name:
                params["group_name"] = group
                if self.add_lun_group(params):
                    return 1
            return 0

        return self.add_lun_group(params)


    def add_lun_group(self, params={}):
        if params.has_key("group_name"):
            group_name = params["group_name"]
        else:
            group_name = None

        ret = self.__get_ib_target_luns(group_name)
        if ret:
            return 1

        if not self.__is_dev_opened(params["device_name"]):
            if self.__open_dev(params):
                return 1
        if not self.__is_dev_exported(params["device_name"],group_name):
            available = {}
            if params.has_key("lun"):
                for key in self.ib_tgts.keys():
                    luns = self.ib_tgts[key]["luns"]
                    for lun in luns.keys:
                        if int(lun) == int(params["lun"]):
                            self.errmsg = "LUN %d already exported" %int(lun)
                            return 1
                        if luns[lun] == params["device_name"]:
                            self.errmsg = "Device %s(%s) already exported" %(params["device_name"], params["path"])
                            return 1
                for key in self.ib_tgts.keys():
                    available[key] = int(params["lun"])
            else:
                for key in self.ib_tgts.keys():
                    i = 0
                    exist = 0
                    lun_a = self.ib_tgts[key]["luns"]
                    lun_b = list()
                    for lun in lun_a.keys():
                        lun_b.append(int(lun))

                    for lun in sorted(lun_b):
                        if int(lun) == i:
                            i += 1
                        if lun_a[str(lun)] == params["device_name"]:
                            self.errmsg = "Device %s(%s) already exported" %(params["device_name"], params["path"])
                            return 1
                    available[key] = i

            done = {}
            failed = 0
            for key in available.keys():
                if not self.__add_lun(key, available[key], params,group_name):
                    done[key] = available[key]
                else:
                    failed = 1
                    break;
            if failed:
                for key in done.keys():
                    self.__del_lun(key, done[key],group_name)
                return 1;
        e, res = self.__create_asm_local_device(params['path'], params['device_name'])
        if e:
            self.errmsg = res
            return e
        return 0


    def drop_lun(self,devname,groups=None):
        if groups:
            for group in groups:
                e,exist = self.drop_lun_with_group(devname,group)
                if e:
                    return 1,exist
            return 0,exist
        else:
            return self.drop_lun_with_group(devname)


    def drop_lun_with_group(self, devname,group=None):
        if not self.__is_dev_opened(devname):
            return 0,0
        
        path = os.path.join(SMARTSCSI_DEVS_DIR, devname, "exported")
        exports = os.listdir(path)
        exist=len(exports)

        for export in exports:
            ept = os.readlink(os.path.join(path, export))
            pths = ept.split("/")
            if len(pths) > 8:
                group_name = pths[-3]
            else:
                group_name = None
            if group and group != group_name:
                continue
            if self.__del_lun(pths[5], int(pths[-1]),group):
                return 1,exist
            exist-=1

        if not exist:
            if self.__close_dev(devname):
                return 1,exist
        e, res = self.__delete_asm_local_device(devname)
        if e:
            self.errmsg = res
            return e,exist
        return 0,exist

    # 使target变为可用, 默认为不可以
    def enable_targets(self):
        if not os.path.exists(SMARTSCSI_SRPT_DIR):
            self.errmsg = "ib-srpt not load"
            return 1

        if self.__get_ib_targets():
            return 1
        # 支持多卡多target输出同一个lun
        if len(self.ib_tgts) >= 2:
            for target in self.ib_tgts.keys():
                try:
                    fobj = open(os.path.join(SMARTSCSI_SRPT_DIR, target, "io_grouping_type"), 'w', 0)
                    fobj.write("this_group_only")
                    fobj.close()
                except IOError as err:
                    self.errmsg = "Group only target %s failed: %s" %(target, err)
                    return 1
        for target in self.ib_tgts.keys():
            try:
                fobj = open(os.path.join(SMARTSCSI_SRPT_DIR, target, "enabled"), 'w', 0)
                fobj.write("1")
                fobj.close()
            except IOError as err:
                self.errmsg = "Enable target %s failed: %s" %(target, err)
                return 1
        # self.__update_srp_daemon_config(self.ib_tgts.keys())
        return 0

    # 设置device参数
    def smartscsi_set_attrs(self, devname, params={}):
        if not self.__is_dev_opened(devname):
            self.errmsg = "Device %s not opened" %devname
            return 1

        for key in params.keys():
            param = os.path.join(SMARTSCSI_DEVS_DIR, devname, key)
            if not os.path.exists(param):
                self.errmsg = "Parameter %s not exist!" %key
                return 1

        for key in params.keys():
            file = os.path.join(SMARTSCSI_DEVS_DIR, devname, key)
            try:
                fobj = open(file, "w", 0)
            except IOError as err:
                self.errmsg = "Failed to open file %s: %s" %(file, err)
                return 1

            value = "%s" %params[key]
            try:
                fobj.write(value)
                fobj.close()
            except IOError as err:
                self.errmsg = "write value \"%s\" to %s failed: %s" %(cmd, mgmt, err)
                return 1
        return 0

    def __create_asm_local_device(self, path, device_name):
        if g.platform['sys_mode'].lower() != "merge":
            return 0, ''
        try:
            uid = pwd.getpwnam('grid').pw_uid
            gid = grp.getgrnam('asmadmin').gr_gid
            if not os.path.exists("/dev/asmdisks"):
                os.mkdir("/dev/asmdisks")
                os.chown("/dev/asmdisks", uid, gid)
            asm_dev = "/dev/asmdisks/%s" % device_name
            if os.path.exists(asm_dev):
                os.remove(asm_dev)
            device = pyudev.Devices.from_device_file(pyudev.Context(), path)
            os.mknod(asm_dev, 0o660 | stat.S_IFBLK, device.device_number)
            os.chmod(asm_dev, 0o660)
            os.chown(asm_dev, uid, gid)
        except Exception as e:
            return -1, e
        return 0, ''

    def __delete_asm_local_device(self, device_name):
        if g.platform['sys_mode'].lower() != "merge":
            return 0, ''
        try:
            asm_dev = "/dev/asmdisks/%s" % device_name
            if os.path.exists("/dev/asmdisks") and os.path.exists(asm_dev):
                os.remove(asm_dev)
        except Exception as e:
            return -1, e
        return 0, ''

    def __update_srp_daemon_config(self, targets):
        if g.platform['sys_mode'].lower() == "merge":
            return
        out = ["# Automatically generated by smartmgr only for sys-mode: merge"]
        out.append("")
        for target in targets:
            out.append("d ioc_guid=%s" % target.replace(":", ''))
        out.append("")
        with open("/etc/srp_daemon.conf", 'w', 0) as f:
            f.write("\n".join(out))

    def drop_group(self,node_uuid):
        if not os.path.exists(SMARTSCSI_SRPT_DIR):
            self.errmsg = "ib-srpt not load"
            return 1

        ret = self.__get_ib_target_luns(node_uuid)
        if ret:
            return 1
        
        for key in self.ib_tgts.keys():
            if len(self.ib_tgts[key]["luns"]) > 0:
                self.errmsg = "The group %s has luns drop first"%node_uuid
                return 1

            ret = self._clear_initiators(key,node_uuid)
            if ret:
                return 1

            ret = self._drop_group(key,node_uuid)
            if ret:
                return 1

        return 0

    def _drop_group(self,target,node_uuid):
        _groupdir = os.path.join(SMARTSCSI_SRPT_DIR, target, "ini_groups")
        group = os.path.join(_groupdir, str(node_uuid))
        if not os.path.exists(group):
            self.errmsg = "Target %s group %s not exist" %(target,node_uuid)
            return 1
        mgmt = os.path.join(_groupdir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "del %s" %(node_uuid)
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    def list_group(self):
        if not os.path.exists(SMARTSCSI_SRPT_DIR):
            self.errmsg = "ib-srpt not load"
            return 1

        if self.__get_ib_target_groups():
            return 1

        return self.ib_tgts


    def add_group(self,node_uuid,guids):
        if not os.path.exists(SMARTSCSI_SRPT_DIR):
            self.errmsg = "ib-srpt not load"
            return 1

        if self.__get_ib_targets():
            return 1
        for key in self.ib_tgts.keys():
            ret = self._add_group(key,node_uuid)
            if ret:
                return 1
            
            for guid in guids:
                ret = self._add_initiators(key,node_uuid,guid)
                if ret:
                    return 1
        return 0

    def _add_initiators(self,target,node_uuid,guid):
        _inidir = os.path.join(SMARTSCSI_SRPT_DIR, target, "ini_groups",node_uuid,"initiators")
        ini = os.path.join(_inidir,"*"+str(guid))
        if os.path.exists(ini):
            self.errmsg = "Target %s group %s ini %s already exist" %(target,node_uuid,guid)
            return 1
        
        mgmt = os.path.join(_inidir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "add *%s" %(guid)
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    def _clear_initiators(self,target,node_uuid):
        _inidir = os.path.join(SMARTSCSI_SRPT_DIR, target, "ini_groups",node_uuid,"initiators")
        if not os.path.exists(_inidir):
            self.errmsg = "Target %s group %s not exist" %(target,node_uuid)
            return 1
        
        mgmt = os.path.join(_inidir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "clear"
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    
    def _add_group(self,target,node_uuid):
        _groupdir = os.path.join(SMARTSCSI_SRPT_DIR, target, "ini_groups")
        group = os.path.join(_groupdir, str(node_uuid))
        if os.path.exists(group):
            self.errmsg = "Target %s group %s already exist" %(target,node_uuid)
            return 1
        mgmt = os.path.join(_groupdir, "mgmt")
        try:
            fobj = open(mgmt, 'w', 0)
        except IOError as err:
            self.errmsg = "Cannot open file %s: %s" %(mgmt, err)
            return 1

        cmd = "create %s" %(node_uuid)
        try:
            fobj.write(cmd)
            fobj.close()
        except IOError as err:
            self.errmsg = "write cmd \"%s\" to %s failed: %s" %(cmd, mgmt, err)
            return 1

        return 0

    # 对设备擦0处理
    def zero_device(self, path):
        e, out = command("dd if=/dev/zero of=%s bs=1M count=100 oflag=direct" % path)
        if e:
            self.errmsg = out
        return e

if __name__ == "__main__":
    # 获取lun/device列表
    # print json.dumps(APISmartScsi().get_lun_list(), indent=4)

    # # 删除lun
    # print APISmartScsi().drop_lun("su001_lvvote")
    # 
    # # 创建lun
    # params = {}
    # params['device_name'] = "su001_lvvote"
    # params['path']        = "/dev/VolGroup/lvvote"
    # params['t10_dev_id']  = "abc"
    # print APISmartScsi().add_lun(params)
    # 
    # # 将target enable起来
    #print APISmartScsi().enable_targets()

    print APISmartScsi().add_group("xxxxxxx")
