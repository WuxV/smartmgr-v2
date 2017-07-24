# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import sys, os, optparse, netifaces

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))

from pdsframe.core.daemon import Daemon
from pdsframe.common.config import init_config, config

from pdsapi import app

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

def check_netconfig(listen_ip):
    ips = [] 
    for i in netifaces.interfaces(): 
        info = netifaces.ifaddresses(i) 
        if netifaces.AF_INET not in info: 
            continue 
        ips.append(info[netifaces.AF_INET][0]['addr']) 
    if listen_ip not in ips:
        print "Error : listen-ip '%s' is not available, please check config : /opt/smartmgr/conf/service.mds.ini" % listen_ip
        sys.exit(1)

class APIDaemon(Daemon):
    def run(self):
        listen_port = int(config.safe_get('model-config', 'api-listen-port'))
        if self.front:
            app.run(debug=True, host="0.0.0.0", port=listen_port)
        else:
            app.run(host="0.0.0.0", port=listen_port)

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

    check_netconfig(config.safe_get('network', 'listen-ip'))

    pidfile = "/var/run/smartmgr-api.pid"
    stdlog  = os.path.join(config.safe_get('log', 'path'), "%s.log" % config.safe_get("model-config","api-log-prefix"))

    daemon  = APIDaemon(pidfile=pidfile, stdout=stdlog, stderr=stdlog, front=front)

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
