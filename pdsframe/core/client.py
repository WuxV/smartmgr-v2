# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import struct
from twisted.internet import reactor
from twisted.internet import protocol

import message.pds_pb2 as pds
from pdsframe.common.common import MAX_LEN
from pdsframe.common.logger import logger

class MyClientProtocal(protocol.Protocol):
    def __init__(self):
        self.data = ""

    def connectionMade(self):
        data = self.factory.msg.SerializeToString()
        assert(len(data) < MAX_LEN)
        data = struct.pack('I', len(data))+data

        self.transport.write(data)

    def dataReceived(self, data):
        pkSize = len(struct.pack('I', 0))

        self.data += data
        if len(self.data) < pkSize:
            # print "pkSize pass"
            return
        dataLen = struct.unpack('I', self.data[:pkSize])[0]

        if len(self.data) < dataLen:
            # print "dataLen pass"
            return 

        response = pds.Message()
        response.ParseFromString(self.data[pkSize:pkSize+dataLen])

        if self.factory.is_timeout == True:
            logger.run.error("Machine is already timeout, skip message :\n%s" % str(response).strip())
            return
        else:
            self.factory.callID.cancel()
        
        assert(response.HasField('rc'))
        logger.run.debug("ReceiveResponse\n%s" % (str(response).strip()))

        # 调用回调处理
        self.factory.callback(response)
        self.transport.loseConnection()
    
    def connectionLost(self, reason):
        # print "connection lost"
        pass

    def createData(self):
        msg = common.CreateMessage()
        return entitydesc.SerializeToString()  

class MyClientFactory(protocol.ClientFactory):
    protocol = MyClientProtocal
    def __init__(self, msg, func, timeout, timeout_fun):
        self.msg         = msg
        self.callback    = func
        self.timeout     = timeout
        self.timeout_fun = timeout_fun
        self.is_timeout  = False
        self.callID      = reactor.callLater(self.timeout, self.handle_timeout)

    def handle_timeout(self):
        self.is_timeout = True
        self.timeout_fun()

    def clientConnectionFailed(self, connector, reason):
        # print "Connection failed - goodbye!"
        # reactor.stop()
        pass
    
    def clientConnectionLost(self, connector, reason):
        # print "Connection lost - goodbye!"
        # reactor.stop()
        pass
