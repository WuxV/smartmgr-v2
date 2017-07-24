#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import parted, time
from pdsframe import *
from service_ios.base.cmdlist import *

PARTED_START_SECTOR = 4096

class DiskParted:
    def __init__(self, devpath):
        self.devpath = devpath

    def post_init(self):
        self.device    = parted.Device(self.devpath)
        self.disk      = parted.Disk(self.device)
        self.type      = self.disk.type
        self.sector    = int(self.device.sectorSize)
        # self.grainSize = self.disk.partitionAlignment.intersect(self.disk.device.optimumAlignment).grainSize

        # 使用统一的分区对齐值
        self.grainSize = PARTED_START_SECTOR

    def docmd(self,args, log = True):
        return command(" ".join(args))

    # 初始化为gpt类型，
    # XXX:该调用会将磁盘上的分区信息全部丢失
    def mklabel(self, params={}):
        e, res = self.docmd([PARTED, '-s', self.devpath, 'mklabel', 'gpt'], log=True)
        if e: return e, res
        return 0, ''

    # 对齐开始位置
    def update_start_pos(self, start_pos):
        m = int(start_pos) % self.grainSize
        n = int(start_pos) / self.grainSize
        if m != 0:
            return int((n+1)*self.grainSize)
        return int(start_pos)

    # 获取磁盘的整个分段情况
    def list_disk_sep(self, params={}):
        e, frees = self.list_disk_frees()
        e, parts = self.list_disk_parts()

        seps = []
        seps.extend(frees)
        seps.extend(parts)
        seps = sorted(seps, key=lambda sep: int(sep['start']))

        # 过滤掉小于1G的分区
        if not params.has_key('all') or params['all'] == Flase:
            sep_new = []
            for sep in seps:
                if int(sep['length']) >= 1*1000*1000*1000/self.sector:
                    sep_new.append(sep)
            return sep_new
        else:
            return seps

    # 获取剩余空间列表
    def list_disk_frees(self, params={}):
        regs = self.disk.getFreeSpaceRegions()
        frees = []
        for reg in regs:
            free = {}
            free["start"]  = str(reg.start)
            free["end"]    = str(reg.end)
            free["length"] = str(reg.length)
            frees.append(free)
        return (0, frees)

    # 获取分区列表
    def list_disk_parts(self, params={}):
        parts = []
        for partition in self.disk.partitions:
            part = {}
            geometry           = partition.geometry
            part["path"]       = partition.path
            part["disk_part"] = partition.number
            part["start"]      = str(geometry.start)
            part["end"]        = str(geometry.end)
            part["length"]     = str(geometry.length)
            parts.append(part)
        return (0, parts)

    # 根据大小创建分区
    # size 传入的大小是512单位的扇区数
    def create_disk_part_by_size(self, size):
        e, parts_old = self.list_disk_parts()
        if e: return e, parts_old
        e, frees = self.list_disk_frees()
        match = None
        for free in frees:
            # 小于1G的空间忽略
            if free['length'] < 1*1000*1000*1000/self.sector:
                continue
            start_pos = self.update_start_pos(free['start'])

            # 满足条件有2种情况
            # 1. 剩余空间大于需要的空间
            # 2. 剩余空间小于需要空间100M以内也接受，这个是由于磁盘真是可用空间小于标称，其已经2048对齐的消耗
            #    且9271的卡的强制容量比实际的大

            length = int(free['end']) - int(start_pos) + 1

            # 将length转换为512大小的扇区
            length = length * self.sector/512
            
            if  length >= int(size):
                match = {}
                match['start'] = start_pos
                match['end']   = size*512/self.sector + start_pos - 1
                break
            elif size - length < 100*1048576/512:
                match = {}
                match['start'] = start_pos
                match['end']   = free['end']
                break

        if match == None:
            return -1, "No enouth space"

        e, res = self.create_disk_part(params={'type':'primary', 'start':match['start'], 'end':match['end']})
        if e: return e, res
        # 通过再次遍历，获取创建出来分区的信息
        self.post_init()
        e, parts_new = self.list_disk_parts()
        if e: return e, parts_new
        for part in parts_new:
            if part not in parts_old:
                return 0, part
        return -1, "Create part error"

    # 创建分区
    def create_disk_part(self, params={}):
        # XXX:GPT支持128个主分区足够使用，因此此处仅支持primary
        assert( params.has_key('type') and params['type'] in ['primary'] )
        assert( params.has_key('start') and str(params['start']).isdigit() )
        assert( params.has_key('end') and str(params['end']).isdigit() )

        start = params['start']
        end   = params['end']
        type  = params['type']

        if self.type != "gpt":
            e, res = self.mklable()
            if e: return e, res
        e, res = self.docmd([PARTED, '-s', self.devpath, 'mkpart', 'primary', str(start)+'s', str(end)+'s'], log=True)
        if e: return e, res
        self.docmd([PARTPROBE, self.devpath], log=True)
        time.sleep(1)
        return 0, ''

    # 删除分区
    def delete_disk_part(self, disk_part):
        assert( disk_part != None and str(disk_part).isdigit() )

        e, parts = self.list_disk_parts()
        if e: return e, parts

        for part in parts:
            if str(part['disk_part']) == str(disk_part):
                return self.docmd([PARTED, '-s', self.devpath, 'rm', str(disk_part)], log=True)
        return -1, 'part \'%s\' not exist' % disk_part
