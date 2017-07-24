# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import socket, sys, os, struct, json, re, hashlib
from flask import Flask, abort, make_response, request, render_template
import protobuf_json

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
from pdsframe import *

reload(sys)
sys.setdefaultencoding( "utf-8" )

SRBD_KEY    = ['node1_srbd_netcard','node1_srbd_mask','node1_srbd_ip','node1_ipmi_ip','node1_hostname','node2_passwd','node2_hostname','node2_srbd_ip','node2_ipmi_ip']
SRBD_STATUS = ['role_status','con_status', 'disk_status']
ROLE = ['primary','secondary']
ACTION = ['disconnect', 'connect', 'on', 'off']

# version list
# v1.0 => smartmgr 2.0

API_VERSION = "v1.0"
api_url     = lambda base:("/api/%s/%s" % (API_VERSION, base))
pkSize      = len(struct.pack('I', 0))

app = Flask(__name__)

def is_ip(ip):
    if re.search(r'^(\d{1,3}\.){3}\d{1,3}$', ip) == None:
        return False
    items = ip.split('.')
    if items[0] == '0':
        return False
    for item in items:
        if int(item)>255 or int(item)<0:
            return False
    return True

def is_float(str):
    try:
        _ = float(str)
        return True
    except:
        return False

def is_port(port):
    if not str(port).isdigit():
        return False
    if int(str(port)) < 0 or int(str(port)) > 65535:
        return False
    return True

def MESSAGE(msg):
    print msg

def get_response(data, status_code):
    if data.has_key('head'):
        data.pop('head')
    response = make_response("%s\n" % json.dumps(data, indent=4), status_code)
    response.headers.set('Content-Type', 'application/json; charset=utf-8')
    response.headers.set('Server',       'Smartmgr-API/2.3')
    return response

@app.errorhandler(400)
def err_400(error):
    return get_response({'error': 'INVALID REQUEST'}, 400)

@app.errorhandler(401)
def err_401(error):
    return get_response({'error': 'NOT AUTHORIZED'}, 401)

@app.errorhandler(404)
def err_404(error):
    return get_response({'error': 'NOT FOUND'}, 404)

@app.errorhandler(405)
def err_405(error):
    return get_response({'error': 'METHOD NOT ALLOWED'}, 405)

@app.errorhandler(406)
def err_406(error):
    return get_response({'error': 'NOT ACCEPTABLE'}, 406)

@app.errorhandler(500)
def err_500(error):
    return get_response({'error': 'INTERNAL SERVER ERROR'}, 500)

def send(message):
    ip   = config.safe_get('network', 'listen-ip')
    port = config.safe_get('network', 'listen-port')

    # 准备数据
    data = message.SerializeToString()  
    data = struct.pack('I', len(data))+data

    # 发包
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    sock.connect((ip, int(port)))  
    sock.send(data)  

    # 收包
    try:
        data = ""
        while True:
            data += sock.recv(1024)
            if len(data) >= (pkSize + struct.unpack('I', data[:pkSize])[0]):
                break
    except Exception as e:
        MESSAGE("Recv data error : %s" % e)
        abort(500)
    sock.close()  

    # 解析包
    response = msg_pds.Message()
    response.ParseFromString(data[pkSize:len(data)])
    if not response.HasField('rc'):
        MESSAGE("Response miss rc field")
        abort(500)
    return response

# ===================================
# 帮助
# ===================================
# 获取帮助页面
@app.route('/api/help', methods=['GET'])
def help():
    return render_template("help.html")

# ===================================
# 其他
# ===================================
# 获取当前版本信息
@app.route('/api/version', methods=['GET'])
def version():
    return get_response({'version':API_VERSION}, 200)

# ===================================
# 磁盘管理
# ===================================
# 磁盘列表
@app.route(api_url('instances/disks'), methods=['GET'])    
def get_disk_list():
    mds_request = MakeRequest(msg_mds.GET_DISK_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取磁盘的详细信息
@app.route(api_url('instances/disks/<string:disk_name>'), methods=['GET']) 
def get_disk_info(disk_name):
    mds_request = MakeRequest(msg_mds.GET_DISK_INFO_REQUEST)
    mds_request.body.Extensions[msg_mds.get_disk_info_request].node_disk_name = disk_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 磁盘添加
@app.route(api_url('instances/disks'), methods=['POST'])   
def disk_add():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'dev_name' not in request.json:
        MESSAGE("Miss dev_name field")
        abort(400)
    if 'partition_count' in request.json:
        if not str(request.json['partition_count']).isdigit():
            MESSAGE("Illegal partition_count field")
            abort(400)
        if int(request.json['partition_count']) <= 0:
            MESSAGE("Illegal partition_count field")
            abort(400)
    if 'disk_type' in request.json:
        if request.json['disk_type'] not in ['ssd', 'hdd']:
            MESSAGE("Illegal disk_type field")
            abort(400)
        
    mds_request = MakeRequest(msg_mds.DISK_ADD_REQUEST)
    mds_request.body.Extensions[msg_mds.disk_add_request].dev_name            = request.json['dev_name']
    if 'partition_count' in request.json:
        mds_request.body.Extensions[msg_mds.disk_add_request].partition_count = int(str(request.json['partition_count']))
    if 'disk_type' in request.json:
        if str(request.json['disk_type']) == "ssd":
            mds_request.body.Extensions[msg_mds.disk_add_request].disk_type   = msg_pds.DISK_TYPE_SSD
        else:
            mds_request.body.Extensions[msg_mds.disk_add_request].disk_type   = msg_pds.DISK_TYPE_HDD
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 磁盘删除
@app.route(api_url('instances/disks/<string:disk_name>'), methods=['DELETE']) 
def disk_drop(disk_name):
    mds_request = MakeRequest(msg_mds.DISK_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.disk_drop_request].disk_name = disk_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 磁盘点灯(点亮)
@app.route(api_url('instances/disks/<string:ces_addr>/led/onstate'), methods=['PATCH']) 
def disk_ledon(ces_addr):
    mds_request = MakeRequest(msg_mds.DISK_LED_REQUEST)
    mds_request.body.Extensions[msg_mds.disk_led_request].ces_addr = ces_addr
    mds_request.body.Extensions[msg_mds.disk_led_request].is_on    = True
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 磁盘点灯(关闭)
@app.route(api_url('instances/disks/<string:ces_addr>/led/offstate'), methods=['PATCH']) 
def disk_ledoff(ces_addr):
    mds_request = MakeRequest(msg_mds.DISK_LED_REQUEST)
    mds_request.body.Extensions[msg_mds.disk_led_request].ces_addr = ces_addr
    mds_request.body.Extensions[msg_mds.disk_led_request].is_on    = False
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取磁盘快盘测试结果列表
@app.route(api_url('instances/qualitys'), methods=['GET']) 
def get_disk_quality_list():
    mds_request = MakeRequest(msg_mds.GET_DISK_QUALITY_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取指定磁盘快盘测试结果
@app.route(api_url('instances/qualitys/<int:t_time>'), methods=['GET']) 
def get_disk_quality_info(t_time):
    mds_request = MakeRequest(msg_mds.GET_DISK_QUALITY_INFO_REQUEST)
    mds_request.body.Extensions[msg_mds.get_disk_quality_info_request].t_time = t_time
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 磁盘替换
@app.route(api_url('instances/disks/<string:disk_name>/replace'), methods=['PATCH'])
def disk_replace(disk_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'dev_name' not in request.json:
        MESSAGE("Miss dev_name field")
        abort(400)

    mds_request = MakeRequest(msg_mds.DISK_REPLACE_REQUEST)
    mds_request.body.Extensions[msg_mds.disk_replace_request].disk_name = disk_name
    mds_request.body.Extensions[msg_mds.disk_replace_request].dev_name = request.json['dev_name']
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)
# ===================================
# PAL Pool管理
# ===================================
# Pool列表
@app.route(api_url('instances/pools'), methods=['GET'])    
def get_pool_list():
    mds_request = MakeRequest(msg_mds.GET_POOL_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Pool添加
@app.route(api_url('instances/pools'), methods=['POST'])   
def pool_add():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'disk_names' not in request.json:
        MESSAGE("Miss disk_names field")
        abort(400)
    if type(request.json['disk_names']) != type([]):
        MESSAGE("Illegal disk_names field")
        abort(400)
    if len(request.json['disk_names']) != 1:
        MESSAGE("Max support one disk now")
        abort(400)
    if 'extent' in request.json and not str(request.json['extent']).isdigit():
        MESSAGE("Illegal extent field")
        abort(400)
    if 'bucket' in request.json and not str(request.json['bucket']).isdigit():
        MESSAGE("Illegal bucket field")
        abort(400)
    if 'sippet' in request.json and not str(request.json['sippet']).isdigit():
        MESSAGE("Illegal sippet field")
        abort(400)
    is_variable = False
    if 'is_variable' in request.json:
        if type(request.json['is_variable']) != type(True):
            MESSAGE("Illegal is_variable field, support:'true/false'")
            abort(400)
        is_variable = request.json['is_variable']
    mds_request = MakeRequest(msg_mds.POOL_ADD_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_add_request].disk_names.append(request.json['disk_names'][0])
    mds_request_body.Extensions[msg_mds.pool_add_request].is_variable = is_variable
    if 'extent' in request.json:
        mds_request.body.Extensions[msg_mds.pool_add_request].extent = int(str(request.json['extent']))
    if 'bucket' in request.json:
        mds_request.body.Extensions[msg_mds.pool_add_request].bucket = int(str(request.json['bucket']))
    if 'sippet' in request.json:
        mds_request.body.Extensions[msg_mds.pool_add_request].sippet = int(str(request.json['sippet']))
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Pool删除
@app.route(api_url('instances/pools/<string:pool_name>'), methods=['DELETE']) 
def pool_drop(pool_name):
    mds_request = MakeRequest(msg_mds.POOL_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_drop_request].pool_name = pool_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 修改pool容量
@app.route(api_url('instances/pools/<string:pool_name>/size'), methods=['PATCH']) 
def pool_resize(pool_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'size' not in request.json:
        MESSAGE("Miss size field")
        abort(400)
    if not str(request.json['size']).isdigit():
        MESSAGE("Param size illegal")
        abort(400)
    mds_request = MakeRequest(msg_mds.POOL_RESIZE_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_resize_request].pool_name = pool_name
    mds_request.body.Extensions[msg_mds.pool_resize_request].size      = int(request.json['size'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Pool配置dirty_thresh
@app.route(api_url('instances/pools/<string:pool_name>/dirtythresh'), methods=['PATCH']) 
def pool_dirtythresh(pool_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'dirty_thresh_lower' not in request.json:
        MESSAGE("Miss dirty_thresh_lower field")
        abort(400)
    if not request.json or 'dirty_thresh_upper' not in request.json:
        MESSAGE("Miss dirty_thresh_upper field")
        abort(400)
    if not str(request.json['dirty_thresh_lower']).isdigit() or int(request.json['dirty_thresh_lower']) > 100:
        MESSAGE("Param dirty_thresh_lower illegal")
        abort(400)
    if not str(request.json['dirty_thresh_upper']).isdigit() or int(request.json['dirty_thresh_upper']) > 100:
        MESSAGE("Param dirty_thresh_upper illegal")
        abort(400)
    mds_request = MakeRequest(msg_mds.POOL_CONFIG_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_config_request].pool_name = pool_name
    mds_request.body.Extensions[msg_mds.pool_config_request].dirty_thresh.lower = int(request.json['dirty_thresh_lower'])
    mds_request.body.Extensions[msg_mds.pool_config_request].dirty_thresh.upper = int(request.json['dirty_thresh_upper'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Pool配置sync_level
@app.route(api_url('instances/pools/<string:pool_name>/synclevel'), methods=['PATCH']) 
def pool_synclevel(pool_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'sync_level' not in request.json:
        MESSAGE("Miss sync_level field")
        abort(400)
    if not str(request.json['sync_level']).isdigit() or int(request.json['sync_level']) > 10:
        MESSAGE("Param sync_level illegal, support 0-10")
        abort(400)
    mds_request = MakeRequest(msg_mds.POOL_CONFIG_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_config_request].pool_name  = pool_name
    mds_request.body.Extensions[msg_mds.pool_config_request].sync_level = int(request.json['sync_level'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Pool配置cache model
@app.route(api_url('instances/pools/<string:pool_name>/cachemodel'), methods=['PATCH']) 
def pool_cachemodel(pool_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if not request.json or 'cache_model' not in request.json:
        MESSAGE("Miss cache_model field")
        abort(400)
    if request.json['cache_model'].lower() not in ["through"]:
        MESSAGE("Param cache_model illegal, support through")
        abort(400)
    mds_request = MakeRequest(msg_mds.POOL_CONFIG_REQUEST)
    mds_request.body.Extensions[msg_mds.pool_config_request].pool_name        = pool_name
    if 'stop_through' in request.json and type(request.json['stop_through']) == type(True):
        mds_request.body.Extensions[msg_mds.pool_config_request].is_stop_through = True
    mds_request.body.Extensions[msg_mds.pool_config_request].pool_cache_model = msg_pds.POOL_CACHE_MODEL_WRITETHROUGH
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# Lun管理
# ===================================
# Lun列表
@app.route(api_url('instances/luns'), methods=['GET'])    
def get_lun_list():
    mds_request = MakeRequest(msg_mds.GET_LUN_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# Lun添加
@app.route(api_url('instances/luns'), methods=['POST'])   
def lun_add():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    is_pmt = False
    if 'pool_name' in request.json and 'size' in request.json:
        if 'data_disk_name' in request.json or 'cache_disk_name' in request.json or 'basedisk' in request.json:
            MESSAGE("Create pmt lun only support params 'pool' and 'size'")
            abort(400)
        if not str(request.json['size']).isdigit():
            MESSAGE("Param 'new size' is not legal")
            abort(400)
        is_pmt = True

    if is_pmt == False:
        if 'data_disk_name' not in request.json:
            MESSAGE("Miss data_disk_name field")
            abort(400)
        if 'cache_disk_name' in request.json and 'pool_name' in request.json:
            MESSAGE("Not support use cache_disk_name and pool_name at the same time")
            abort(400)

    mds_request      = MakeRequest(msg_mds.LUN_ADD_REQUEST)
    mds_request_body = mds_request.body.Extensions[msg_mds.lun_add_request]
    if is_pmt == True:
        mds_request_body.lun_type  = msg_pds.LUN_TYPE_PALPMT
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].pool_name = request.json['pool_name']
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palpmt].size      = int(request.json['size'])
    if is_pmt == False and 'cache_disk_name' in request.json:
        data_disk_name  = request.json['data_disk_name']
        cache_disk_name = request.json['cache_disk_name']
        mds_request_body.lun_type  = msg_pds.LUN_TYPE_SMARTCACHE
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].data_disk_name  = data_disk_name
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_smartcache].cache_disk_name = cache_disk_name
    if is_pmt == False and 'pool_name' in request.json:
        data_disk_name = request.json['data_disk_name']
        pool_name      = request.json['pool_name']
        mds_request_body.lun_type  = msg_pds.LUN_TYPE_PALCACHE
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].data_disk_name = data_disk_name
        mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palcache].pool_name      = pool_name
    if is_pmt == False and not 'pool_name' in request.json and not 'cache_disk_name' in request.json :
        if 'basedisk' in request.json and type(request.json['basedisk']) == type(True):
            mds_request_body.lun_type  = msg_pds.LUN_TYPE_BASEDISK
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_basedisk].data_disk_name = request.json['data_disk_name']
        else:
            mds_request_body.lun_type  = msg_pds.LUN_TYPE_PALRAW
            mds_request_body.Extensions[msg_mds.ext_lunaddrequest_palraw].data_disk_name = request.json['data_disk_name']

    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# LUN删除
@app.route(api_url('instances/luns/<string:lun_name>'), methods=['DELETE']) 
def lun_drop(lun_name):
    if request.json and 'rebalance' in request.json and not str(request.json['rebalance']).isdigit():
        MESSAGE("Illegal rebalance field")
        abort(400)

    if request.json and 'force' in request.json and not type(request.json['force']) == type(True):
        MESSAGE("Illegal force field")
        abort(400)

    mds_request = MakeRequest(msg_mds.LUN_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.lun_drop_request].lun_name = lun_name
    if request.json and 'rebalance' in request.json:
        mds_request.body.Extensions[msg_mds.lun_drop_request].rebalance_power = int(request.json['rebalance'])
    if request.json and 'force' in request.json:
        mds_request.body.Extensions[msg_mds.lun_drop_request].force = bool(request.json['force'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# LUN上线
@app.route(api_url('instances/luns/<string:lun_name>/onlinestate'), methods=['PATCH']) 
def lun_online(lun_name):
    mds_request = MakeRequest(msg_mds.LUN_ONLINE_REQUEST)
    mds_request.body.Extensions[msg_mds.lun_online_request].lun_name = lun_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# LUN离线
@app.route(api_url('instances/luns/<string:lun_name>/offlinestate'), methods=['PATCH']) 
def lun_offline(lun_name):
    mds_request = MakeRequest(msg_mds.LUN_OFFLINE_REQUEST)
    mds_request.body.Extensions[msg_mds.lun_offline_request].lun_name = lun_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# LUN活跃
@app.route(api_url('instances/luns/<string:lun_name>/active'), methods=['PATCH']) 
def lun_active(lun_name):
    if request.json and 'rebalance' in request.json and not str(request.json['rebalance']).isdigit():
        MESSAGE("Illegal rebalance field")
        abort(400)

    if request.json and 'force' in request.json and not type(request.json['force']) == type(True):
        MESSAGE("Illegal force field")
        abort(400)

    mds_request = MakeRequest(msg_mds.LUN_ACTIVE_REQUEST)
    mds_request.body.Extensions[msg_mds.lun_active_request].lun_name = lun_name
    if request.json and 'rebalance' in request.json:
        mds_request.body.Extensions[msg_mds.lun_active_request].rebalance_power = int(request.json['rebalance'])
    if request.json and 'force' in request.json:
        mds_request.body.Extensions[msg_mds.lun_active_request].force = bool(request.json['force'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# LUN闲置
@app.route(api_url('instances/luns/<string:lun_name>/inactive'), methods=['PATCH']) 
def lun_inactive(lun_name):
    mds_request = MakeRequest(msg_mds.LUN_INACTIVE_REQUEST)
    mds_request.body.Extensions[msg_mds.lun_inactive_request].lun_name = lun_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# QoS管理
# ===================================
# QoS列表
@app.route(api_url('instances/qoss'), methods=['GET'])
def get_qos_list():
    mds_request = MakeRequest(msg_mds.GET_QOS_TEMPLATE_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# QoS模板添加
@app.route(api_url('instances/qoss'), methods=['POST'])
def qos_add():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'template_name' not in request.json or 'items' not in request.json:
        MESSAGE("Miss dev_name/items field")
        abort(400)

    try:
        qos_items = [ (i.split('=')[0], i.split('=')[1]) for i in request.json['items'].split(',')]
    except:
        MESSAGE("QoS 'items' parameter illegal, e.g. read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100")
        abort(400)

    for items in qos_items:
        if items[0] not in ['read-bps', 'read-iops', 'write-bps', 'write-iops']:
            MESSAGE("QoS 'items' parameter not support '%s'" % items[0])
            abort(400)
        if not str(items[1]).isdigit() or int(items[1]) > 1000000000:
            MESSAGE("Param '%s' is not legal" % items[0])
            abort(400)

    mds_request      = MakeRequest(msg_mds.QOS_TEMPLATE_ADD_REQUEST)
    mds_request.body.Extensions[msg_mds.qos_template_add_request].template_name = request.json['template_name']

    for items in qos_items:
        if   items[0] == "read-bps":
            mds_request.body.Extensions[msg_mds.qos_template_add_request].qos_info.read_bps   = int(items[1])
        elif items[0] == "read-iops":
            mds_request.body.Extensions[msg_mds.qos_template_add_request].qos_info.read_iops  = int(items[1])
        elif items[0] == "write-bps":
            mds_request.body.Extensions[msg_mds.qos_template_add_request].qos_info.write_bps  = int(items[1])
        elif items[0] == "write-iops":
            mds_request.body.Extensions[msg_mds.qos_template_add_request].qos_info.write_iops = int(items[1])

    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# QoS模板删除
@app.route(api_url('instances/qoss/<string:template_name>'), methods=['DELETE'])
def qos_drop(template_name):
    mds_request = MakeRequest(msg_mds.QOS_TEMPLATE_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.qos_template_drop_request].template_name = template_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# QoS模板更新
@app.route(api_url('instances/qoss/<string:template_name>/items'), methods=['PATCH'])
def qos_update(template_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'items' not in request.json:
        MESSAGE("Miss items field")
        abort(400)

    try:
        qos_items = [ (i.split('=')[0], i.split('=')[1]) for i in request.json['items'].split(',')]
    except:
        MESSAGE("QoS 'items' parameter illegal, e.g. read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100")
        abort(400)

    for items in qos_items:
        if items[0] not in ['read-bps', 'read-iops', 'write-bps', 'write-iops']:
            MESSAGE("QoS 'items' parameter not support '%s'" % items[0])
            abort(400)
        if not str(items[1]).isdigit() or int(items[1]) > 1000000000:
            MESSAGE("Param '%s' is not legal" % items[0])
            abort(400)

    mds_request      = MakeRequest(msg_mds.QOS_TEMPLATE_UPDATE_REQUEST)
    mds_request.body.Extensions[msg_mds.qos_template_update_request].template_name = template_name

    for items in qos_items:
        if   items[0] == "read-bps":
            mds_request.body.Extensions[msg_mds.qos_template_update_request].qos_info.read_bps   = int(items[1])
        elif items[0] == "read-iops":
            mds_request.body.Extensions[msg_mds.qos_template_update_request].qos_info.read_iops  = int(items[1])
        elif items[0] == "write-bps":
            mds_request.body.Extensions[msg_mds.qos_template_update_request].qos_info.write_bps  = int(items[1])
        elif items[0] == "write-iops":
            mds_request.body.Extensions[msg_mds.qos_template_update_request].qos_info.write_iops = int(items[1])

    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 关联QoS模板
@app.route(api_url('instances/qoss/<string:template_name>/link'), methods=['PATCH'])
def qos_link(template_name):
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'lun_name' not in request.json:
        MESSAGE("Miss lun_name field")
        abort(400)

    mds_request = MakeRequest(msg_mds.LINK_QOS_TEMPLATE_REQUEST)
    mds_request.body.Extensions[msg_mds.link_qos_template_request].template_name = template_name
    mds_request.body.Extensions[msg_mds.link_qos_template_request].lun_name = request.json["lun_name"]
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 取消关联QoS模板
@app.route(api_url('instances/qoss/<string:lun_name>/unlink'), methods=['PATCH'])
def qos_unlink(lun_name):
    mds_request = MakeRequest(msg_mds.UNLINK_QOS_TEMPLATE_REQUEST)
    mds_request.body.Extensions[msg_mds.unlink_qos_template_request].lun_name = lun_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# 节点管理
# ===================================
# 获取节点信息
@app.route(api_url('instances/node'), methods=['GET'])    
def get_node_info():
    mds_request = MakeRequest(msg_mds.GET_NODE_INFO_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取node list，不包含smartmon的node
@app.route(api_url('instances/nodes'), methods=['GET'])    
def get_node_list():
    mds_request = MakeRequest(msg_mds.GET_NODE_LIST_REQUEST)
    mds_request.body.Extensions[msg_mds.get_node_list_request].is_remove_smartmon = True
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 配置节点信息
@app.route(api_url('instances/node'), methods=['PATCH'])   
def node_config():
    if 'node_name' not in request.json:
        MESSAGE("Miss node_name field")
        abort(400)
    mds_request = MakeRequest(msg_mds.NODE_CONFIG_REQUEST)
    mds_request.body.Extensions[msg_mds.node_config_request].node_name = request.json['node_name']
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# License管理
# ===================================
# 获取license信息
@app.route(api_url('license/info'), methods=['GET'])    
def get_license_info():
    mds_request = MakeRequest(msg_mds.GET_LICENSE_INFO_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取license文件
@app.route(api_url('license/file'), methods=['GET'])    
def get_license_file():
    mds_request = MakeRequest(msg_mds.GET_LICENSE_FILE_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 更新license文件
@app.route(api_url('license/file'), methods=['PATCH'])
def put_license_file():
    if 'license_base64' not in request.json:
        MESSAGE("Miss license_base64 field")
        abort(400)
    mds_request = MakeRequest(msg_mds.PUT_LICENSE_FILE_REQUEST)
    mds_request.body.Extensions[msg_mds.put_license_file_request].license_base64 = request.json['license_base64']
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# 配置文件备份管理
# ===================================
# 设置配置文件的第二存储点
@app.route(api_url('instances/storage/<string:second_storage_ip>'), methods=['GET']) 
def set_second_storage(second_storage_ip):
    mds_request = MakeRequest(msg_mds.SET_SECOND_STORAGE_IP_REQUEST)
    mds_request.body.Extensions[msg_mds.set_second_storage_ip_request].second_storage_ip = second_storage_ip
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 获取配置文件的第二存储点
@app.route(api_url('instances/storage/get_ip'), methods=['GET']) 
def get_second_storage():
    mds_request = MakeRequest(msg_mds.GET_SECOND_STORAGE_IP_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# Slot管理
# ===================================
@app.route(api_url('instances/slots'), methods=['GET'])
def get_slot_list():
    mds_request = MakeRequest(msg_mds.GET_SLOT_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# asm磁盘管理
# ===================================
# 获取asm磁盘列表
@app.route(api_url('instances/asmdisks'), methods=['GET'])
def get_asmdisk_list():
    mds_request = MakeRequest(msg_mds.GET_ASMDISK_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 添加asm磁盘
@app.route(api_url('instances/asmdisks'), methods=['POST'])
def asmdisk_add():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'asmdisk_path' not in request.json or 'diskgroup_name' not in request.json:
        MESSAGE("Miss asmdisk_path/diskgroup_name field")
        abort(400)

    if 'rebalance' in request.json and not str(request.json['rebalance']).isdigit():
        MESSAGE("Illegal rebalance field")
        abort(400)

    if 'force' in request.json and not type(request.json['force']) == type(True):
        MESSAGE("Illegal force field")
        abort(400)

    mds_request = MakeRequest(msg_mds.ASMDISK_ADD_REQUEST)
    mds_request.body.Extensions[msg_mds.asmdisk_add_request].asmdisk_path = request.json['asmdisk_path']
    mds_request.body.Extensions[msg_mds.asmdisk_add_request].diskgroup_name = request.json['diskgroup_name']
    if 'rebalance' in request.json:
        mds_request.body.Extensions[msg_mds.asmdisk_add_request].rebalance_power = int(request.json['rebalance'])
    if 'force' in request.json:
        mds_request.body.Extensions[msg_mds.asmdisk_add_request].force = bool(request.json['force'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 删除asm磁盘
@app.route(api_url('instances/asmdisks/<string:asmdisk_name>'), methods=['DELETE'])
def asmdisk_drop(asmdisk_name):
    if request.json and 'rebalance' in request.json and not str(request.json['rebalance']).isdigit():
        MESSAGE("Illegal rebalance field")
        abort(400)

    if request.json and 'force' in request.json and not type(request.json['force']) == type(True):
        MESSAGE("Illegal rebalance field")
        abort(400)

    mds_request = MakeRequest(msg_mds.ASMDISK_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.asmdisk_drop_request].asmdisk_name = asmdisk_name
    if request.json and 'rebalance' in request.json:
        mds_request.body.Extensions[msg_mds.asmdisk_drop_request].rebalance_power = int(request.json['rebalance'])
    if request.json and 'force' in request.json:
        mds_request.body.Extensions[msg_mds.asmdisk_drop_request].force = bool(request.json['force'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# asm磁盘上线
@app.route(api_url('instances/asmdisks/<string:asmdisk_name>/onlinestate'), methods=['PATCH']) 
def asmdisk_online(asmdisk_name):
    mds_request = MakeRequest(msg_mds.ASMDISK_ONLINE_REQUEST)
    mds_request.body.Extensions[msg_mds.asmdisk_online_request].asmdisk_name = asmdisk_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# asm磁盘下线
@app.route(api_url('instances/asmdisks/<string:asmdisk_name>/offlinestate'), methods=['PATCH']) 
def asmdisk_offline(asmdisk_name):
    mds_request = MakeRequest(msg_mds.ASMDISK_OFFLINE_REQUEST)
    mds_request.body.Extensions[msg_mds.asmdisk_offline_request].asmdisk_name = asmdisk_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# asm磁盘组管理
# ===================================
# 获取asm磁盘组列表
@app.route(api_url('instances/diskgroups'), methods=['GET'])
def get_diskgroup_list():
    mds_request = MakeRequest(msg_mds.GET_DISKGROUP_LIST_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 添加asm磁盘组
@app.route(api_url('instances/diskgroups'), methods=['POST'])
def diskgroup_add():
    if request.headers.get('Content-Type') != 'application/json':
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'diskgroup_name' not in request.json or 'asmdisk_paths' not in request.json:
        MESSAGE("Miss diskgroup_name/asmdisk_paths field")
        abort(400)

    if 'redundancy' in request.json and request.json['redundancy'] not in ['external', 'normal', 'high']:
        MESSAGE("Param 'redundancy' is not legal, only support 'external'/'normal'/'high'")
        abort(400)
    
    attr_items = None
    if 'attr' in request.json:
        try:
            attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in request.json['attr'].split(',')]
            for attr in attr_items:
                if attr[0] not in ['compatible.asm', 'compatible.rdbms']:
                    MESSAGE("Param 'attr' is not legal, only support 'compatible.asm'/'compatible.rdbms'")
                    abort(400)
        except:
            MESSAGE("Param 'attr' parameter illegal, e.g. compatible.asm=11.2,compatible.rdbms=11.2")
            abort(400)

    mds_request = MakeRequest(msg_mds.DISKGROUP_ADD_REQUEST)
    mds_request.body.Extensions[msg_mds.diskgroup_add_request].diskgroup_name = request.json['diskgroup_name']
    for path in request.json['asmdisk_paths'].split(','):
        mds_request.body.Extensions[msg_mds.diskgroup_add_request].asmdisk_paths.append(path)
    if 'redundancy' in request.json:
        mds_request.body.Extensions[msg_mds.diskgroup_add_request].redundancy = request.json['redundancy']
    if 'attr' in request.json:
        for attr in attr_items:
            if attr[0] == 'compatible.asm':
                mds_request.body.Extensions[msg_mds.diskgroup_add_request].compatible_asm = attr[1]
            if attr[0] == "compatible.rdbms":
                mds_request.body.Extensions[msg_mds.diskgroup_add_request].compatible_rdbms = attr[1]
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 删除asm磁盘组
@app.route(api_url('instances/diskgroups/<string:diskgroup_name>'), methods=['DELETE']) 
def diskgroup_drop(diskgroup_name):
    mds_request = MakeRequest(msg_mds.DISKGROUP_DROP_REQUEST)
    mds_request.body.Extensions[msg_mds.diskgroup_drop_request].diskgroup_name = diskgroup_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# 修改asm磁盘组
@app.route(api_url('instances/diskgroups/<string:diskgroup_name>/alter'), methods=['PATCH']) 
def diskgroup_alter(diskgroup_name):
    if request.headers.get('Content-Type') != 'application/json':
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)

    if not request.json or 'rebalance' not in request.json:
        MESSAGE("Miss rebalance field")
        abort(400)

    if not str(request.json['rebalance']).isdigit():
        MESSAGE("Illegal rebalance field")
        abort(400)

    mds_request = MakeRequest(msg_mds.DISKGROUP_ALTER_REQUEST)
    mds_request.body.Extensions[msg_mds.diskgroup_alter_request].diskgroup_name = diskgroup_name
    mds_request.body.Extensions[msg_mds.diskgroup_alter_request].rebalance_power = int(request.json['rebalance'])
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# srbd管理
# ===================================
# srbd init
@app.route(api_url('instances/srbd/init'), methods=['PATCH'])    
def srbd_init():
    mds_request = MakeRequest(msg_mds.SRBD_INIT_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# srbd info
@app.route(api_url('instances/srbd/info'), methods=['GET'])    
def srbd_info():
    mds_request = MakeRequest(msg_mds.GET_SRBD_INFO_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# srbd config 配置srbd信息
@app.route(api_url('instances/srbd/config'), methods=['POST'])   
def srbd_config():
    if request.headers.get('Content-Type') != "application/json":
        MESSAGE("Unsupport Content-Type, default:'application/json'")
        abort(406)
    if 'nodeid' in request.json and 'attr' in request.json:
        attr_items = None
        try:
            attr_items = [ (i.split('=')[0], i.split('=')[1]) for i in request.json['attr'].split(',')]
            for attr in attr_items:
                a = request.json['nodeid'] + "_" + attr[0] 
                if a not in SRBD_KEY or attr[0] in SRBD_STATUS:
                    MESSAGE("key parameter illegal")
                    abort(400)
        except:
            MESSAGE("key parameter illegal")
            abort(400)
        mds_request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
        for attr in attr_items:
            if request.json['nodeid'] + "_" + attr[0] in SRBD_KEY and attr[0] not in SRBD_STATUS:
                srbd_config = msg_pds.SrbdConfig()
                srbd_config.nodeid = str(request.json['nodeid'])
                srbd_config.srbd_key = str(request.json['nodeid'] + "_" + attr[0])
                srbd_config.srbd_value = attr[1]
                mds_request.body.Extensions[msg_mds.srbd_config_request].srbd_config.CopyFrom(srbd_config)
        mds_response = send(mds_request)
    elif 'role' in request.json:
        if request.json['role'] not in ROLE: 
            message("key parameter illegal")
            abort(400)
        mds_request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
        mds_request.body.Extensions[msg_mds.srbd_config_request].node_role = request.json['role']
        mds_response = send(mds_request)
    elif "action" in request.json:
        if request.json['action'] not in ACTION: 
            message("key parameter illegal")
            abort(400)
        mds_request = MakeRequest(msg_mds.SRBD_CONFIG_REQUEST)
        mds_request.body.Extensions[msg_mds.srbd_config_request].node_action = request.json['action']
        mds_response = send(mds_request)
    else:
        message("key parameter illegal")
        abort(400)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# srbd 脑裂恢复
@app.route(api_url('instances/srbd/sbr'), methods=['PATCH'])   
def srbd_sbr():
    mds_request = MakeRequest(msg_mds.SRBD_SPLITBRAIN_RECOVERY_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# ===================================
# pcs管理
# ===================================
# pcs init
@app.route(api_url('instances/pcs/init'), methods=['PATCH'])    
def pcs_init():
    mds_request = MakeRequest(msg_mds.PCS_INIT_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# pcs info
@app.route(api_url('instances/pcs/info'), methods=['GET'])    
def pcs_info():
    mds_request = MakeRequest(msg_mds.GET_PCS_INFO_REQUEST)
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# srbd config 配置srbd信息
@app.route(api_url('instances/pcs/config/<string:action>'), methods=['PATCH'])   
def pcs_config(action):
    if action not in ['on', 'off', 'enable', 'disable']:
        MESSAGE("action field")
        abort(400)
    mds_request = MakeRequest(msg_mds.PCS_CONFIG_REQUEST)
    mds_request.body.Extensions[msg_mds.pcs_config_request].action = action
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

# srbd drop 
@app.route(api_url('instances/pcs/drop/<string:stonith_name>'), methods=['DELETE'])   
def pcs_drop_stonith(stonith_name):
    mds_request = MakeRequest(msg_mds.PCS_DROP_STONITH_REQUEST)
    mds_request.body.Extensions[msg_mds.pcs_drop_stonith_request].stonith_name= stonith_name
    mds_response = send(mds_request)
    return get_response(protobuf_json.pb2json(mds_response), 200)

