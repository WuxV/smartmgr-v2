# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
from cli_head import *
from view.view_poolmgr import ViewPoolMgr
import message.mds_pb2 as msg_mds
import message.pds_pb2 as msg_pds
from pdsframe import *

class PoolMgr(BaseMgr):
    def __init__(self, srv=None, params={}):
        self.srv  = srv
        self.opt  = cmd_option['pool']
        self.view = ViewPoolMgr(self.srv)    # 注册视图类

    def cli_list(self, params = {}):
        request = MakeRequest(msg_mds.GET_POOL_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_list_error(request, response)
        return self.view.cli_list(request, response)

    def cli_drop(self, params = {}):
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")
        request = MakeRequest(msg_mds.POOL_DROP_REQUEST)
        request.body.Extensions[msg_mds.pool_drop_request].pool_name = params['pool_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_drop_error(request, response)
        return self.view.cli_drop(request, response)

    def cli_info(self, params = {}):
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")
        request = MakeRequest(msg_mds.GET_POOL_LIST_REQUEST)
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_info_error(request, response)
        return self.view.cli_info(request, response, pool_name=params['pool_name'])

    def cli_add(self, params = {}):
        if not params.has_key('disk_names'):
            return self.view.params_error("Miss disk name parameter")
        attr_items = None
        if params.has_key('attr'):
            try:
                attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in params['attr'].split(',')]
                for attr in attr_items:
                    if attr[0] not in ['extent', 'bucket', 'sippet']:
                        return self.view.params_error("'attr' parameter illegal, support 'extent/bucket/sippet'")
                    if not str(attr[1][:-1]).isdigit():
                        return self.view.params_error("'attr' parameter '%s' illegal" % attr[0])
                    if attr[0] == 'extent' and attr[1][-1].lower() != 'g':
                        return self.view.params_error("'attr' parameter '%s' illegal" % attr[0])
                    if attr[0] == 'bucket' and attr[1][-1].lower() != 'm':
                        return self.view.params_error("'attr' parameter '%s' illegal" % attr[0])
                    if attr[0] == 'sippet' and attr[1][-1].lower() != 'k':
                        return self.view.params_error("'attr' parameter '%s' illegal" % attr[0])
            except:
                return self.view.params_error("Pool 'attr' parameter illegal")

        request = MakeRequest(msg_mds.POOL_ADD_REQUEST)
        request.body.Extensions[msg_mds.pool_add_request].disk_names.append(params['disk_names'])
        if params.has_key('variable') and params['variable'] == True:
            request.body.Extensions[msg_mds.pool_add_request].is_variable = True
        if attr_items != None:
            for attr in attr_items:
                if attr[0] == 'extent':
                    request.body.Extensions[msg_mds.pool_add_request].extent = int(attr[1][:-1])*1024*1024*1024/512
                if attr[0] == 'bucket':
                    request.body.Extensions[msg_mds.pool_add_request].bucket = int(attr[1][:-1])*1024*1024/512
                if attr[0] == 'sippet':
                    request.body.Extensions[msg_mds.pool_add_request].sippet = int(attr[1][:-1])*1024/512
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_add_error(request, response)
        return self.view.cli_add(request, response)

    def cli_config(self, params = {}):
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")

        if not params.has_key('dirty_thresh') and not params.has_key('model') and not params.has_key('level') \
                and not params.has_key('skip_thresh'):
            return self.view.params_error("Miss dirty or model or level or skip parameter")

        if params.has_key('stop_through') and not params.has_key('model'):
            return self.view.params_error("Param '-S' must used with '-m'")

        if params.has_key('dirty_thresh') and params.has_key('model'):
            return self.view.params_error("Not supported setting model and dirty at the same time")
        
        if params.has_key('dirty_thresh') and params.has_key('level'):
            return self.view.params_error("Not supported setting level and dirty at the same time")
        
        if params.has_key('model') and params.has_key('level'):
            return self.view.params_error("Not supported setting level and model at the same time")
        
        request = MakeRequest(msg_mds.POOL_CONFIG_REQUEST)
        request.body.Extensions[msg_mds.pool_config_request].pool_name = params['pool_name']

        # dirty
        if params.has_key('dirty_thresh'):
            dirty_thresh = params['dirty_thresh'].split(",")
            if len(dirty_thresh) != 2 or not str(dirty_thresh[0]).isdigit() or not str(dirty_thresh[1]).isdigit():
                return self.view.params_error("'Dirty' parameter illegal, use [lower,upper]")
            if int(dirty_thresh[0]) > 100 or int(dirty_thresh[1]) > 100:
                return self.view.params_error("'Dirty' parameter illegal, lower or upper max value is 100")
            if int(dirty_thresh[0]) > int(dirty_thresh[1]):
                return self.view.params_error("'Dirty' parameter illegal, lower can't gt then upper value")
            request.body.Extensions[msg_mds.pool_config_request].dirty_thresh.lower = int(dirty_thresh[0])
            request.body.Extensions[msg_mds.pool_config_request].dirty_thresh.upper = int(dirty_thresh[1])

        # model
        if params.has_key('model'):
            model = params['model'].lower()
            if model not in ['through']:
                return self.view.params_error("Pool model parameter illegal, only support through")
            if params.has_key('stop_through') and params['stop_through'] == True:
                request.body.Extensions[msg_mds.pool_config_request].is_stop_through = True
            request.body.Extensions[msg_mds.pool_config_request].pool_cache_model = msg_pds.POOL_CACHE_MODEL_WRITETHROUGH

        # level
        if params.has_key('level'):
            if not str(params['level']).isdigit() or int(params['level']) not in range(11):
                return self.view.params_error("'level' parameter illegal, support 0-10")
            request.body.Extensions[msg_mds.pool_config_request].sync_level = int(params['level'])

        # skip
        if params.has_key('skip_thresh'):
            if not params['skip_thresh'][-1] in ['k', 'K']:
                return self.view.params_error("Please use size unit by 'k'")
            if not str(params['skip_thresh'][:-1]).isdigit() or int(params['skip_thresh'][:-1]) > 1024:
                return self.view.params_error("Param 'skip' is not legal, support 0-1024k")
            request.body.Extensions[msg_mds.pool_config_request].skip_thresh = int(params['skip_thresh'][:-1])

        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_config_error(request, response)
        return self.view.cli_config(request, response)

    def cli_disable(self, params = {}):
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")
        request = MakeRequest(msg_mds.SET_POOL_DISABLE_REQUEST)
        request.body.Extensions[msg_mds.set_pool_disable_request].pool_name = params['pool_name']
        response = self.send(request)
        if response.rc.retcode != 0:
            return self.view.cli_disable_error(request, response)
        return self.view.cli_disable(request, response)

    def cli_rebuild(self, params = {}):
        if not params.has_key('disk_names'):
            return self.view.params_error("Miss disk name parameter")
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")

        request = MakeRequest(msg_mds.POOL_REBUILD_REQUEST)
        request.body.Extensions[msg_mds.pool_rebuild_request].pool_name = params['pool_name']
        request.body.Extensions[msg_mds.pool_rebuild_request].disk_names.append(params['disk_names'])
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_rebuild_error(request, response)
        return self.view.cli_rebuild(request, response)

    def cli_resize(self, params = {}):
        if not params.has_key('pool_name'):
            return self.view.params_error("Miss pool name parameter")
        if not params.has_key('size'):
            return self.view.params_error("Miss pool 'new size' parameter")
        if not params['size'][-1] in ['g', 'G']:
            return self.view.params_error("Please use size unit by 'G'")
        if not str(params['size'][:-1]).isdigit() or int(params['size'][:-1]) == 0:
            return self.view.params_error("Param 'new size' is not legal")

        request = MakeRequest(msg_mds.POOL_RESIZE_REQUEST)
        request.body.Extensions[msg_mds.pool_resize_request].pool_name = params['pool_name']
        request.body.Extensions[msg_mds.pool_resize_request].size      = int(params['size'][:-1])
        response = self.send(request)

        if response.rc.retcode != 0:
            return self.view.cli_resize_error(request, response)
        return self.view.cli_resize(request, response)
