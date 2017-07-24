# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import socket, hashlib
import sys, os, struct, json
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))

from pdsframe import *
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
from pdsframe.common.config import init_config, config
from pdsframe.common.common import MAX_LEN

import protobuf_json

pkSize = len(struct.pack('I', 0))
socket.setdefaulttimeout(120)

def OUT_DEBUG(out):
    print "Debug : %s" % out

def OUT_INFO(out):
    print out

def OUT_ERROR(out):
    print "\033[1;31m" + out + "\033[0m"

class BaseMgr:
    def send(self, message):
        if self.srv['cli_config']['debug'] == True:
            out  = "====================== Request ======================\n"
            out += str(message).strip()
            OUT_INFO(out)

        # 尝试次数
        try_times = 1
        info      = ""
        response = msg_pds.Message()
        
        class RequestStateType:
            INIT         = 0
            NOT_MASTER   = 1
            TIMEOUT      = 2
            SOCKET_ERROR = 3
            UNEXPECTED   = 4

        # REQUEST_STATE_TYPE = enum.Enum('INIT', 'NOT_MASTER', 'TIMEOUT', 'SOCKET_ERROR', 'UNEXPECTED')
        REQUEST_STATE_TYPE = RequestStateType()
        while(try_times >= 0):
            try:
                request_state = REQUEST_STATE_TYPE.INIT
                response = self._send(message)
                break
            except socket.timeout as e:
                request_state = REQUEST_STATE_TYPE.TIMEOUT
                break
            except socket.error as e:
                try_times -= 1
                request_state = REQUEST_STATE_TYPE.SOCKET_ERROR
                continue
            except Exception as e:
                try_times -= 1
                if self.srv['cli_config']['debug'] == True:
                    OUT_DEBUG(str(e))
                request_state = REQUEST_STATE_TYPE.UNEXPECTED

        if request_state == REQUEST_STATE_TYPE.NOT_MASTER:
            out  = "Connection Error : Cann't get MDS info, please try again or 30 seconds later"
            OUT_ERROR(out)
            sys.exit(1)
        elif request_state == REQUEST_STATE_TYPE.TIMEOUT:
            out  = "Command Timeout : Please try again or try again later."
            OUT_ERROR(out)
            sys.exit(1)
        elif request_state == REQUEST_STATE_TYPE.SOCKET_ERROR:
            out  = "Connection Refused : MDS service is starting ?"
            OUT_ERROR(out)
            sys.exit(1)
        elif request_state == REQUEST_STATE_TYPE.UNEXPECTED or not response.HasField('head') or not response.HasField('rc'):
            out  = "=======================================================================\n"
            out += "* If you see this tip, it means that an unexpected error occurred !!! *\n"
            out += "* Please contact your supplier for help.                              *\n"
            out += "======================================================================="
            OUT_ERROR(out)
            sys.exit(1)

        if self.srv['cli_config']['json'] == True:
            OUT_INFO(json.dumps(protobuf_json.pb2json(response), indent=4))
            sys.exit(0)

        if self.srv['cli_config']['debug'] == True:
            out  = "====================== Response ======================\n"
            out += "%s\n" % str(response).strip()
            out += "======================================================"
            OUT_INFO(out)

        return response

    def _send(self, message):
        # 准备数据
        data = message.SerializeToString()  
        assert(len(data) < MAX_LEN)
        data = struct.pack('I', len(data))+data

        # 发包
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        sock.connect((self.srv['ip'], self.srv['port']))  
        sock.send(data)  

        # 收包
        data = ""
        while True:
            data += sock.recv(1024)  
            if len(data) >= (pkSize + struct.unpack('I', data[:pkSize])[0]):
                break
        sock.close()  

        # 解析包
        response = msg_pds.Message()
        response.ParseFromString(data[pkSize:len(data)])
        return response
