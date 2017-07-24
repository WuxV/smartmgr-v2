# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import psutil, socket
import threading,socket,json,time,struct,sys

from pdsframe import *
from service_mds import g
from service_mds import common
import message.pds_pb2 as msg_pds

pkSize = len(struct.pack('I', 0))

class BoarCastSer:
    def __init__(self, params={}):
        self.host = params['host']
        self.port = params['port'] 
    
    def server(self):
        host = "%s.0" % ".".join(self.host.split(".")[:3])
        address= (host, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        sock.bind(address)
        
        while True:
            time.sleep(0.1)
            try:
                data = ""
                while True:
                    _data, addr = sock.recvfrom(1024)  
                    data += _data
                    if len(data) >= (pkSize + struct.unpack('I', data[:pkSize])[0]):
                        break
                data = data[pkSize:len(data)]

                logger.run.debug("Recv broadcast request %s from %s:%s" % (json.loads(data), addr[0], addr[1]))
                _data = json.loads(data)
                if _data['action'] == "discover":
                    if _data.has_key("broadcast_version"):
                        nsnode_info              = msg_pds.NSNodeInfo()
                        if _data['broadcast_version'] == g.broadcast_version:
                            nsnode_info.node_uuid = g.node_uuid
                        nsnode_info.node_name    = g.node_info.node_name
                        nsnode_info.sys_mode     = g.platform['sys_mode']
                        nsnode_info.platform     = g.platform['platform']
                        nsnode_info.host_name    = socket.gethostname()
                        nsnode_info.listen_ip    = config.safe_get('network', 'listen-ip')
                        nsnode_info.listen_port  = config.safe_get_int('network', 'listen-port')
                        nsnode_info.broadcast_ip = self.host
                        nsnode_info.ibguids.extend(g.ibguids)
                        nsnode_info.is_smartmon  = g.is_smartmon
                        data = nsnode_info.SerializeToString()
                        data = struct.pack('I', len(data))+data
                        ret = sock.sendto(data, addr)
                        logger.run.debug("Send broadcast response %s to %s:%s ret %s" % (nsnode_info, addr[0], addr[1], ret))
                    if _data.has_key("smartmon_ip"):
                        g.smartmon_ip = _data["smartmon_ip"] 
                else:
                    logger.run.error("Not support")
                    assert(0)
            except (KeyboardInterrupt,SystemExit):
                raise
            except socket.timeout as e:
                pass
            except Exception as e:
                logger.run.error("recv udp error:%s" % e)

class MyThread(threading.Thread):
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.params = params
    
    def run(self):
        s = BoarCastSer(self.params)
        s.server()        

class CreateBoarCastSer(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME = 5

    def INIT(self):
        ncard = config.safe_get('model-config', 'discover-ncard')
        nip   = common.get_ip_address(ncard)
        if nip == None:
            logger.run.error("Can't get ip from :%s" % ncard)
            return MS_FINISH

        params = {}
        params['host'] = nip
        params['port'] = config.safe_get_int('model-config', 'discover-port')

        for connection in psutil.net_connections():
            if connection.type == socket.SOCK_DGRAM and connection.laddr[1] == params['port']:
                return MS_FINISH

        logger.run.debug("Start create boardcase thread, params : %s" % str(params))
        t = MyThread(params)
        t.setDaemon(True)
        t.start()
        return MS_FINISH
