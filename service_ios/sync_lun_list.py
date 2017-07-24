# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time, os
from pdsframe import *
from service_ios import g
from service_ios import common
import message.pds_pb2 as msg_pds
import message.ios_pb2 as msg_ios
import message.mds_pb2 as msg_mds
from service_ios.base.apismartcache import APISmartCache
from service_ios.base.apismartscsi import APISmartScsi
from service_ios.base.apidisk import APIDisk
from service_ios.base import apipal

class SyncLunListMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 30

    def TIMEOUT(self):
        return self.FinishMachine()

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH

        if g.platform['sys_mode'] == "database":
            return MS_FINISH

        if int(time.time()) - g.last_modify_time < 60:
            return MS_FINISH

        e, self.disk_list = APIDisk().get_disk_list()
        if e: 
            logger.run.error("Get disk list error")
            return MS_FINISH

        # 获取节点信息
        mds_request = MakeRequest(msg_mds.GET_NODE_INFO_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetNodeInfo)
        return MS_CONTINUE

    def Entry_GetNodeInfo(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.debug("Get Node info failed %s:%s" % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.node_name = response.body.Extensions[msg_mds.get_node_info_response].node_info.node_name

        mds_request = MakeRequest(msg_mds.GET_POOL_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetPoolList)
        return MS_CONTINUE

    def Entry_GetPoolList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get pool list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.pool_infos = response.body.Extensions[msg_mds.get_pool_list_response].pool_infos

        mds_request = MakeRequest(msg_mds.GET_BASEDISK_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetBaseDiskList)
        return MS_CONTINUE

    def Entry_GetBaseDiskList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get basedisk list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.basedisk_infos = response.body.Extensions[msg_mds.get_basedisk_list_response].basedisk_infos

        mds_request = MakeRequest(msg_mds.GET_BASEDEV_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetBaseDevList)
        return MS_CONTINUE

    def Entry_GetBaseDevList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get basedev list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.basedev_infos = response.body.Extensions[msg_mds.get_basedev_list_response].basedev_infos

        mds_request = MakeRequest(msg_mds.GET_PALCACHE_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetPalCacheList)
        return MS_CONTINUE

    def Entry_GetPalCacheList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get palcache list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.palcache_infos = response.body.Extensions[msg_mds.get_palcache_list_response].palcache_infos

        mds_request = MakeRequest(msg_mds.GET_PALRAW_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetPalRawList)
        return MS_CONTINUE

    def Entry_GetPalRawList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get palraw list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.palraw_infos = response.body.Extensions[msg_mds.get_palraw_list_response].palraw_infos

        mds_request = MakeRequest(msg_mds.GET_PALPMT_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetPalPmtList)
        return MS_CONTINUE

    def Entry_GetPalPmtList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get palpmt list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.palpmt_infos = response.body.Extensions[msg_mds.get_palpmt_list_response].palpmt_infos

        mds_request = MakeRequest(msg_mds.GET_SMARTCACHE_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetSmartCacheList)
        return MS_CONTINUE

    def Entry_GetSmartCacheList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get smartcache list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.smartcache_infos = response.body.Extensions[msg_mds.get_smartcache_list_response].smartcache_infos

        mds_request = MakeRequest(msg_mds.GET_LUN_GROUP_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetLunGroupList)
        return MS_CONTINUE

    def Entry_GetLunGroupList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get lun group list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        self.group_infos = response.body.Extensions[msg_mds.get_lun_group_list_response].nsnode_infos
        
        mds_request = MakeRequest(msg_mds.GET_LUN_LIST_REQUEST)
        self.SendRequest(g.mds_service.listen_ip, g.mds_service.listen_port, mds_request, self.Entry_GetLunList)
        return MS_CONTINUE


    def Entry_GetLunList(self, response):
        if response.rc.retcode != msg_pds.RC_SUCCESS:
            logger.run.error('Get lun list failed %s:%s' % (response.rc.retcode, response.rc.message))
            return self.FinishMachine()

        if int(time.time()) - g.last_modify_time < 30:
            return MS_FINISH

        self.lun_infos = response.body.Extensions[msg_mds.get_lun_list_response].lun_infos
        
        # 同步4种lun类型的基础资源
        self.PrepareBaseDisk()
        self.PrepareBaseDev()
        self.PrepareSmartCache()
        self.PreparePal()

        self.load_groups()

        return self.SyncLun()

    def PrepareBaseDisk(self):
        pass

    def PrepareBaseDev(self):
        pass

    def PrepareSmartCache(self):
        smartcache_infos = {}
        for smartcache_info in self.smartcache_infos:
            smartcache_infos[smartcache_info.smartcache_id] = smartcache_info

        e, smartcache_list = APISmartCache().list()
        if e: 
            logger.run.error("Get smartcache list failed:%s", smartcache_list)
            return self.FinishMachine()

        self.todo_load_smartcache = {}
        for smartcache_info in self.smartcache_infos:
            if smartcache_info.smartcache_id not in smartcache_list.keys():
                self.todo_load_smartcache[smartcache_info.smartcache_id] = smartcache_info

        if len(self.todo_load_smartcache.keys()) == 0:
            return

        for smartcache_info in self.todo_load_smartcache.values():
            params = { \
                'smartcache_id':smartcache_info.smartcache_id,
                "cache_disk_id":smartcache_info.cache_disk_id, 
                'cache_disk_part':smartcache_info.cache_disk_part, 
                "data_disk_id":smartcache_info.data_disk_id, 
                'data_disk_part':smartcache_info.data_disk_part, 
                }
            self.LongWork(self.load_smartcache, params, self.Entry_LoadSmartCache, 20)
        return MS_CONTINUE

    def load_smartcache(self, params):
        cache_dev = common.GetPartInfo(params['cache_disk_id'], params['cache_disk_part'], self.disk_list)
        if cache_dev == None:
            logger.run.error("Cann't find cache dev by uuid:%s, index:%s" % (params['cache_disk_id'], params['cache_disk_part']))
            return params, ""

        data_dev = common.GetPartInfo(params['data_disk_id'], params['data_disk_part'], self.disk_list)
        if data_dev == None:
            logger.run.error("Cann't find data dev by uuid:%s, index:%s" % (params['data_disk_id'], params['data_disk_part']))
            return params, ""

        logger.run.info("Start load smartcache '%s'" % (",".join(["%s:%s" % (k, v) for k, v in params.items()])))

        e, res = APISmartCache().load({'cache_dev':cache_dev['DEVNAME'], 'data_dev':data_dev['DEVNAME']})
        result = False
        if e:
            print res
            logger.run.error("Load cache '%s' failed, e:%s, res:%s" % (",".join(["%s:%s" % (k, v) for k, v in params.items()]), e, res))
            result = False
        else:
            result = True
        return params, result

    def Entry_LoadSmartCache(self, res):
        params, result = res
        logger.run.info("Load smartcache '%s' result:%s" % (",".join(["%s:%s" % (k, v) for k, v in params.items()]), result))

        self.todo_load_smartcache.pop(params['smartcache_id'])
        if len(self.todo_load_smartcache.keys()) == 0:
            return
        return MS_CONTINUE

    def PreparePal(self):
        # 在同步pal的时候, 需要先刷新target-id, 以及检查模块
        pal_ids = []
        pal_ids.extend([palcache_info.pal_id for palcache_info in self.palcache_infos])
        pal_ids.extend([palraw_info.pal_id   for palraw_info   in self.palraw_infos])
        pal_ids.extend([palpmt_info.pal_id   for palpmt_info   in self.palpmt_infos])
        common.CheckDriverConfigure(pal_ids)

        palpool   = apipal.Pool()
        paldisk   = apipal.Disk()
        paltarget = apipal.Target()

        # pal目前认到的磁盘
        e, pal_disks = paldisk.get_disk_list()
        if e:
            logger.run.error("Get pal disk list failed:%s" % pal_disks)
            return
        pal_disks_path_name = [disk.path_name() for disk in pal_disks]

        # pal目前认到的target
        e, pal_targets = paltarget.get_target_list()
        if e:
            logger.run.error("Get pal target list failed:%s" % pal_targets)
            return
        pal_targets_name = [target.name() for target in pal_targets]

        # pal目前认到的pool
        e, pal_pools = palpool.get_pool_list()
        if e:
            logger.run.error("Get pal pool list failed:%s" % pal_pools)
            return
        pal_pools_name = [pool.name() for pool in pal_pools]

        pool_id_to_info      = {}
        todo_load_pool_disk  = []
        todo_load_cache_disk = []
        todo_load_raw_disk   = []
        todo_del_target      = []
        todo_del_pool        = []

        # 获取需要删除的垃圾target
        cfg_target_name = []
        cfg_target_name.extend([palcache_info.palcache_name for palcache_info in self.palcache_infos])
        cfg_target_name.extend([palraw_info.palraw_name     for palraw_info   in self.palraw_infos])
        cfg_target_name.extend([palpmt_info.palpmt_name     for palpmt_info   in self.palpmt_infos])
        for target_name in pal_targets_name:
            if target_name not in cfg_target_name:
                todo_del_target.append(target_name)

        # 获取需要删除的垃圾pool
        for pool_name in pal_pools_name:
            if pool_name not in [pool_info.pool_name for pool_info in self.pool_infos]:
                todo_del_pool.append(pool_name)

        # 清理垃圾target
        for target_name in todo_del_target:
            logger.run.info("Auto del target %s" % target_name)
            e, res = paltarget.del_target(target_name)
            if e: logger.run.warning("Auto del target failed :%s" % res)

        # 清理垃圾pool
        for pool_name in todo_del_pool:
            logger.run.info("Auto del pool %s" % pool_name)
            e, res = palpool.del_pool(pool_name)
            if e: logger.run.warning("Auto del pool failed :%s" % res)

        # 获取pool没有load的盘
        for pool_info in self.pool_infos:
            pool_id_to_info[pool_info.pool_id] = pool_info
            assert(len(pool_info.pool_disk_infos) == 1)
            # 如果pool已经is_invalid or is_disable则不再尝试load pool的盘
            if pool_info.is_invalid == True or pool_info.is_disable == True:
                logger.run.info("Skip check pool %s disk for is invalid or is disable" % pool_info.pool_name)
                continue
            pool_disk_info = pool_info.pool_disk_infos[0]
            part           = common.GetPartInfo(pool_disk_info.disk_id, pool_disk_info.disk_part, self.disk_list)
            if part == None:
                logger.run.warning("Pal pool %s disk miss" % pool_info.pool_name)
                continue
            if part['DEVNAME'] not in pal_disks_path_name:
                todo_load_pool_disk.append(part['DEVNAME'])

        # 获取palcache没有load的盘
        for palcache_info in self.palcache_infos:
            part = common.GetPartInfo(palcache_info.disk_id, palcache_info.disk_part, self.disk_list)
            if part == None:
                continue
            if part['DEVNAME'] not in pal_disks_path_name:
                todo_load_cache_disk.append({"dev_name":part['DEVNAME'], "pool_id":palcache_info.pool_id})

        # 获取palraw没有load的盘
        for palraw_info in self.palraw_infos:
            part = common.GetPartInfo(palraw_info.disk_id, palraw_info.disk_part, self.disk_list)
            if part == None:
                continue
            if part['DEVNAME'] not in pal_disks_path_name:
                todo_load_raw_disk.append({"dev_name":part['DEVNAME']})

        # load所有pool需要load的盘
        for dev_name in todo_load_pool_disk:
            logger.run.info("Auto load pool disk %s" % dev_name)
            e, res = paldisk.load_disk(dev_name)
            if e: logger.run.error("Load pool disk faild %s:%s" % (dev_name, res))

        # 重新获取pal目前认到的pool, 且为running状态的pool
        e, pal_pools = palpool.get_pool_list()
        if e:
            logger.run.error("Get pal pool list failed:%s" % pal_pools)
            return
        loading_pal_pools_id = [pool.uuid() for pool in pal_pools if apipal.testBit(pool.state(), apipal.POOL_STATE_LOADING)]

        for todo_info in todo_load_cache_disk:
            dev_name = todo_info['dev_name']
            pool_id  = todo_info['pool_id']
            # 如果target对应的pool已经标记为disable, 则使用raw的方式load磁盘
            if pool_id in pool_id_to_info.keys() and pool_id_to_info[pool_id].is_disable == True:
                logger.run.info("Start load disk %s by raw for disable pool %s" % (dev_name, pool_id_to_info[pool_id].pool_name))
                e, res = paldisk.load_disk(dev_name, 'raw')
                if e: logger.run.error("Load cache disk faild %s:%s" % (dev_name, res))
                continue
            # 如果target对应的pool已经标记为rebuild, 则使用cache的方式load磁盘
            if pool_id in pool_id_to_info.keys() and pool_id_to_info[pool_id].is_rebuild == True and pool_id_to_info[pool_id].is_invalid == False:
                logger.run.info("Start load disk %s by rebuild pool %s" % (dev_name, pool_id_to_info[pool_id].pool_name))
                e, res = paldisk.load_disk(dev_name, 'cache', pool_id_to_info[pool_id].pool_name)
                if e: logger.run.error("Load cache disk faild %s:%s" % (dev_name, res))
                continue
            # load所有target需要load的盘, 仅load target对应的pool是loading状态的target
            if pool_id not in loading_pal_pools_id:
                logger.run.info("Skip load disk %s by not loading pool %s" % (dev_name, pool_id))
                continue
            logger.run.info("Auto load cache disk %s" % dev_name)
            e, res = paldisk.load_disk(dev_name)
            if e: logger.run.error("Load cache disk faild %s:%s" % (dev_name, res))

        for todo_info in todo_load_raw_disk:
            dev_name = todo_info['dev_name']
            logger.run.info("Auto load raw disk %s" % dev_name)
            e, res = paldisk.load_disk(dev_name)
            if e: logger.run.error("Load raw disk faild %s:%s" % (dev_name, res))
        return self.SyncPoolDirtyThresh()

    def SyncPoolDirtyThresh(self):
        pool_name_to_info = {}
        for pool_info in self.pool_infos:
            pool_name_to_info[pool_info.pool_name] = pool_info
        # pal目前认到的pool
        palpool      = apipal.Pool()
        e, pal_pools = palpool.get_pool_list()
        if e:
            logger.run.error("Get pal pool list failed:%s" % pal_pools)
            return
        pal_pools_name = [pool.name() for pool in pal_pools]
        for pal_pool_name in pal_pools_name:
            if pal_pool_name not in pool_name_to_info.keys():
                continue
            e, state = apipal.Pool().get_pool_stat(pal_pool_name)
            if e:
                logger.run.error("Get pal pool %s state failed:%s" % (pal_pool_name, state))
                continue
            # sync level
            if state['sync_level'] != pool_info.sync_level:
                e, res = apipal.Pool().set_sync_level(pal_pool_name, pool_info.sync_level)
                if e:
                    logger.run.error("Set pool %s sync level failed:%s" % (pal_pool_name, res))

            # dirty thresh
            if pool_info.HasField('dirty_thresh') and \
                    (abs(int(state['p_lower_thresh']) - pool_name_to_info[pal_pool_name].dirty_thresh.lower) > 5 or \
                    abs(int(state['p_upper_thresh']) - pool_name_to_info[pal_pool_name].dirty_thresh.upper) > 5):
                lower = pool_name_to_info[pal_pool_name].dirty_thresh.lower 
                upper = pool_name_to_info[pal_pool_name].dirty_thresh.upper 
                logger.run.info("Start set pool %s dirty thresh to %s:%s" % (pal_pool_name, lower, upper))
                e, res = apipal.Pool().set_dirty_thresh(pal_pool_name, lower, upper)
                if e:
                    logger.run.error("Set pool %s dirty thresh failed:%s" % (pal_pool_name, res))
        return self.SyncTargetSkipThresh()

    def SyncTargetSkipThresh(self):
        pool_id_skip_thd = {}
        for pool_info in self.pool_infos:
            pool_id_skip_thd[pool_info.pool_id] = pool_info.skip_thresh 

        for palcache_info in self.palcache_infos:
            e, state = apipal.Target().get_target_stat(palcache_info.palcache_name)
            if e:
                logger.run.error("Can't get target state %s:%s:%s" % (palcache_info.palcache_name, e, state))
                continue
            p_s_t = pool_id_skip_thd[palcache_info.pool_id]
            if (state['skip_thresh']*512>>10) != p_s_t:
                logger.run.info("Set target skip thresh %s:%s" % (palcache_info.palcache_name, p_s_t))
                e, res = apipal.Target().set_skip_thresh(palcache_info.palcache_name, p_s_t)
                if e: logger.run.error("Set target skip thresh failed %s:%s:%s:%s" % (palcache_info.palcache_name, p_s_t, e, res))


    def load_groups(self):
        group_list = APISmartScsi().list_group()
        groups ={}
        for group_info in self.group_infos:
            groups[group_info.node_uuid] = group_info.node_info.node_guids
        
        # 目前是所有target的group都形同循环一次即可
        exist_list = []
        if group_list == 1:
            return
        for k in group_list.keys():
            for group_name in  group_list[k]["groups"].keys():
                exist_list.append(group_name)
            break

        if exist_list:
            for group_name in exist_list:
                if group_name not in groups.keys():
                    if APISmartScsi().drop_group(group_name):
                        logger.run.error("Drop group %s faild"%group_name)
            for i in groups.keys():
                if i not in exist_list:
                    if APISmartScsi().add_group(i,groups[i]):
                        logger.run.error("Create group %s faild"%i)

        elif not exist_list:
            for i in groups.keys():
                if APISmartScsi().add_group(i,groups[i]):
                    logger.run.error("Create group %s faild"%i)
        
    def SyncLun(self):
        # 同步增加
        lun_list = APISmartScsi().get_lun_list()
        for lun_info in self.lun_infos:
            params = {}
            params["group_name"]=[]
            group_uuids=[]
            for info in lun_info.group_info:
                if info.group_state:
                    group_uuids.append(info.group_uuid)
            if lun_info.config_state == False:
                continue

            lun_name = "%s_%s" % (self.node_name, lun_info.lun_name)
            # 过滤已经在线有组lun
            if lun_name in lun_list.keys() and lun_list[lun_name]['attrs'].has_key('exported') and lun_list[lun_name]['attrs']['group_name']:
                group_num = 0
                for name in group_uuids:
                    if name in lun_list[lun_name]['attrs']["group_name"]:
                        continue
                    params["group_name"].append(name)
                    group_num+=1
                if not group_num:
                    continue
            # 过滤已经在线无组lun
            elif lun_name in lun_list.keys() and lun_list[lun_name]['attrs'].has_key('exported') and not lun_list[lun_name]['attrs']['group_name']:
                continue
            else:
                params["group_name"] = group_uuids
            logger.run.info("lun group %s"%params["group_name"])
            if lun_info.lun_type == msg_pds.LUN_TYPE_BASEDEV:
                for basedev_info in self.basedev_infos:
                    if basedev_info.basedev_id == lun_info.Extensions[msg_pds.ext_luninfo_basedev_id]:
                        if os.path.exists(basedev_info.dev_name):
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = basedev_info.dev_name
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            elif lun_info.lun_type == msg_pds.LUN_TYPE_BASEDISK:
                for basedisk_info in self.basedisk_infos:
                    if basedisk_info.basedisk_id == lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id]:
                        part = common.GetPartInfo(basedisk_info.disk_id, basedisk_info.disk_part, self.disk_list)
                        if part != None:
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = part['DEVNAME']
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            elif lun_info.lun_type == msg_pds.LUN_TYPE_SMARTCACHE:
                for smartcache_info in self.smartcache_infos:
                    if smartcache_info.smartcache_id == lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id]:
                        if os.path.exists(os.path.join("/dev/mapper", smartcache_info.smartcache_id)):
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = os.path.join("/dev/mapper", smartcache_info.smartcache_id)
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALCACHE:
                for palcache_info in self.palcache_infos:
                    if palcache_info.palcache_id == lun_info.Extensions[msg_pds.ext_luninfo_palcache_id]:
                        if os.path.exists(os.path.join("/dev/", palcache_info.palcache_name)):
                            # pal目前认到的target, target除了在dev下确认外,还需要在target list二次确认
                            paltarget = apipal.Target()
                            e, pal_targets = paltarget.get_target_list()
                            if e:
                                logger.run.error("Get pal target list failed:%s" % pal_targets)
                                continue
                            ok_flag = False 
                            for target in pal_targets:
                                if str(target.uuid()) == palcache_info.palcache_id:
                                    if apipal.testBit(target.state(), apipal.TARGET_LOADED):
                                        ok_flag = True
                                    break
                            if ok_flag == False:
                                logger.run.error("PalCache %s status is not ok" % palcache_info.palcache_name)
                                continue
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = os.path.join("/dev/", palcache_info.palcache_name)
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALRAW:
                for palraw_info in self.palraw_infos:
                    if palraw_info.palraw_id == lun_info.Extensions[msg_pds.ext_luninfo_palraw_id]:
                        if os.path.exists(os.path.join("/dev/", palraw_info.palraw_name)):
                            # pal目前认到的target, target除了在dev下确认外,还需要在target list二次确认
                            paltarget = apipal.Target()
                            e, pal_targets = paltarget.get_target_list()
                            if e:
                                logger.run.error("Get pal target list failed:%s" % pal_targets)
                                continue
                            ok_flag = False 
                            for target in pal_targets:
                                if str(target.uuid()) == palraw_info.palraw_id:
                                    if apipal.testBit(target.state(), apipal.TARGET_LOADED):
                                        ok_flag = True
                                    break
                            if ok_flag == False:
                                logger.run.error("PalRaw %s status is not ok" % palraw_info.palraw_name)
                                continue
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = os.path.join("/dev/", palraw_info.palraw_name)
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            elif lun_info.lun_type == msg_pds.LUN_TYPE_PALPMT:
                for palpmt_info in self.palpmt_infos:
                    if palpmt_info.palpmt_id == lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id]:
                        if os.path.exists(os.path.join("/dev/", palpmt_info.palpmt_name)):
                            # pal目前认到的target, target除了在dev下确认外,还需要在target list二次确认
                            paltarget = apipal.Target()
                            e, pal_targets = paltarget.get_target_list()
                            if e:
                                logger.run.error("Get pal target list failed:%s" % pal_targets)
                                continue
                            ok_flag = False 
                            for target in pal_targets:
                                if str(target.uuid()) == palpmt_info.palpmt_id:
                                    if apipal.testBit(target.state(), apipal.TARGET_LOADED):
                                        ok_flag = True
                                    break
                            if ok_flag == False:
                                logger.run.error("PalPmt %s status is not ok" % palpmt_info.palpmt_name)
                                continue
                            logger.run.info("Start auto load lun %s" % (lun_info.lun_name))
                            params['device_name'] = "%s_%s" % (self.node_name, lun_info.lun_name)
                            params['path']        = os.path.join("/dev/", palpmt_info.palpmt_name)
                            params['t10_dev_id']  = lun_info.lun_id[:23]
                            apismartscsi = APISmartScsi()
                            e = apismartscsi.add_lun(params)
                            if e: logger.run.error("Add lun failed:%s" % apismartscsi.errmsg)
                        break
            else:
                assert(0)
        
        # 同步删除
        lun_list = APISmartScsi().get_lun_list()
        for lun_name in lun_list.keys():
            if lun_name not in ["%s_%s" % (self.node_name, lun_info.lun_name) for lun_info in self.lun_infos]:
                apismartscsi = APISmartScsi()
                if lun_list[lun_name]["attrs"]["group_name"]:
                    for k in lun_list[lun_name]["attrs"]["group_name"]:
                        logger.run.info("Start auto remove lun %s group %s" %(lun_name,k))
                        e,exist_lun = apismartscsi.drop_lun_with_group(lun_name,k)
                        if e:
                            logger.run.error("Drop lun failed:%s" % apismartscsi.errmsg)
                else:
                    logger.run.info("Start auto remove lun %s" % lun_name)
                    e,exist_lun = apismartscsi.drop_lun_with_group(lun_name)
                    if e: 
                        logger.run.error("Drop lun failed:%s" % apismartscsi.errmsg)

        APISmartScsi().enable_targets()
        return self.FinishMachine()

    def FinishMachine(self):
        return MS_FINISH
