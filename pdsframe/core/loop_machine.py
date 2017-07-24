# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, traceback
from twisted.internet import reactor, task
from pdsframe.common.logger import logger
from pdsframe.common.config import config
from pdsframe.common.Singleton import Singleton
from pdsframe.core.client import MyClientFactory

class LoopMachine(Singleton):
    loop_machine = []

    def __init__(self):
        pass

    def AllMachine(self):
        return LoopMachine.loop_machine

    def AddMachine(self, lt, create_fun):
        LoopMachine.loop_machine.append((lt, create_fun))

def loop_machine():
    for lt, create_fun in LoopMachine.getInstance().AllMachine():
        t = task.LoopingCall(create_loop_machine, create_fun)
        t.start(lt)

def create_loop_machine(create_fun):
    Machine = create_fun()
    machine = Machine()

    try:
        machine.INIT()
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        # err  = "\n#####################################\n"
        # err += "# Except e:%s\n" % e
        # err += "#####################################"
        # logger.run.error(err)
