# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import commands
def command(cmd,timeout = 60*10):
    e, res = commands.getstatusoutput("/usr/bin/timeout %s %s" % (timeout, cmd))
    if e == 31744:
        return -2, "subprocess timeout" 
    try:
        return e, str(res).decode("utf-8")
    except:
        return e, str(res)
