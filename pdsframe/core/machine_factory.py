# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe.common.Singleton import Singleton

class MachineFactory(Singleton):

    machine_factory = {}

    def __init__(self):
        pass

    def AllMachine(self):
        return MachineFactory.machine_factory

    def AddMachine(self, id, create_fun):
        if not MachineFactory.machine_factory.has_key(id):
            MachineFactory.machine_factory[id] = create_fun
            return 0
        return 1

    def RemoveMachine(self, id):
        if MachineFactory.machine_factory.has_key(id):
            del MachineFactory.machine_factory[id]
            return 0
        return 1

    def NewMachine(self, id):
        if MachineFactory.machine_factory.has_key(id):
            return MachineFactory.machine_factory[id]()
        return None
