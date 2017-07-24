# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import struct
from twisted.internet import reactor
from twisted.internet import protocol

import message.pds_pb2 as pds

from pdsframe.core.client import MyClientFactory
from pdsframe.common.logger import logger
from pdsframe.common.config import config
from pdsframe.common.common import MAX_LEN, MS_ERROR, MS_CONTINUE, MS_FINISH
from pdsframe.core.machine_factory import MachineFactory

class MyServerProtocal(protocol.Protocol):
    def __init__(self):
        self.data = ""

    def connectionMade(self):
        # logger.run.debug("connection made [%s:%s] session: %d" % (self.transport.client[0], self.transport.client[1], self.transport.sessionno))
        pass

    def connectionLost(self, reason):
        # logger.run.debug("connectionLost")
        pass

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

        request = pds.Message()
        request.ParseFromString(self.data[pkSize:pkSize+dataLen])
        return self.handleData(request)

    # 处理数据流
    def handleData(self, request):
        Machine = MachineFactory.getInstance().NewMachine(request.head.message_type)
        if Machine == None:
            logger.run.error("Cann't find machine by message type: %d " % request.head.message_type)
            self.transport.loseConnection()
            return
        logger.run.debug("ReceiveRequest from [%s:%s]\n%s" % (self.transport.client[0], self.transport.client[1], str(request).strip()))

        machine = Machine(self.transport)
        ret = machine.INIT(request)
        if ret == MS_CONTINUE:
            return
        elif ret in [MS_ERROR, MS_FINISH]:
            self.transport.loseConnection()
        else:
            assert(0)

class MyServerFactory(protocol.Factory):
    # protocol: This will be used by the default buildProtocol to create new protocols:
    protocol = MyServerProtocal
