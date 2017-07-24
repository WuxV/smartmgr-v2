# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time

sys.path.append(os.path.abspath(os.path.join(__file__, '../../')))

from pdsframe.common.config import init_config, config
init_config('/root/workspace/pds-mgr/files/conf/test/service.mds.81.ini')

import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

if __name__ == "__main__":
    # for i in range(1000):
    #     mds_request = msg_mds.HeartbeatActiveInstancesRequest()
    #     for j in range(30):
    #         mds_request.instances_ids.append('sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss')
    # print "done"
    # time.sleep(20)
    # sys.exit()

    attach_info = msg_pds.AttachInfo()
    attach_info.node_id      = "xxx"
    iscsimap_init_info_1 = attach_info.iscsimap_info.iscsimap_init_infos.add()
    iscsimap_init_info_1.init_name = "init-1"

    iscsimap_init_info_2 = attach_info.iscsimap_info.iscsimap_init_infos.add()
    iscsimap_init_info_2.init_name = "init-2"

    iscsimap_init_info_3 = attach_info.iscsimap_info.iscsimap_init_infos.add()
    iscsimap_init_info_3.init_name = "init-3"

    iscsimap_init_info_4 = attach_info.iscsimap_info.iscsimap_init_infos.add()
    iscsimap_init_info_4.init_name = "init-4"
    print attach_info
    print dir(attach_info)
    attach_info.iscsimap_info.Clear()
    print attach_info
    sys.exit(1)

    print dir(attach_info.iscsimap_info.iscsimap_init_infos)

    attach_info.iscsimap_info.iscsimap_init_infos.remove(iscsimap_init_info_1)
    print str(attach_info)
    attach_info.iscsimap_info.iscsimap_init_infos.remove(iscsimap_init_info_4)
    print str(attach_info)
    attach_info.iscsimap_info.iscsimap_init_infos.remove(iscsimap_init_info_2)
    print str(attach_info)
    attach_info.iscsimap_info.iscsimap_init_infos.remove(iscsimap_init_info_3)
    print str(attach_info)

    print attach_info.HasField('iscsimap_info')
