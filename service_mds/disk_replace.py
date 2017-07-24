# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class DiskReplaceMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.DISK_REPLACE_REQUEST

    def INIT(self, request):
        self.response     = MakeResponse(msg_mds.DISK_REPLACE_RESPONSE, request)
        self.request      = request
        self.request_body = request.body.Extensions[msg_mds.disk_replace_request]

        if g.is_ready == False:
            self.response.rc.retcode = msg_mds.RC_MDS_SERVICE_IS_NOT_READY
            self.response.rc.message = "MDS service is not ready"
            self.SendResponse(self.response)
            return MS_FINISH

        # 获取被替换磁盘信息
        old_disk_info = common.GetDiskInfoByName(self.request_body.disk_name)
        if old_disk_info == None:
            self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
            self.response.rc.message = "Disk %s is not exist" % (self.request_body.disk_name)
            self.SendResponse(self.response)
            return MS_FINISH

        self.ces_addr  = None
        self.dev_name  = None

        # 检查dev_name参数
        if self.request_body.dev_name.startswith("/dev"):
            # 检查所有raid, 如果有盘的盘符为dev_name, 则提示使用ces操作
            for rdisk in g.raid_disk_list_all.raid_disk_infos:
                if rdisk.HasField('dev_name') and rdisk.dev_name == self.request_body.dev_name:
                    self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                    self.response.rc.message = "Please use Raid.Addr as params"
                    self.SendResponse(self.response)
                    return MS_FINISH
            self.dev_name  = self.request_body.dev_name
        else:
            # ces
            items = self.request_body.dev_name.split(":")
            if len(items) not in [3,4]:
                self.response.rc.retcode = msg_mds.RC_MDS_ERROR_PARAMS
                self.response.rc.message = "param 'Raid.Addr' is ilegal"
                self.SendResponse(self.response)
                return MS_FINISH
            self.ces_addr = self.request_body.dev_name

        # 检查新磁盘是否已经初始化过了
        for disk in g.disk_list.disk_infos:
            # 以盘符查找
            if self.dev_name != None and disk.dev_name == self.dev_name:
                self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
                self.response.rc.message = "Disk %s already initialized" % self.dev_name
                self.SendResponse(self.response)
                return MS_FINISH
            # 以ces查找
            elif disk.HasField('raid_disk_info'):
                ces_addr = "%s:%s:%s" % (disk.raid_disk_info.ctl, disk.raid_disk_info.eid, disk.raid_disk_info.slot)
                if ces_addr == self.ces_addr:
                    self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
                    self.response.rc.message = "Disk %s already initialized" % self.ces_addr
                    self.SendResponse(self.response)
                    return MS_FINISH
    
        self.raid_disk_info = None
        # 检查目标盘是否存在
        # 以盘符查找
        if self.dev_name != None:
            disk = [disk for disk in g.disk_list_all.disk_infos if disk.dev_name == self.dev_name]
            if len(disk) == 0:
                self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
                self.response.rc.message = "Disk %s not exist" % self.dev_name
                self.SendResponse(self.response)
                return MS_FINISH
            if disk[0].HasField('raid_disk_info'):
                self.raid_disk_info = msg_pds.RaidDiskInfo()
                self.raid_disk_info.CopyFrom(disk[0].raid_disk_info)
        # 以ces查找
        if self.ces_addr != None:
            raid_disk = []
            for disk in g.raid_disk_list_all.raid_disk_infos:
                if "%s:%s:%s" % (disk.ctl, disk.eid, disk.slot) == self.ces_addr:
                    raid_disk.append(disk)
            if len(raid_disk) == 0:
                self.response.rc.retcode = msg_mds.RC_MDS_DISK_NOT_EXIST
                self.response.rc.message = "Disk %s not exist" % self.ces_addr
                self.SendResponse(self.response)
                return MS_FINISH
            if raid_disk[0].HasField('dev_name') and raid_disk[0].dev_name != "": 
                # 如果raid有盘符, 则直接通过盘符初始化, 不再通过ces_addr
                self.dev_name = raid_disk[0].dev_name
                self.ces_addr = None
            self.raid_disk_info = msg_pds.RaidDiskInfo()
            self.raid_disk_info = raid_disk[0]
            if raid_disk[0].drive_type.lower() == "ssd":
                disk_type = msg_pds.DISK_TYPE_SSD
            else:
                disk_type = msg_pds.DISK_TYPE_HDD

            # ces类型 检查新磁盘和被替换磁盘类型是否一致
            if disk_type != old_disk_info.disk_type:
                self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
                self.response.rc.message = "Disk '%s' type must be the same as '%s'" % (self.request_body.dev_name, self.request_body.disk_name)
                self.SendResponse(self.response)
                return MS_FINISH

        # 检查新磁盘大小
        if self.raid_disk_info.size < old_disk_info.size:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Disk '%s' size must be greater than or equal to '%s'" % (self.request_body.dev_name, self.request_body.disk_name)
            self.SendResponse(self.response)
            return MS_FINISH

        lun_infos = common.GetLunInfoByDiskID(old_disk_info.header.uuid)
        if old_disk_info.disk_type == msg_pds.DISK_TYPE_SSD:
            pool_infos = common.GetPoolInfoByDiskID(old_disk_info.header.uuid)
            for pool_info in pool_infos:
                pool_lun_infos = common.GetLunInfoByPoolID(pool_info.pool_id)
                lun_infos.extend(pool_lun_infos)

        # 检查是否被smartcache盘引用
        smartcache_list = [lun_info for lun_info in lun_infos if lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE]
        if len(smartcache_list) > 0:
            self.response.rc.retcode = msg_mds.RC_MDS_NOT_SUPPORT
            self.response.rc.message = "Disk '%s' contains smartcache lun, not support" % (self.request_body.disk_name)
            self.SendResponse(self.response)
            return MS_FINISH

        # 整理换盘需要的信息
        self.old_disk_info = {}
        self.old_disk_info['disk_id']   = old_disk_info.header.uuid
        self.old_disk_info['disk_name'] = self.request_body.disk_name
        self.old_disk_info['disk_type'] = old_disk_info.disk_type
        self.old_disk_info['partition_count'] = len(old_disk_info.diskparts)
        if old_disk_info.disk_type == msg_pds.DISK_TYPE_SSD:
            self.old_disk_info['pools'] = []
            for pool_info in pool_infos:
                pool = {}
                pool['pool_name']   = pool_info.pool_name
                pool['size']        = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].size
                pool['max_size']    = pool_info.Extensions[msg_mds.ext_poolinfo_pool_export_info].max_size
                pool['disk_part']   = pool_info.pool_disk_infos[0].disk_part
                pool['is_variable'] = pool_info.is_variable
                if pool_info.HasField("extent"):
                    pool['extent'] = pool_info.extent
                if pool_info.HasField("bucket"):
                    pool['bucket'] = pool_info.bucket
                if pool_info.HasField("sippet"):
                    pool['sippet'] = pool_info.sippet
                self.old_disk_info['pools'].append(pool)

        self.old_disk_info['luns'] = []
        for lun_info in lun_infos:
            lun = {}
            lun['lun_name']     = lun_info.lun_name
            lun['lun_type']     = lun_info.lun_type
            lun['group_name']   = lun_info.group_name
            lun['config_state'] = lun_info.config_state
            if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                basedisk_info  = common.GetBaseDiskInfoById(lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id])
                data_part_info = common.GetDiskPartByID(basedisk_info.disk_id, basedisk_info.disk_part)
                data_disk_name = "%sp%s" % (self.request_body.disk_name, data_part_info.disk_part)
                lun['data_disk_name'] = data_disk_name

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                palraw_info    = common.GetPalRawInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palraw_id])
                data_part_info = common.GetDiskPartByID(palraw_info.disk_id, palraw_info.disk_part)
                data_disk_name = "%sp%s" % (self.request_body.disk_name, data_part_info.disk_part)
                lun['data_disk_name'] = data_disk_name

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                palcache_info  = common.GetPalCacheInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palcache_id])
                data_disk_info = common.GetDiskInfoByID(palcache_info.disk_id)
                data_part_info = common.GetDiskPartByID(palcache_info.disk_id, palcache_info.disk_part)
                data_disk_name = "%sp%s" % (data_disk_info.disk_name, data_part_info.disk_part)
                pool_info      = common.GetPoolInfoById(palcache_info.pool_id)
                lun['pool_name']      = pool_info.pool_name
                lun['data_disk_name'] = data_disk_name

            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
                palpmt_info = common.GetPalPmtInfoById(lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id])
                size        = palpmt_info.size
                pool_info   = common.GetPoolInfoById(palpmt_info.pool_id)
                lun['pool_name'] = pool_info.pool_name
                lun['lun_size']  = size

            self.old_disk_info['luns'].append(lun)

        if len(self.old_disk_info['luns']) > 0:
            self.lun_offline_flag = 0
            return self.send_lun_offline_request()

        if self.old_disk_info['disk_type'] == msg_pds.DISK_TYPE_SSD and len(self.old_disk_info['pools']) > 0:
            self.pool_drop_flag = 0
            return self.send_pool_drop_request()

        mds_request = MakeRequest(msg_mds.DISK_DROP_REQUEST)
        mds_request.body.Extensions[msg_mds.disk_drop_request].disk_name = self.request_body.disk_name
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_DiskDrop)
        return MS_CONTINUE

    def send_lun_offline_request(self):
        lun_info = self.old_disk_info['luns'][self.lun_offline_flag]
        if lun_info['config_state'] == True:
            mds_request = MakeRequest(msg_mds.LUN_OFFLINE_REQUEST)
            mds_request.body.Extensions[msg_mds.lun_offline_request].lun_name = "%s_%s" % (g.node_info.node_name, lun_info['lun_name'])
            self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_LunOffline)
            return MS_CONTINUE
        
        return self.Entry_LunOffline(None)

    def Entry_LunOffline(self, response):
        if response and response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        
        if self.lun_offline_flag < len(self.old_disk_info['luns'])-1:
            self.lun_offline_flag += 1
            return self.send_lun_offline_request()

        self.lun_drop_flag = 0
        return self.send_lun_drop_request()

    def send_lun_drop_request(self):
        lun_info = self.old_disk_info['luns'][self.lun_drop_flag]
        mds_request = MakeRequest(msg_mds.LUN_DROP_REQUEST)
        mds_request.body.Extensions[msg_mds.lun_drop_request].lun_name = "%s_%s" % (g.node_info.node_name, lun_info['lun_name'])
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_Lundrop)
        return MS_CONTINUE

    def Entry_Lundrop(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.lun_drop_flag < len(self.old_disk_info['luns'])-1:
            self.lun_drop_flag += 1
            return self.send_lun_drop_request()

        if self.old_disk_info['disk_type'] == msg_pds.DISK_TYPE_SSD:
            self.pool_drop_flag = 0
            return self.send_pool_drop_request()

        mds_request = MakeRequest(msg_mds.DISK_DROP_REQUEST)
        mds_request.body.Extensions[msg_mds.disk_drop_request].disk_name = self.request_body.disk_name
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_DiskDrop)
        return MS_CONTINUE

    def Entry_DiskDrop(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        mds_request = MakeRequest(msg_mds.DISK_ADD_REQUEST)
        mds_request.body.Extensions[msg_mds.disk_add_request].dev_name = self.request_body.dev_name
        mds_request.body.Extensions[msg_mds.disk_add_request].partition_count = self.old_disk_info['partition_count']
        mds_request.body.Extensions[msg_mds.disk_add_request].disk_name = self.request_body.disk_name
        if self.request_body.dev_name.startswith("/dev"):
            mds_request.body.Extensions[msg_mds.disk_add_request].disk_type = self.old_disk_info['disk_type']

        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_DiskAdd)
        return MS_CONTINUE

    def Entry_DiskAdd(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.old_disk_info['disk_type'] == msg_pds.DISK_TYPE_SSD and len(self.old_disk_info['pools']) > 0:
            self.pool_add_flag = 0
            return self.send_pool_add_request()

        if self.old_disk_info['disk_type'] == msg_pds.DISK_TYPE_HDD and len(self.old_disk_info['luns']) > 0:
            self.lun_add_flag = 0
            return self.send_lun_add_request()

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def send_pool_drop_request(self):
        old_pool_info = self.old_disk_info['pools'][self.pool_drop_flag]
        mds_request = MakeRequest(msg_mds.POOL_DROP_REQUEST)
        mds_request.body.Extensions[msg_mds.pool_drop_request].pool_name = old_pool_info['pool_name']
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_PoolDrop)
        return MS_CONTINUE

    def Entry_PoolDrop(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.pool_drop_flag < len(self.old_disk_info['pools'])-1:
            self.pool_drop_flag += 1
            return self.send_pool_drop_request()

        mds_request = MakeRequest(msg_mds.DISK_DROP_REQUEST)
        mds_request.body.Extensions[msg_mds.disk_drop_request].disk_name = self.request_body.disk_name
        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_DiskDrop)
        return MS_CONTINUE

    def send_pool_add_request(self):
        old_pool_info = self.old_disk_info['pools'][self.pool_add_flag]
        disk_part_name = "%sp%s" % (self.request_body.disk_name, old_pool_info['disk_part'])

        mds_request = MakeRequest(msg_mds.POOL_ADD_REQUEST)
        mds_request.body.Extensions[msg_mds.pool_add_request].disk_names.append(disk_part_name)
        mds_request.body.Extensions[msg_mds.pool_add_request].pool_name = old_pool_info['pool_name']
        if old_pool_info['is_variable'] == True:
            request.body.Extensions[msg_mds.pool_add_request].is_variable = True
        if old_pool_info.has_key("extent"):
            request.body.Extensions[msg_mds.pool_add_request].extent = old_pool_info['extent']
        if old_pool_info.has_key("bucket"):
            request.body.Extensions[msg_mds.pool_add_request].bucket = old_pool_info['bucket']
        if old_pool_info.has_key("sippet"):
            request.body.Extensions[msg_mds.pool_add_request].sippet = old_pool_info['sippet']

        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_PoolAdd)
        return MS_CONTINUE

    def Entry_PoolAdd(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH
        
        if self.pool_add_flag < len(self.old_disk_info['pools'])-1:
            self.pool_add_flag += 1
            return self.send_pool_add_request()

        self.pool_resize_flag = 0
        return self.send_pool_resize_request()

    def send_pool_resize_request(self):
        old_pool_info = self.old_disk_info['pools'][self.pool_resize_flag]

        if old_pool_info['size'] < old_pool_info['max_size']:
            mds_request = MakeRequest(msg_mds.POOL_RESIZE_REQUEST)
            mds_request.body.Extensions[msg_mds.pool_resize_request].pool_name = old_pool_info['pool_name']
            mds_request.body.Extensions[msg_mds.pool_resize_request].size      = (old_pool_info['size']*512)>>30
            self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_PoolResize)
            return MS_CONTINUE

        return self.Entry_PoolResize(None)

    def Entry_PoolResize(self, response):
        if response and response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.pool_resize_flag < len(self.old_disk_info['pools'])-1:
            self.pool_resize_flag += 1
            return self.send_pool_resize_request()

        if len(self.old_disk_info['luns']) > 0:
            self.lun_add_flag = 0
            return self.send_lun_add_request()

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def send_lun_add_request(self):
        lun_info = self.old_disk_info['luns'][self.lun_add_flag]

        mds_request = MakeRequest(msg_mds.LUN_ADD_REQUEST)
        mds_request_body = mds_request.body.Extensions[msg_mds.lun_add_request]
        group_name = lun_info['group_name'][0]
        mds_request_body.group_name = group_name
        mds_request_body.lun_type = lun_info['lun_type']
        mds_request_body.lun_name = lun_info['lun_name']

        if lun_info['lun_type']   == msg_pds.LUN_TYPE_BASEDISK:
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_basedisk].data_disk_name = lun_info['data_disk_name']
        elif lun_info['lun_type'] == msg_pds.LUN_TYPE_PALRAW:
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palraw].data_disk_name = lun_info['data_disk_name']
        elif lun_info['lun_type'] == msg_pds.LUN_TYPE_PALCACHE:
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].data_disk_name = lun_info['data_disk_name']
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].pool_name      = lun_info['pool_name']
        elif lun_info['lun_type'] == msg_pds.LUN_TYPE_PALPMT:
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].pool_name = lun_info['pool_name']
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].size      = (lun_info['lun_size']*512)>>30

        self.SendRequest(g.listen_ip, g.listen_port, mds_request, self.Entry_LunAdd)

        return MS_CONTINUE

    def Entry_LunAdd(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            self.response.rc.CopyFrom(response.rc)
            self.SendResponse(self.response)
            return MS_FINISH

        if self.lun_add_flag < len(self.old_disk_info['luns'])-1:
            self.lun_add_flag += 1
            return self.send_lun_add_request()

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH
