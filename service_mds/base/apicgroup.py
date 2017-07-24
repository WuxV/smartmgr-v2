#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import pyudev, os
from pdsframe import *

class APICGroup:
    def __init__(self):
        # 由于centos7/centos6的默认挂载点不一样, 因此要实时获取
        e,path = command("cat /proc/mounts  | grep group | grep blkio | awk '{print $2}'")
        if path == "":
            CGROUP_ROOT = "/cgroup/blkio"
        else:
            CGROUP_ROOT = path.strip()
        
        self.CGROUP_READ_BPS   = os.path.join(CGROUP_ROOT, 'blkio.throttle.read_bps_device')
        self.CGROUP_READ_IOPS  = os.path.join(CGROUP_ROOT, 'blkio.throttle.read_iops_device')
        self.CGROUP_WRITE_BPS  = os.path.join(CGROUP_ROOT, 'blkio.throttle.write_bps_device')
        self.CGROUP_WRITE_IOPS = os.path.join(CGROUP_ROOT, 'blkio.throttle.write_iops_device')

    def set_qos(self, maj_min, params={}):
        assert(params.has_key("read_bps_device"))
        assert(params.has_key("read_iops_device"))
        assert(params.has_key("write_bps_device"))
        assert(params.has_key("write_iops_device"))

        try:
            # read_bps_device
            cmd = "%s %s" % (maj_min, params['read_bps_device']) 
            fsys = open(self.CGROUP_READ_BPS, 'w', params['read_bps_device'])
            fsys.write(cmd)
            fsys.close()

            # read_iops_device
            cmd = "%s %s" % (maj_min, params['read_iops_device']) 
            fsys = open(self.CGROUP_READ_IOPS, 'w', params['read_iops_device'])
            fsys.write(cmd)
            fsys.close()

            # write_bps_device
            cmd = "%s %s" % (maj_min, params['write_bps_device']) 
            fsys = open(self.CGROUP_WRITE_BPS, 'w', params['write_bps_device'])
            fsys.write(cmd)
            fsys.close()

            # write_iops_device
            cmd = "%s %s" % (maj_min, params['write_iops_device']) 
            fsys = open(self.CGROUP_WRITE_IOPS, 'w', params['write_iops_device'])
            fsys.write(cmd)
            fsys.close()
        except Exception as e:
            return -1, str(e)

        new_params = self.get_qos(maj_min)

        for i in ['read_bps_device', 'read_iops_device', 'write_bps_device', 'write_iops_device']:
            if new_params[i] != params[i]:
                return -1, "Set '%s' failed" % i
        return 0, ''

    def drop_qos(self, maj_min):
        params = {}
        params['read_bps_device']   = 0 
        params['read_iops_device']  = 0 
        params['write_bps_device']  = 0 
        params['write_iops_device'] = 0 
        ret, result = self.set_qos(maj_min, params)
        if ret:
            return -1, "Drop '%s' failed" % maj_min

        return 0, ''

    def get_qos(self, maj_min):
        params = {}
        params["read_bps_device"]   = self._get_qos_by_path(maj_min, self.CGROUP_READ_BPS)
        params["read_iops_device"]  = self._get_qos_by_path(maj_min, self.CGROUP_READ_IOPS)
        params["write_bps_device"]  = self._get_qos_by_path(maj_min, self.CGROUP_WRITE_BPS)
        params["write_iops_device"] = self._get_qos_by_path(maj_min, self.CGROUP_WRITE_IOPS)
        return params

    def _get_qos_by_path(self, maj_min, path):
        try:
            fsys = open(path, 'r')
            content = fsys.read()
            fsys.close()
            for line in content.splitlines():
                if line.split()[0] == maj_min:
                    return int(line.split()[1])
            return 0
        except Exception as e:
            return -1
