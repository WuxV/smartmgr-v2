# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import sys, os, optparse, time

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))

from twisted.internet import reactor
from pdsframe.core.server import MyServerFactory
from pdsframe.core.daemon import Daemon
from pdsframe.core.loop_machine import loop_machine
from pdsframe.common.config import init_config, config
from pdsframe.common.logger import init_logger, logger
from pdsframe.common.dbclient import init_dbservice
from pdsframe.common.common import *

def parse_args():
    usage   = """usage: %prog --action [start|stop|restart|status] --config filename --front"""
    parser = optparse.OptionParser(usage=usage)
    help = "action type"
    parser.add_option('-a', '--action', metavar="<action>", dest="action", type="string", action='store', help=help)

    help = "config file name"
    parser.add_option('-c', '--config', metavar="<config file name>", dest="filename", type="string", action='store', help=help)

    help = "front running"
    parser.add_option('-f', '--front', metavar="<front running>", dest="front", action='store_true', help=help, default=False)
    return parser.parse_args()

class S2SFrameDaemon(Daemon):
    def pre_start(self):

        logger.run.info("==============start==============")

        port  = config.safe_get_int('network', 'listen-port')
        model = config.safe_get('model', 'path')

        if model[len(model)-1] == "/":
            model = model[:len(model)-2] 

        pos = model.rfind('/')

        model_path = model[:pos]
        model_name = model[pos+1:]

        sys.path.append(model_path)

        if config.safe_get('system', 'module').lower() == "mds":
            init_dbservice()

        # 在import的时候,会执行每个服务的init.py的INIT过程
        __import__(model_name)

        reactor.listenTCP(port, MyServerFactory())
        reactor.callWhenRunning(loop_machine)
        reactor.suggestThreadPoolSize(50)

    def run(self):
        print "service started"
        reactor.run()

def check_kernel_flag():
    cmdline = "/proc/cmdline"
    if not os.path.exists(cmdline):
        logger.run.warning("file /proc/cmdline not exist")
        return
    try:
        with open(cmdline, 'r') as f:
            content = f.read()
        if "phg-lock" in content.split() and not os.path.exists("/var/run/phg-unlock"):
            logger.run.info("==============lock by cmdline==============")
            sys.exit(100)
    except Exception as e:
        logger.run.error("Read /proc/cmdline failed:%s" % e)
        return

def main():
    options, args = parse_args()

    if options.action == None:
        print "Miss action params"
        sys.exit(-1)

    if options.filename == None:
        print "Miss config file params"
        sys.exit(-1)

    filename = options.filename
    front    = options.front
    action   = options.action

    if not os.path.exists(filename):
        print "Config file '%s' not exists" % filename
        sys.exit(-1)

    init_config(filename)

    init_logger()

    # 检查kernel标记
    check_kernel_flag()

    module  = config.safe_get("system", "module")
    
    pidfile = "/var/run/smartmgr-%s.pid" % module
    stdlog  = "/var/log/smartmgr/.%s.stdlog" % module
    daemon  = S2SFrameDaemon(pidfile=pidfile, stdout=stdlog, stderr=stdlog, front=front)

    if 'start' == action:
        daemon.start()
    elif 'stop' == action:
        daemon.stop()
    elif 'restart' == action:
        daemon.restart()
    elif 'status' == action:
        if daemon.status():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
       print 'Unknown command'
       sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    main()
