# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import socket, struct
import message.pds_pb2 as msg_pds
from pdsframe import *

pkSize = len(struct.pack('I', 0))

def send(message):
    ip   = config.safe_get('network', 'listen-ip')
    port = config.safe_get('network', 'listen-port')

    # 准备数据
    data = message.SerializeToString()  
    data = struct.pack('I', len(data))+data

    # 发包
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    sock.connect((ip, int(port)))  
    sock.send(data)  
    data = ""
    while True:
        data += sock.recv(1024)  
        if len(data) >= (pkSize + struct.unpack('I', data[:pkSize])[0]):
            break
    sock.close()  

    # 解析包
    response = msg_pds.Message()
    response.ParseFromString(data[pkSize:len(data)])
    if not response.HasField('rc'):
        assert(0)
    return str(response).strip()

