#encoding:utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
import json, base64, hashlib, struct

PARTED_START_SECTOR = 4096

# 一个扇区的大小
SECTOR_SIZE     = 512
# 使用的最大扇区数
MAX_SECTOR      = 100
# 存储盘头信息的总字节数, 含长度定义段
MAX_LEN         = SECTOR_SIZE*MAX_SECTOR
# 存储数据长度段的长度,按一个整形的存储空间存储数据长度
LEN_PKSIZE      = len(struct.pack('I', 0))
# 由数据长度段可表示的最大信息长度的字节数
CONTENT_MAX_LEN = 2**(8*LEN_PKSIZE)
# 一个md5值的字符串长度
MD5_SIZE        = len(hashlib.md5('Hi').hexdigest())
# 盘头信息的起始扇区
START_SECTOR    = 128
# 盘头信息的结束扇区
END_SECTOR      = START_SECTOR+MAX_SECTOR

# FIXME:极限边界 [34-4096), 4096是分区的时候保留的扇区数结尾, 34是gpt类型分区表的扇区起始
assert(START_SECTOR>=34 and END_SECTOR<PARTED_START_SECTOR)

class DiskHeader:
    def __init__(self, devpath):
        self.devpath = devpath

    # 编码盘头信息
    def encode_header_data(self, header):
        data = {}
        data['version'] = "1"           # 盘头信息版本号
        data['system']  = "pbdata"      # 盘头产生系统
        data['header']  = header

        # 简单2次base64编码加密
        data = base64.encodestring(base64.encodestring(json.dumps(data)))

        # 创建md5校验
        md5sum = hashlib.md5(data).hexdigest().upper()

        # 在消息体最前加入md5值
        data = md5sum+data

        # 按512补"0"对齐，因为在度数据到磁盘中最小单位512，如果不用"0"填充，会导致垃圾数据读入
        if len(data)%SECTOR_SIZE != 0:
            data += "0"*((len(data)/SECTOR_SIZE+1)*SECTOR_SIZE-len(data))

        if len(data) > CONTENT_MAX_LEN or len(data+struct.pack('I', 0)) > MAX_LEN:
            return -1, "Disk head information's len %s exceeds the maximum length limit %s or maximum content limit %s" %  \
                (len(data), MAX_LEN, CONTENT_MAX_LEN)

        data = struct.pack('I', len(data))+data
        return 0, data

    # 解码盘头信息
    def decode_header_data(self, data):
        if len(data) < LEN_PKSIZE:
            return -1, "Miss data from len"

        # 获取数据总长度
        dataLen = struct.unpack('I', data[:LEN_PKSIZE])[0]

        if len(data)-LEN_PKSIZE < dataLen:
            return -1, "Miss data"

        # 获取md5校验和
        md5sum  = data[LEN_PKSIZE:LEN_PKSIZE+MD5_SIZE]
        # 获取数据
        data    = data[LEN_PKSIZE+MD5_SIZE:dataLen].rstrip('0')

        if hashlib.md5(data).hexdigest().upper() != md5sum:
            return -1, "Disk head information does not exist, or damaged"

        data = json.loads(base64.decodestring(base64.decodestring(data)))
        return 0, data['header']

    # 获取盘头信息
    def get_header_data(self):
        try:
            disk = open(self.devpath, 'rb')
            disk.seek(SECTOR_SIZE*START_SECTOR)
            data = disk.read((END_SECTOR-START_SECTOR)*SECTOR_SIZE)
            disk.close()
            return self.decode_header_data(data)
        except Exception as e:
            return -2, str(e)

    # 设置盘头信息
    def set_header_data(self, header):
        try:
            e, data = self.encode_header_data(header)
            if e: return e, data
            disk = open(self.devpath, 'rb+')
            disk.seek(SECTOR_SIZE*START_SECTOR)
            disk.write(data)
            disk.close()
            return 0, ''
        except Exception as e:
            return -2, e

    def init_header(self):
        header = {}
        header['uuid'] = uuid.uuid1()
        return header
