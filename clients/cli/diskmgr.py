# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_diskmgr import ViewDiskMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class DiskMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['disk']
        self.view = ViewDiskMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_DISK_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        if params.has_key('part') and params['part'] == True:
            return self.view.cli_list_by_part(request, response)
        return self.view.cli_list(request, response)

    #添加disk_info
    def cli_info(self,params = {}):
        if not params.has_key('disk_name'):
            return self.view.params_error("Miss param 'disk_name'")
        request = MakeRequest(msg_mds.GET_DISK_INFO_REQUEST)
        request.body.Extensions[msg_mds.get_disk_info_request].node_disk_name = params['disk_name']
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_info_error(request,response)
        return self.view.cli_info(request,response)

    def cli_add(self, params = {}):
        if not params.has_key('dev_name'):
            return self.view.params_error("Miss param 'dev_name'")
        if params.has_key('partition_count') and not params['partition_count'].isdigit():
            return self.view.params_error("Param 'partition count' is ilegal")
        if params.has_key('disk_type') and params['disk_type'].lower() not in ["ssd", "hdd"]:
            return self.view.params_error("Param 'disk type' is ilegal, support ssd/hdd")

        request = MakeRequest(msg_mds.DISK_ADD_REQUEST)
        request.body.Extensions[msg_mds.disk_add_request].dev_name = params['dev_name']
        if params.has_key('partition_count'):
            request.body.Extensions[msg_mds.disk_add_request].partition_count = int(params['partition_count'])
        if params.has_key('disk_type'):
            if params['disk_type'].lower() == "ssd":
                request.body.Extensions[msg_mds.disk_add_request].disk_type = msg_pds.DISK_TYPE_SSD
            else:
                request.body.Extensions[msg_mds.disk_add_request].disk_type = msg_pds.DISK_TYPE_HDD
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('disk_name'):
            return self.view.params_error("Miss disk name parameter")
        request = MakeRequest(msg_mds.DISK_DROP_REQUEST)
        request.body.Extensions[msg_mds.disk_drop_request].disk_name = params['disk_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_led(self, params = {}):
        if not params.has_key('action'):
            return self.view.params_error("Miss action parameter")

        if params['action'].lower() not in ['on', 'off']:
            return self.view.params_error("Param 'action' is ilegal")

        if params.has_key('all') and params['all'] == True:
            return self._led_all(params)

        if not params.has_key('ces_addr'):
            return self.view.params_error("Miss disk path parameter")

        items = params['ces_addr'].split(":")
        if len(items) not in [3, 4]:
            return self.view.params_error("Param 'path' is ilegal")

        request = MakeRequest(msg_mds.DISK_LED_REQUEST)
        request.body.Extensions[msg_mds.disk_led_request].ces_addr = params['ces_addr']
        if params['action'].lower() == "on":
            request.body.Extensions[msg_mds.disk_led_request].is_on = True
        else:
            request.body.Extensions[msg_mds.disk_led_request].is_on = False

        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_led_error(request, response)
        return self.view.cli_led(request, response)

    def _led_all(self, params):
        request = MakeRequest(msg_mds.GET_DISK_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_led_error(request, response)

        todo_led_ces = []
        for disk_info in response.body.Extensions[msg_mds.get_disk_list_response].disk_infos:
            if disk_info.HasField('raid_disk_info'):
                todo_led_ces.append("%s:%s:%s" % (disk_info.raid_disk_info.ctl, disk_info.raid_disk_info.eid, disk_info.raid_disk_info.slot))

        todo_led_ces.sort()
        for ces in todo_led_ces:
            out = ""
            out += "Sed disk light %-7s to %s ... " % (ces, params['action'].upper())
            request = MakeRequest(msg_mds.DISK_LED_REQUEST)
            request.body.Extensions[msg_mds.disk_led_request].ces_addr = ces
            if params['action'].lower() == "on": request.body.Extensions[msg_mds.disk_led_request].is_on = True
            else: request.body.Extensions[msg_mds.disk_led_request].is_on = False
            response = self.send(request)
            if response.rc.retcode != 0:
                out += self.view.out_error("FAILED")
            else:
                out += self.view.out_success("SUCCESS")
            print out
        return "Done"

    # 磁盘性能测试
    def cli_quality(self, params = {}):
        # 检查参数
        if not params.has_key("info") and not params.has_key("test") and not params.has_key("list"):
            return self.view.params_error('miss option type, info/test/list?')
        if "info" in params.keys() and ("test" in params.keys() or "list" in params.keys()):
            return self.view.params_error('info option params failed ')
        if "test" in params.keys() and ("info" in params.keys() or "list" in params.keys()):
            return self.view.params_error('test option params failed ')
        if "list" in params.keys() and ("info" in params.keys() or "test" in params.keys()):
            return self.view.params_error('list option params failed ')

        # info
        if "info" in params.keys():
            try:
                t_time = int(time.mktime(time.strptime(params['info'], '%Y-%m-%d.%H:%M:%S')))
            except:
                return self.view.params_error("param info '%s' is illegal" % params['info'])
            request = MakeRequest(msg_mds.GET_DISK_QUALITY_INFO_REQUEST)
            request.body.Extensions[msg_mds.get_disk_quality_info_request].t_time = t_time
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_quality_error(request, response)
            return self.view.cli_quality_info(request, response)
        # test
        if "test" in params.keys():
            if "force" not in params.keys():
                return self.view.params_error('IO quality test will affect the front-end business, use [-f] to start quality test')
            request = MakeRequest(msg_mds.DISK_QUALITY_TEST_REQUEST)
            request.body.Extensions[msg_mds.disk_quality_test_request].force = True
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_quality_error(request, response)
            return self.view.cli_quality_test(request, response)
        # list
        if "list" in params.keys():
            request = MakeRequest(msg_mds.GET_DISK_QUALITY_LIST_REQUEST)
            response = self.send(request)
            if response.rc.retcode != 0:
                return self.view.cli_quality_error(request, response)
            return self.view.cli_quality_list(request, response)

    def cli_replace(self, params = {}):
        if not params.has_key('disk_name'):
            return self.view.params_error("Miss disk name parameter")
        if not params.has_key('dev_name'):
            return self.view.params_error("Miss param 'dev_name'")
        request = MakeRequest(msg_mds.DISK_REPLACE_REQUEST)
        request.body.Extensions[msg_mds.disk_replace_request].disk_name = params['disk_name']
        request.body.Extensions[msg_mds.disk_replace_request].dev_name = params['dev_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_replace_error(request, response)
        return self.view.cli_replace(request, response)
