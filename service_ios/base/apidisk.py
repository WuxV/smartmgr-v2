#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import pyudev,os, uuid, time
from pdsframe import *
from service_ios.base.cmdlist import *

from service_ios.base.common import get_mount_list, is_flash, is_df, is_nvme, get_disk_disk_part
from service_ios.base.diskparted import DiskParted
from service_ios.base.diskheader import DiskHeader

# 获取需要过滤掉的device-name, 目前仅包含过滤系统盘的设备号
def get_skip_device_number(mount_list, context):
    # /dev/mapper/xxx => 252:0
    dm_2_dn = {}
    e, dmsetup_table = command("dmsetup table --target linear")
    if e: return e, dmsetup_table
    for dm in filter(lambda dm:len(dm.split()) >= 5 and len(dm.split()[4].split(':')) == 2, dmsetup_table.splitlines()):
        dm_2_dn["/dev/mapper/%s" % dm.split()[0][:-1]] = dm.split()[4]
    
    skip_list = []
    for dev, point in mount_list.items():
        if point in ['/', '/boot', '/home']:
            if dev in dm_2_dn.keys():
                skip_list.append(dm_2_dn[dev])
            else:
                d = pyudev.Devices.from_device_file(context, dev)
                skip_list.append("%s:%s"  % (os.major(d.device_number), os.minor(d.device_number)))
    return 0, skip_list

