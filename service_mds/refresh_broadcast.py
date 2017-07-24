# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import socket, json, struct, time
from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

pkSize = len(struct.pack('I', 0))

# 节点信息最大有效时间
MAX_NSNODE_ACTIVE_TIME = 30

class RefreshBroadcastMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME  = 10

    def INIT(self):
        if g.is_ready == False:
            return MS_FINISH
        
        self.LongWork(self.send_broadcast, {}, self.Entry_Broadcast)
            
        return MS_CONTINUE

    def send_broadcast(self, params={}):
        rc = msg_pds.ResponseCode()
        rc.retcode = msg_pds.RC_SUCCESS
        ncard = config.safe_get('model-config', 'discover-ncard')
        nip   = common.get_ip_address(ncard)
        if nip == None:
            logger.run.error("Can't get ip from :%s" % ncard)
            return rc, []
        data = {"action":"discover", "broadcast_version":g.broadcast_version}
        smartmon_ip = config.safe_get('network', 'listen-ip') 
        if g.is_smartmon == True:
            data.update({"smartmon_ip":smartmon_ip})
        data = json.dumps(data)
        data = struct.pack('I', len(data))+data
        host = "%s.0" % ".".join(nip.split(".")[:3])
        desc = (host, config.safe_get_int('model-config', 'discover-port'))
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        sock.settimeout(2)
        sock.sendto(data, desc)

        data_nsnode = []
        try:
            data = ""
            while True:
                data += sock.recv(1024)  
                if len(data) >= (pkSize + struct.unpack('I', data[:pkSize])[0]):
                    _data = data[pkSize:pkSize+struct.unpack('I', data[:pkSize])[0]]
                    data_nsnode.append(_data)
                    data = data[pkSize+struct.unpack('I', data[:pkSize])[0]:]
        except socket.timeout as e:
            pass
        sock.close()  
        return rc, data_nsnode

    def Entry_Broadcast(self, result):
        rc, data_nsnode = result

        # 更新节点时间
        g.nsnode_list.Clear()
        for data in data_nsnode:
            nsnode_info = msg_pds.NSNodeInfo()
            try:
                nsnode_info.ParseFromString(data)
            except:
                continue

            # 每次都更新不需要跳过
            #key = "%s.%s.%s" % (nsnode_info.listen_ip, nsnode_info.listen_port, nsnode_info.sys_mode)
            #flag = False
            #for _nsnode_info in g.nsnode_list.nsnode_infos: 
            #    if key == "%s.%s.%s" % (_nsnode_info.listen_ip, _nsnode_info.listen_port, _nsnode_info.sys_mode):
            #        print key
            #        _nsnode_info.last_broadcast_time = int(time.time())
            #        flag = True
            #        break
            #if flag == False:
            #    _nsnode_info = g.nsnode_list.nsnode_infos.add()
            #    _nsnode_info.CopyFrom(nsnode_info)
            #    _nsnode_info.last_broadcast_time = int(time.time())
            #    # 存储节点上线, 需要置刷新标记
            #    if nsnode_info.sys_mode != "database":
            #        g.srp_rescan_flag = True

            _nsnode_info = g.nsnode_list.nsnode_infos.add()
            _nsnode_info.CopyFrom(nsnode_info)
            _nsnode_info.last_broadcast_time = int(time.time())
            # 存储节点上线, 需要置刷新标记
            if nsnode_info.sys_mode != "database":
                g.srp_rescan_flag = True

        # 清除超时节点
        nsnode_list = msg_mds.G_NSNodeList() 
        for nsnode_info in g.nsnode_list.nsnode_infos: 
            if int(time.time()) - nsnode_info.last_broadcast_time < MAX_NSNODE_ACTIVE_TIME:
                nsnode_list.nsnode_infos.add().CopyFrom(nsnode_info)
            else:
                # 存储节点离线, 需要置刷新标记
                if nsnode_info.sys_mode != "database":
                    g.srp_rescan_flag = True
        g.nsnode_list = nsnode_list
        return MS_FINISH
