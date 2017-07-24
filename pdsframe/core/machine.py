# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import uuid, struct, time
import message.pds_pb2 as msg_pds
from pdsframe.common.logger import logger
from pdsframe.common.config import config
from pdsframe.common.common import MAX_LEN
from pdsframe.core.machine_factory import MachineFactory
from pdsframe.core.loop_machine import LoopMachine
from pdsframe.core.client import MyClientFactory

from twisted.internet import reactor, threads

class BaseMachine(object):
    MESSAGE_LOG = True

    def __init__(self, transport = None):
        self.default_timeout = 10
        self._transport = transport
        self._params = None

    def TIMEOUT(self):
        info = "'%s' has timeout happen, info: \n%s" % (self.__class__.__name__, "\n".join(["%8s : %s" % (k,v) for k,v in self._params.items()]))
        logger.run.error(info)

        if not hasattr(self, 'LOOP_TIME') and hasattr(self, 'response'):
            self.response.rc.retcode = msg_pds.RC_TIMEOUT
            self.response.rc.message = "Action timeout"
            self.SendResponse(self.response)
            return msg_pds.RC_TIMEOUT
        elif not hasattr(self, 'LOOP_TIME'):
            logger.run.warning("Machine has timeout happened, but has no response action")

    def SendInternalRequest(self, msg, cb, timeout=0, timeout_fun=None):
        self._params = {'type':'InternalRequest', 'message':msg, 'callback':cb.__name__}
        if timeout == 0:        timeout     = self.default_timeout
        if timeout_fun == None: timeout_fun = self.TIMEOUT

        assert(not msg.HasField('rc'))
        logger.run.debug("SendInternalRequest\n%s" % str(msg).strip())
        self.send_internal_request(msg, cb, timeout, timeout_fun)

    def SendRequest(self, ip, port, msg, cb, timeout=0, timeout_fun=None):
        self._params = {'type':'Request', 'message':msg, 'callback':cb.__name__, 'ip':ip, 'port':port}
        if timeout == 0:        timeout     = self.default_timeout
        if timeout_fun == None: timeout_fun = self.TIMEOUT

        assert(not msg.HasField('rc'))
        logger.run.debug("SendRequest to [%s:%s]\n%s" % (ip, port, str(msg).strip()))
        self.send_request(ip, port, msg, cb, timeout, timeout_fun)

    def SendResponse(self, msg):
        assert(msg.HasField('rc'))
        logger.run.debug("SendResponse\n%s" % str(msg).strip())
        self.send_response(msg)

    def LongWork(self, fun, params, cb = None, timeout = 0, timeout_fun = None):
        message = {'session':str(uuid.uuid1()), 'params':params}
        self._params = {'type':'LongWork', 'message':message, 'function':fun.__name__}
        logger.run.debug("SendLongWork : %s %s" % (fun.__name__, message))
        if cb != None:
            if timeout == 0:        timeout     = self.default_timeout
            if timeout_fun == None: timeout_fun = self.TIMEOUT
            machine = self.__class__.__name__
            longAction = LongAction(fun, message, cb, timeout, timeout_fun, machine)
            longAction.do()
        else:
            reactor.callInThread(fun, message['params'])

    def send_internal_request(self, msg, cb, timeout, timeout_fun):
        port = config.safe_get_int('network', 'listen-port')
        reactor.connectTCP("localhost", port, MyClientFactory(msg, cb, timeout, timeout_fun))

    def send_request(self, ip, port, msg, cb, timeout, timeout_fun):
        reactor.connectTCP(ip, port, MyClientFactory(msg, cb, timeout, timeout_fun))

    def send_response(self, response):
        response = response.SerializeToString()  
        assert(len(response) < MAX_LEN)
        response = struct.pack('I', len(response))+response
        assert(self._transport != None)
        self._transport.write(response)

class LongAction():
    def __init__(self, fun, message, cb, timeout, timeout_fun, machine):
        self.fun         = fun
        self.message     = message
        self.cb          = cb
        self.timeout     = timeout
        self.timeout_fun = timeout_fun
        self.is_timeout  = False
        self.machine     = machine

    def do(self):
        self.callID = reactor.callLater(self.timeout, self.handle_timeout)

        d=threads.deferToThread(self.fun, self.message['params'])
        d.addCallback(self.handle_langwork)

    def handle_timeout(self):
        self.is_timeout = True
        self.timeout_fun()

    def handle_langwork(self, result):
        if self.is_timeout == True:
            logger.run.error("'%s' long work '%s' session '%s' aready time out, skip."%(self.machine, self.fun.__name__, self.message['session']))
        else:
            logger.run.debug("ReceiveLongWork : session: '%s',%s" % (self.message['session'], ";".join([str(i).strip() for i in list(result)])))
            self.callID.cancel()
            return self.cb(result)

class MataMachine(type):
    def __new__(cls, name, bases, attrs):
        if 'INIT' not in attrs.keys():
            raise TypeError("INIT method is not implemented")

        def create_myself():
            return type(name, bases, attrs)

        attrs['create_myself'] = create_myself
        return super(MataMachine, cls).__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        if 'LOOP_TIME' in attrs:
            LoopMachine.getInstance().AddMachine(attrs['LOOP_TIME'], attrs['create_myself'])
        else:
            MachineFactory.getInstance().AddMachine(attrs['MID'], attrs['create_myself'])

def MakeRequest(machine_type, origin_message = None):
    message = msg_pds.Message()
    message.head.message_type  = machine_type
    if origin_message == None:
        message.head.session = str(uuid.uuid1())
        message.head.flowno  = 1
    else:
        message.head.session = origin_message.head.session
        message.head.flowno  = origin_message.head.flowno + 1
    return message

def MakeResponse(machine_type, origin_message):
    assert(origin_message != None)
    assert(origin_message.head.message_type == (machine_type - 1))

    return MakeRequest(machine_type, origin_message)
