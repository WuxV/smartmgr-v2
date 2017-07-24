# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time

sys.path.append(os.path.abspath(os.path.join(__file__, '../../')))

from pdsframe.common.config import init_config, config
init_config('../files/conf/test/service.ios.215.ini')

from service_ios.base.raid.megaraid import MegaRaid

if __name__ == "__main__":
    print MegaRaid().get_disk_list()
    # print MegaRaid().get_ctl_disk_list(0)
    # print MegaRaid().get_udev_disk_list()
    # for i in range(100):
    #     print "======================================================"
    #     print i
    #     print MegaRaid().get_disk_list()
    #     time.sleep(2)
