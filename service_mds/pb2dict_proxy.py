# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import message.pds_pb2 as msg_pds

def dict2pb(type_name, dict_info):
    return getattr(PbDictProxy(), type_name)(True, dict_info)

def pb2dict(type_name, protobuf_info):
    return getattr(PbDictProxy(), type_name)(False, protobuf_info)

class PbDictProxy():
    def disk_info(self, is_to_pb, data):
        if is_to_pb:
            disk_info = msg_pds.DiskInfo()
            disk_info.disk_name   = data['disk_name']
            disk_info.size        = data['size']
            disk_info.disk_type   = data['disk_type']
            disk_info.header.uuid = data['header.uuid']
            for _diskpart in data['diskparts']:
                diskpart = disk_info.diskparts.add()
                diskpart.disk_part = _diskpart['disk_part']
                diskpart.size      = _diskpart['size']
            return disk_info
        else:
            disk_info = {}
            disk_info['disk_name']   = data.disk_name
            disk_info['header.uuid'] = data.header.uuid
            disk_info['size']        = data.size
            disk_info['disk_type']   = data.disk_type
            disk_info['diskparts']   = []
            for _diskpart in data.diskparts:
                diskpart = {}
                diskpart['disk_part']  = _diskpart.disk_part
                diskpart['size']       = _diskpart.size
                disk_info['diskparts'].append(diskpart)
            return disk_info

    def basedisk_info(self, is_to_pb, data):
        if is_to_pb:
            basedisk_info = msg_pds.BaseDiskInfo()
            basedisk_info.basedisk_id = data['basedisk_id']
            basedisk_info.disk_id     = data['disk_id']
            basedisk_info.disk_part   = data['disk_part']
            return basedisk_info
        else:
            basedisk_info = {}
            basedisk_info['basedisk_id'] = data.basedisk_id
            basedisk_info['disk_id']     = data.disk_id
            basedisk_info['disk_part']   = data.disk_part
            return basedisk_info

    def smartcache_info(self, is_to_pb, data):
        if is_to_pb:
            smartcache_info = msg_pds.SmartCacheInfo()
            smartcache_info.smartcache_id   = data['smartcache_id']
            smartcache_info.data_disk_id    = data['data_disk_id']
            smartcache_info.data_disk_part  = data['data_disk_part']
            smartcache_info.cache_disk_id   = data['cache_disk_id']
            smartcache_info.cache_disk_part = data['cache_disk_part']
            for _params in data['params']:
                kv = smartcache_info.params.add()
                kv.disk_part = _params['key']
                kv.size      = _params['value']
            return smartcache_info
        else:
            smartcache_info = {}
            smartcache_info['smartcache_id']   = data.smartcache_id
            smartcache_info['data_disk_id']    = data.data_disk_id
            smartcache_info['data_disk_part']  = data.data_disk_part
            smartcache_info['cache_disk_id']   = data.cache_disk_id
            smartcache_info['cache_disk_part'] = data.cache_disk_part
            smartcache_info['params']   = []
            for _param in data.params:
                kv = {}
                kv['key']   = _param.key
                kv['value'] = _param.value
                smartcache_info['params'].append(kv)
            return smartcache_info

    def lun_info(self, is_to_pb, data):
        if is_to_pb:
            lun_info = msg_pds.LunInfo()
            lun_info.lun_name     = data['lun_name']
            lun_info.lun_id       = data['lun_id']
            lun_info.lun_type     = data['lun_type']
            lun_info.config_state = data['config_state']
            if data.has_key('qos_template_id'):
                lun_info.qos_template_id = data['qos_template_id']
            if data.has_key('qos_template_name'):
                lun_info.qos_template_name = data['qos_template_name']
            if data.has_key('qos_template_name'):
                lun_info.qos_template_name = data['qos_template_name']
            if data.has_key('ext_luninfo_basedisk_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_basedisk_id]   = data['ext_luninfo_basedisk_id']
            if data.has_key('ext_luninfo_basedev_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_basedev_id]    = data['ext_luninfo_basedev_id']
            if data.has_key('ext_luninfo_smartcache_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_smartcache_id] = data['ext_luninfo_smartcache_id']
            if data.has_key('ext_luninfo_palcache_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_palcache_id]   = data['ext_luninfo_palcache_id']
            if data.has_key('ext_luninfo_palraw_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_palraw_id]   = data['ext_luninfo_palraw_id']
            if data.has_key('ext_luninfo_palpmt_id'):
                lun_info.Extensions[msg_pds.ext_luninfo_palpmt_id]   = data['ext_luninfo_palpmt_id']
            if data.has_key('group_info'):
                for k in  data["group_info"].keys():
                    info = lun_info.group_info.add()
                    info.group_uuid = k
                    info.group_state = data["group_info"][k]["group_state"]
            if data.has_key('group_name'):
                lun_info.group_name.extend(data["group_name"])

            return lun_info
        else:
            lun_info = {}
            lun_info['lun_name']     = data.lun_name
            lun_info['lun_id']       = data.lun_id
            lun_info['lun_type']     = data.lun_type
            lun_info['config_state'] = data.config_state
            lun_info['group_info'] = {}
            for info in  data.group_info:
                lun_info['group_info'][info.group_uuid] = {}
                lun_info['group_info'][info.group_uuid]["group_state"] = info.group_state
            lun_info["group_name"] = []
            for i in data.group_name:
                lun_info["group_name"].append(i)
            lun_info['qos_template_id'] = data.qos_template_id
            lun_info['qos_template_name'] = data.qos_template_name
            if data.HasExtension(msg_pds.ext_luninfo_basedev_id):
                lun_info['ext_luninfo_basedev_id']   = data.Extensions[msg_pds.ext_luninfo_basedev_id]
            if data.HasExtension(msg_pds.ext_luninfo_basedisk_id):
                lun_info['ext_luninfo_basedisk_id']   = data.Extensions[msg_pds.ext_luninfo_basedisk_id]
            if data.HasExtension(msg_pds.ext_luninfo_smartcache_id):
                lun_info['ext_luninfo_smartcache_id'] = data.Extensions[msg_pds.ext_luninfo_smartcache_id]
            if data.HasExtension(msg_pds.ext_luninfo_palcache_id):
                lun_info['ext_luninfo_palcache_id']   = data.Extensions[msg_pds.ext_luninfo_palcache_id]
            if data.HasExtension(msg_pds.ext_luninfo_palraw_id):
                lun_info['ext_luninfo_palraw_id']   = data.Extensions[msg_pds.ext_luninfo_palraw_id]
            if data.HasExtension(msg_pds.ext_luninfo_palpmt_id):
                lun_info['ext_luninfo_palpmt_id']   = data.Extensions[msg_pds.ext_luninfo_palpmt_id]
            return lun_info

    def pool_info(self, is_to_pb, data):
        if is_to_pb:
            pool_info = msg_pds.PoolInfo()
            pool_info.pool_id     = data['pool_id']
            pool_info.pool_name   = data['pool_name']
            if data.has_key('extent'):      pool_info.extent     = data['extent']
            if data.has_key('bucket'):      pool_info.bucket     = data['bucket']
            if data.has_key('sippet'):      pool_info.sippet     = data['sippet']
            if data.has_key('is_invalid'):  pool_info.is_invalid = data['is_invalid']
            if data.has_key('is_rebuild'):  pool_info.is_rebuild = data['is_rebuild']
            if data.has_key('sync_level'):  pool_info.sync_level = data['sync_level']
            if data.has_key('skip_thresh'): pool_info.skip_thresh = data['skip_thresh']
            if data.has_key('is_variable'): pool_info.is_variable = data['is_variable']
            for _pool_disk_info in data['pool_disk_infos']:
                pool_disk_info = pool_info.pool_disk_infos.add()
                pool_disk_info.disk_id   = _pool_disk_info['disk_id']
                pool_disk_info.disk_part = _pool_disk_info['disk_part']
            if data.has_key('dirty_thresh'):
                pool_info.dirty_thresh.lower = int(data['dirty_thresh']['lower'])
                pool_info.dirty_thresh.upper = int(data['dirty_thresh']['upper'])
            return pool_info
        else:
            pool_info = {}
            pool_info['pool_name'] = data.pool_name
            pool_info['pool_id']   = data.pool_id
            if data.HasField('extent'):      pool_info['extent']     = data.extent
            if data.HasField('bucket'):      pool_info['bucket']     = data.bucket
            if data.HasField('sippet'):      pool_info['sippet']     = data.sippet
            if data.HasField('is_invalid'):  pool_info['is_invalid'] = data.is_invalid
            if data.HasField('is_rebuild'):  pool_info['is_rebuild'] = data.is_rebuild
            if data.HasField('sync_level'):  pool_info['sync_level'] = data.sync_level
            if data.HasField('skip_thresh'): pool_info['skip_thresh'] = data.skip_thresh
            if data.HasField('is_variable'): pool_info['is_variable'] = data.is_variable
            pool_info['pool_disk_infos'] = []
            for _pool_disk_info in data.pool_disk_infos:
                pool_disk_info = {}
                pool_disk_info['disk_id']   = _pool_disk_info.disk_id
                pool_disk_info['disk_part'] = _pool_disk_info.disk_part
                pool_info['pool_disk_infos'].append(pool_disk_info)
            if data.HasField('dirty_thresh'):
                pool_info['dirty_thresh'] = {}
                pool_info['dirty_thresh']['lower'] = data.dirty_thresh.lower
                pool_info['dirty_thresh']['upper'] = data.dirty_thresh.upper
            return pool_info

    def palcache_info(self, is_to_pb, data):
        if is_to_pb:
            palcache_info = msg_pds.PalCacheInfo()
            palcache_info.palcache_id   = data['palcache_id']
            palcache_info.palcache_name = data['palcache_name']
            palcache_info.pal_id        = data['pal_id']
            palcache_info.pool_id       = data['pool_id']
            palcache_info.disk_id       = data['disk_id']
            palcache_info.disk_part     = data['disk_part']
            return palcache_info
        else:
            palcache_info = {}
            palcache_info['palcache_id']   = data.palcache_id
            palcache_info['palcache_name'] = data.palcache_name
            palcache_info['pal_id']        = data.pal_id
            palcache_info['pool_id']       = data.pool_id
            palcache_info['disk_id']       = data.disk_id
            palcache_info['disk_part']     = data.disk_part
            return palcache_info

    def palraw_info(self, is_to_pb, data):
        if is_to_pb:
            palraw_info = msg_pds.PalRawInfo()
            palraw_info.palraw_id   = data['palraw_id']
            palraw_info.palraw_name = data['palraw_name']
            palraw_info.pal_id      = data['pal_id']
            palraw_info.disk_id     = data['disk_id']
            palraw_info.disk_part   = data['disk_part']
            return palraw_info
        else:
            palraw_info = {}
            palraw_info['palraw_id']   = data.palraw_id
            palraw_info['palraw_name'] = data.palraw_name
            palraw_info['pal_id']      = data.pal_id
            palraw_info['disk_id']     = data.disk_id
            palraw_info['disk_part']   = data.disk_part
            return palraw_info

    def palpmt_info(self, is_to_pb, data):
        if is_to_pb:
            palpmt_info = msg_pds.PalPmtInfo()
            palpmt_info.palpmt_id   = data['palpmt_id']
            palpmt_info.palpmt_name = data['palpmt_name']
            palpmt_info.pal_id      = data['pal_id']
            palpmt_info.pool_id     = data['pool_id']
            palpmt_info.size        = data['size']
            return palpmt_info
        else:
            palpmt_info = {}
            palpmt_info['palpmt_id']   = data.palpmt_id
            palpmt_info['palpmt_name'] = data.palpmt_name
            palpmt_info['pal_id']      = data.pal_id
            palpmt_info['pool_id']     = data.pool_id
            palpmt_info['size']        = data.size
            return palpmt_info

    def basedev_info(self, is_to_pb, data):
        if is_to_pb:
            basedev_info = msg_pds.BaseDevInfo()
            basedev_info.basedev_id = data['basedev_id']
            basedev_info.dev_name   = data['dev_name']
            basedev_info.size       = data['size']
            return basedev_info
        else:
            basedev_info = {}
            basedev_info['basedev_id'] = data.basedev_id
            basedev_info['dev_name']   = data.dev_name
            basedev_info['size']       = data.size
            return basedev_info

    def node_info(self, is_to_pb, data):
        if is_to_pb:
            node_info = msg_pds.NodeInfo()
            node_info.node_name = data['node_name']
            return node_info
        else:
            node_info = {}
            node_info['node_name'] = data.node_name
            return node_info

    def nsnode_info(self, is_to_pb, data):
        if is_to_pb:
            nsnode_info = msg_pds.NodeInfoConf()
            nsnode_info.node_uuid    = data["node_uuid"]
            nsnode_info.node_name    = data["node_name"]
            nsnode_info.listen_ip    = data["listen_ip"]
            nsnode_info.listen_port  = data["listen_port"]

            nsnode_info.node_guids.extend(data["node_guids"])
            if "node_index" in data.keys():
                nsnode_info.node_index    =data["node_index"]
            return nsnode_info
        else:
            node_info = {}
            node_info['node_uuid'] = data.node_uuid
            node_info['node_name'] = data.node_name
            node_info['listen_port'] = data.listen_port
            node_info['listen_ip'] = data.listen_ip
            node_info["node_guids"]   = []
            for ibguid in data.node_guids:
                node_info["node_guids"].append(ibguid)
            if data.HasField("node_index"):
                node_info["node_index"] = data.node_index
            return node_info

    def group_info(self, is_to_pb, data):
        if is_to_pb:
            group_info = msg_pds.GroupInfoConf()
            group_info.group_name    = data["group_name"]
            group_info.node_uuids.extend(data["node_uuids"])
            return group_info
        else:
            group_info = {}
            group_info['group_name'] = data.group_name
            group_info["node_uuids"]   = []
            for node_uuid in data.node_uuids:
                group_info["node_uuids"].append(node_uuid)
            return group_info

    def template_info(self, is_to_pb, data):
        if is_to_pb:
            template_info = msg_pds.QosTemplateInfo()
            template_info.template_id         = data["template_id"]
            template_info.template_name       = data["template_name"]
            template_info.qos_info.read_bps   = data["read_bps"]
            template_info.qos_info.read_iops  = data["read_iops"]
            template_info.qos_info.write_bps  = data["write_bps"]
            template_info.qos_info.write_iops = data["write_iops"]
            return template_info
        else:
            template_info = {}
            template_info["template_id"]   = data.template_id
            template_info["template_name"] = data.template_name
            template_info["read_bps"]      = data.qos_info.read_bps or 0
            template_info["read_iops"]     = data.qos_info.read_iops or 0
            template_info["write_bps"]     = data.qos_info.write_bps or 0
            template_info["write_iops"]    = data.qos_info.write_iops or 0
            return template_info