class APIDisk:
    # 获取节点的所有磁盘，不包括系统盘，包括虚拟机的vdx盘
    def get_disk_list(self):
        mount_list = get_mount_list()
        if mount_list == None:
            return -1, "Get mount list failed"

        disk_list=[]
        context = pyudev.Context()
        disks = context.list_devices(subsystem='block', DEVTYPE='disk')
        parts = context.list_devices(subsystem='block', DEVTYPE='partition')

        # 获取需要过滤调的设备号
        e, skip_device_number = get_skip_device_number(mount_list, context)
        if e: return e, skip_device_number

        try:
            dev_pasts = {}
            for part in parts:
                if part.parent['DEVNAME'] not in dev_pasts.keys():
                    dev_pasts[part.parent['DEVNAME']] = []
                part_info = {}
                part_info['DEVNAME'] = str(part['DEVNAME'])
                # FIXME: part_info['DEVNAME']正常是/dev/sdXN的形式 但是不确定的情况下，会出现sdXN的性质 因此此处补充/dev/
                if not part_info['DEVNAME'].startswith("/dev/"):
                    part_info['DEVNAME'] = "/dev/%s" % part_info['DEVNAME']
                part_info['SIZE']  = int(part.attributes.get('size'))
                part_info['INDEX'] = get_disk_disk_part(part_info['DEVNAME'])
                part_info['DE_NO'] = "%s:%s"  % (os.major(part.device_number), os.minor(part.device_number))

                if part_info['DEVNAME'] in mount_list.keys():
                    part_info['MOUNT_POINT'] = mount_list[part_info['DEVNAME']]
                dev_pasts[part.parent['DEVNAME']].append(part_info)

            for disk in disks:
                major = os.major(disk.device_number)
                # smartcache在dmsetup remove的时候，会出现disk['DEVNAME'] == dm-2, 且major == 253的状态出现
                if not disk['DEVNAME'].startswith("/dev/"):
                    continue
                if not major == 8 and not (65 <= major <= 71) and not (128 <= major <= 135) and not is_flash(disk['DEVNAME']):
                    continue
                if disk.get('ID_VENDOR') == "SCST_BIO":
                    continue
                # 过滤掉容量小于10G的盘
                if int(disk.attributes.get('size'))*512 < (10<<30):
                    continue

                disk_info = {}
                if is_nvme(disk['DEVNAME']):
                    disk_info['drive_type'] = "nvme"
                # 标记df类型保存卡信息
                if is_df(disk['DEVNAME']):
                    disk_info['drive_type'] = "df_pcie"

                disk_info['DEVNAME'] = str(disk['DEVNAME'])
                disk_info['SIZE']    = int(disk.attributes.get('size'))
                disk_info['DE_NO']   = "%s:%s" % (os.major(disk.device_number), os.minor(disk.device_number))

                # 获取盘头信息
                e, header = DiskHeader(disk_info['DEVNAME']).get_header_data()
                if e == -2:
                    continue
                if e == 0:
                    disk_info['HEADER'] = header

                # 补充分区信息
                disk_info['PARTS'] = []
                if disk_info['DEVNAME'] in dev_pasts.keys():
                    disk_info['PARTS'] = dev_pasts[disk_info['DEVNAME']]
                # 过滤系统盘
                if disk_info['DE_NO'] in skip_device_number:
                    continue
                if len([part_info for part_info in disk_info['PARTS'] if part_info['DE_NO'] in skip_device_number]) != 0:
                    continue
                disk_list.append(disk_info)
        except pyudev.device.DeviceNotFoundAtPathError as e:
            # XXX: 在for part in parts 和 for disk in disks中会偶尔出现如下异常
            # No device at '/sys/devices/virtual/block/dm-2'
            # No device at '/sys/devices/pci0000:00/0000:00:06.0/virtio3/host2/target2:0:0/2:0:0:3/block/sdb/sdb1'
            # 应该是在分区的过程中内核磁盘信息没有及时同步导致，或期间正在删除smartcache导致
            # 因为不影响执行结果，因此此处不处理
            return -1, e
        except Exception as e:
            return -2, e
        return 0, disk_list

    def create_multi_part(self, devinfo, partition_count, part_time):
        per_part_size = int(devinfo['SIZE'])/int(partition_count)
        if per_part_size < 10*1000*1000*1000/512:
            return -1, "Per part size will be lt 10G, please reduce the number of partitions"

        disk_parts = []
        for i in range(partition_count):
            time.sleep(part_time)
            e, new_part = self.create_part(devinfo, per_part_size)
            if e: return e, new_part
            disk_parts.append(new_part)
        return 0, disk_parts

    # 创建新的磁盘分区
    def create_part(self, devinfo, size):
        diskparted = DiskParted(devinfo['DEVNAME'])
        diskparted.post_init()

        # 开始创建分区
        e, part = diskparted.create_disk_part_by_size(size)
        # 当连续分区的时候，可能导致分区失败，这种情况的失败需要单独处理
        if e and part.startswith('Warning: WARNING: the kernel failed to re-read the partition table on'):
            return -1, "Create disk part failed, please try again"
        if e: return e, part

        part_dev  = {}
        part_dev['size']  = str(int(part['length']) * diskparted.sector / 512)
        part_dev['path']  = part['path']

        if self.__nonexist_sleep(part['path']):
            return -1, "Create parted error"
        return 0, part_dev

    # 延迟判存在
    def __nonexist_sleep(self, path):
        flag = False
        # 判断盘符路径是否存在
        for i in range(20):
            if os.path.exists(path):
                flag = True
                break
            time.sleep(0.5)
        if flag == False:
            return 1

        # 判断udev是否存在
        for i in range(20):
            try:
                context = pyudev.Context()
                parts = context.list_devices(subsystem='block', DEVTYPE='partition')
                part_lable = []
                for part in parts:
                    lable = part['DEVNAME']
                    if not lable.startswith("/dev/"):
                        lable = "/dev/%s" % lable
                    part_lable.append(lable)
                if path in part_lable:
                    flag = True
                    break
            except:
                pass
            time.sleep(0.5)
        if flag == False:
            return 1
        return 0

    # 初始化磁盘
    def disk_init(self, params={}):
        devinfo         = params['devinfo']
        partition_count = params['partition_count']
        if params.has_key("part_time"):
            part_time = params['part_time']
        else:
            part_time = 1

        # 1. 清除磁盘上的分区
        diskparted = DiskParted(devinfo['DEVNAME'])
        e, res = diskparted.mklabel()
        if e: return e, res
        diskparted.post_init()

        # 2. 向磁盘写盘头信息
        header = {}
        header['uuid'] = str(uuid.uuid1())
        e, res = DiskHeader(devinfo['DEVNAME']).set_header_data(header)
        if e: return e, res

        # 3. 磁盘分区
        e, disk_parts = self.create_multi_part(devinfo, partition_count, part_time)
        if e: return e, disk_parts

        return 0, ''
