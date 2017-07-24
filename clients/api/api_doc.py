#coding:utf-8
api_items = [
    ### other
    {
        'role':['storage', 'merge', 'merge-e','database'],
        'platform':['pbdata', 'generic'],
        'type':"其他",
        'title':'获取API版本',
        'url':'GET : http://<ip:port>/api/version',
        'href':'version',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
            {
                'name':'version',
                'type':'string',
                'must':True,
                'info':'RESTful api 版本信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/version \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 26 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:22:18 GMT \n\
 \n\
{ \n\
    "version": "v1.0" \n\
} \n\
'
    },
    ### node list(不包含smartmon-server)       
    {
        'role':['storage', 'merge', 'merge-e','database'],
        'platform':['pbdata', 'generic'],
        'type':"节点管理",
        'title':'获取节点列表(不包含smartmon-server)',
        'url':'GET : http://<ip:port>/api/<version>/instances/nodes',
        'href':'get_node_list',
        'req_attr': 
        [
            {
                'name':'is_remove_smartmon',
                'type':'bool',
                'must':True,
                'info':'判断是否去除smartmon的node list',
            },
        ],
        'res_attr': 
        [
            {
                'name':'get_node_list_response',
                'type':'GetNodeListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'nsnode_infos',
                'type':'NSNodeInfo',
                'must':True,
                'info':'节点列表详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/nodes \n\
',
        'res_demo':'\
HTTP/1.0 200 OK\n\
Content-Type: application/json; charset=utf-8\n\
Content-Length: 1209\n\
Server: Smartmgr-API/2.3\n\
Date: Fri, 06 Jan 2017 02:01:51 GMT\n\
\n\
{\n\
    "body": {\n\
        "get_node_list_response": {\n\
            "nsnode_infos": [\n\
                {\n\
                    "broadcast_ip": "172.16.9.214", \n\
                    "listen_ip": "172.16.9.214", \n\
                    "listen_port": 9003, \n\
                    "node_name": "su214", \n\
                    "platform": "pbdata", \n\
                    "node_status": 1, \n\
                    "last_broadcast_time": 1483668104, \n\
                    "host_name": "dntosu214", \n\
                    "sys_mode": "storage", \n\
                    "node_uuid": "1a707816-c04d-11e6-8c60-525400bcd2d0"\n\
                }, \n\
                {\n\
                    "broadcast_ip": "172.16.9.215", \n\
                    "listen_ip": "172.16.9.215", \n\
                    "listen_port": 9003, \n\
                    "node_name": "du215", \n\
                    "platform": "generic", \n\
                    "node_status": 1, \n\
                    "last_broadcast_time": 1483668104, \n\
                    "host_name": "dntodu215", \n\
                    "sys_mode": "database", \n\
                    "node_uuid": "2a707816-c04d-11e6-8c60-525400bcd2d0"\n\
                }\n\
            ]\n\
        }\n\
    }, \n\
    "rc": {\n\
        "retcode": 0\n\
    }\n\
}\n\
'
    },

    ### node config     
    {
        'role':['storage', 'merge', 'merge-e','database'],
        'platform':['pbdata', 'generic'],
        'type':"节点管理",
        'title':'节点配置',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/node',
        'href':'node_config',
        'req_attr': 
        [
            {
                'name':'node_name',
                'type':'string',
                'must':True,
                'info':'节点ID, 此id为存储节点映射出来lun名字的前缀',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/node -X PATCH  \n\
    -H "Content-Type: application/json"  \n\
    -d \'{"node_name":"su002"}\' \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:54:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### node info       
    {
        'role':['storage', 'merge', 'merge-e','database'],
        'platform':['pbdata', 'generic'],
        'type':"节点管理",
        'title':'获取节点信息',
        'url':'GET : http://<ip:port>/api/<version>/instances/node',
        'href':'get_node_info',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_node_info_response',
                'type':'GetNodeInfoResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'node_info',
                'type':'NodeInfo',
                'must':True,
                'info':'节点详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/node \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 323 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:53:26 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_node_info_response": { \n\
            "node_info": { \n\
                "node_name": "su002" \n\
            } \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### disk add        
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'添加磁盘',
        'url':'POST : http://<ip:port>/api/<version>/instances/disks',
        'href':'disk_add',
        'req_attr': 
        [
            {
                'name':'dev_name',
                'type':'string',
                'must':True,
                'info':'磁盘路径, 1.标准机型:使用ces地址; 2.通用机型:使用/dev设备名称',
            },
            {
                'name':'partition_count',
                'type':'uint32',
                'must':False,
                'info':'初始化时, 分区数量, 未指定情况下, 默认为1个分区',
            },
            {
                'name':'disk_type',
                'type':'string',
                'must':False,
                'info':'磁盘类型, 支持hdd/ssd, 当为通用机型的时候, 需要使用该字段标示磁盘类型; 或添加flash卡的时候, 使用该字段标示为SSD类型',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks -X POST  \n\
    -H "Content-Type: application/json" \n\
    -d \'{"dev_name":"1:1:0", "partition_count":2}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:33:42 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### disk drop       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'删除磁盘',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/disks/<string:node_disk_logical_id>',
        'href':'disk_drop',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks/sd01 -X DELETE  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:37:24 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### disk list       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'获取磁盘列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/disks',
        'href':'get_disk_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_disk_list_response',
                'type':'GetDiskListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)disk_infos',
                'type':'DiskInfo',
                'must':False,
                'info':'磁盘信息',
            },
            {
                'name':'(array)raid_disk_infos',
                'type':'RaidDiskInfo',
                'must':False,
                'info':'系统当前认到的raid设备',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.1/instances/disks \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 12971 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:35:55 GMT \n\
 \n\
head { \n\
  message_type: 20031 \n\
  session: "1d9848f4-80ae-11e6-8619-002590e83916" \n\
  flowno: 2 \n\
} \n\
body { \n\
  [pds.mds.get_disk_list_response] { \n\
    disk_infos { \n\
      disk_name: "hd01" \n\
      dev_name: "/dev/sdi" \n\
      disk_type: DISK_TYPE_HDD \n\
      size: 5859373056 \n\
      diskparts { \n\
        disk_part: 1 \n\
        size: 1953124352 \n\
        dev_name: "/dev/sdi1" \n\
        last_heartbeat_time: 1474539591 \n\
        actual_state: true \n\
      } \n\
      diskparts { \n\
        disk_part: 2 \n\
        size: 1953124352 \n\
        dev_name: "/dev/sdi2" \n\
        last_heartbeat_time: 1474539591 \n\
        actual_state: true \n\
      } \n\
      diskparts { \n\
        disk_part: 3 \n\
        size: 1953120223 \n\
        dev_name: "/dev/sdi3" \n\
        last_heartbeat_time: 1474539591 \n\
        actual_state: true \n\
      } \n\
      header { \n\
        uuid: "b2ec6d1c-809b-11e6-b5da-002590e83916" \n\
      } \n\
      actual_state: true \n\
      last_heartbeat_time: 1474539591 \n\
      raid_disk_info { \n\
        raid_type: RAID_TYPE_MEGARAID \n\
        ctl: 0 \n\
        eid: 16 \n\
        slot: 11 \n\
        drive_type: "hdd" \n\
        protocol: "sas" \n\
        pci_addr: "0000:05:00.0" \n\
        size: "2.727 TB" \n\
        model: "ST3000NM0023" \n\
        state: "Onln" \n\
        dev_name: "/dev/sdi" \n\
        last_heartbeat_time: 1474539591 \n\
        health: "PASS" \n\
        hdd_diskhealth_info { \n\
          verifies_gb: "218033.353" \n\
          life_left: "-" \n\
          uncorrected_reads: "0" \n\
          uncorrected_verifies: "0" \n\
          corrected_reads: "36941627" \n\
          load_cycle_pct_left: "100%" \n\
          load_cycle_count: "1142" \n\
          corrected_writes: "0" \n\
          non_medium_errors: "-" \n\
          reads_gb: "10.826" \n\
          load_cycle_spec: "300000" \n\
          start_stop_pct_left: "100%" \n\
          uncorrected_writes: "0" \n\
          start_stop_spec: "10000" \n\
          corrected_verifies: "903550913" \n\
          start_stop_cycles: "681" \n\
        } \n\
      } \n\
      [pds.mds.ext_diskinfo_free_size]: 5859373056 \n\
    } \n\
    disk_infos { \n\
      dev_name: "/dev/sdh" \n\
      size: 5859373056 \n\
      diskparts { \n\
        disk_part: 1 \n\
        size: 2929686528 \n\
        dev_name: "/dev/sdh1" \n\
      } \n\
      diskparts { \n\
        disk_part: 2 \n\
        size: 2929680351 \n\
        dev_name: "/dev/sdh2" \n\
      } \n\
      header { \n\
        uuid: "73df6016-7f1f-11e6-bca5-002590e83916" \n\
      } \n\
      last_heartbeat_time: 1474539591 \n\
      raid_disk_info { \n\
        raid_type: RAID_TYPE_MEGARAID \n\
        ctl: 0 \n\
        eid: 16 \n\
        slot: 10 \n\
        drive_type: "hdd" \n\
        protocol: "sas" \n\
        pci_addr: "0000:05:00.0" \n\
        size: "2.727 TB" \n\
        model: "ST3000NM0023" \n\
        state: "Onln" \n\
        dev_name: "/dev/sdh" \n\
        last_heartbeat_time: 1474539591 \n\
        health: "PASS" \n\
        hdd_diskhealth_info { \n\
          verifies_gb: "58779.204" \n\
          life_left: "-" \n\
          uncorrected_reads: "0" \n\
          uncorrected_verifies: "0" \n\
          corrected_reads: "245705368" \n\
          load_cycle_pct_left: "100%" \n\
          load_cycle_count: "937" \n\
          corrected_writes: "0" \n\
          non_medium_errors: "-" \n\
          reads_gb: "91.625" \n\
          load_cycle_spec: "300000" \n\
          start_stop_pct_left: "100%" \n\
          uncorrected_writes: "0" \n\
          start_stop_spec: "10000" \n\
          corrected_verifies: "3670801499" \n\
          start_stop_cycles: "486" \n\
        } \n\
      } \n\
      [pds.mds.ext_diskinfo_free_size]: 5859373056 \n\
    } \n\
  } \n\
} \n\
rc { \n\
  retcode: 0 \n\
} \n\
'
    },
    ### get disk info
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'获取指定磁盘的详细信息',
        'url':'GET : http://<ip:port>/api/<version>/instances/disks/<string:disk_name>',
        'href':'get_disk_info',
        'req_attr': 
        [
            {
                'name':'disk_name',
                'type':'string',
                'must':True,
                'info':'磁盘名，如hd01，sd01',
            },
        ],
        'res_attr': 
        [
            {
                'name':'get_disk_info_response',
                'type':'GetDiskInfoResponse',
                'must':False,
                'info':'磁盘的详细信息',
            },
        ],

        'response' :
        [
            {
                'name':'disk_info',
                'type':'DiskInfo',
                'must':False,
                'info':'磁盘的详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks/hd01 \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 77  \n\
Server: Smartmgr-API/2.3 \n\
Date: Thu, 22 Sep 2016 06:54:46 GMT \n\
 \n\
head { \n\
  message_type: 20091 \n\
  session: "3d6639de-80b8-11e6-b4b7-002590e83916" \n\
  flowno: 2 \n\
} \n\
body { \n\
  [pds.mds.get_disk_info_response] { \n\
    disk_info { \n\
      disk_name: "hd01" \n\
      dev_name: "/dev/sdi" \n\
      disk_type: DISK_TYPE_HDD \n\
      size: 5859373056 \n\
      diskparts { \n\
        disk_part: 1 \n\
        size: 1953124352 \n\
        dev_name: "/dev/sdi1" \n\
        last_heartbeat_time: 1474543945 \n\
        actual_state: true \n\
      } \n\
      diskparts { \n\
        disk_part: 2 \n\
        size: 1953124352 \n\
        dev_name: "/dev/sdi2" \n\
        last_heartbeat_time: 1474543945 \n\
        actual_state: true \n\
      } \n\
      diskparts { \n\
        disk_part: 3 \n\
        size: 1953120223 \n\
        dev_name: "/dev/sdi3" \n\
        last_heartbeat_time: 1474543945 \n\
        actual_state: true \n\
      } \n\
      header { \n\
        uuid: "b2ec6d1c-809b-11e6-b5da-002590e83916" \n\
      } \n\
      actual_state: true \n\
      last_heartbeat_time: 1474543945 \n\
      raid_disk_info { \n\
        raid_type: RAID_TYPE_MEGARAID \n\
        ctl: 0 \n\
        eid: 16 \n\
        slot: 11 \n\
        drive_type: "hdd" \n\
        protocol: "sas" \n\
        pci_addr: "0000:05:00.0" \n\
        size: "2.727 TB" \n\
        model: "ST3000NM0023" \n\
        state: "Onln" \n\
        dev_name: "/dev/sdi" \n\
        last_heartbeat_time: 1474543945 \n\
        health: "PASS" \n\
        hdd_diskhealth_info { \n\
          verifies_gb: "218033.353" \n\
          life_left: "-" \n\
          uncorrected_reads: "0" \n\
          uncorrected_verifies: "0" \n\
          corrected_reads: "36997932" \n\
          load_cycle_pct_left: "100%" \n\
          load_cycle_count: "1142" \n\
          corrected_writes: "0" \n\
          non_medium_errors: "-" \n\
          reads_gb: "10.841" \n\
          load_cycle_spec: "300000" \n\
          start_stop_pct_left: "100%" \n\
          uncorrected_writes: "0" \n\
          start_stop_spec: "10000" \n\
          corrected_verifies: "903550913" \n\
          start_stop_cycles: "681" \n\
        } \n\
      } \n\
    } \n\
  } \n\
} \n\
rc { \n\
  retcode: 0 \n\
} \n\
'    },
    ### disk led off       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'关闭磁盘raid灯',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/disks/<ces_addr>/led/offstate',
        'href':'disk_ledoff',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks/0:30:0/led/offstate -X PATCH  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:40:03 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### disk led on       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'点亮磁盘raid灯',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/disks/<ces_addr>/led/onstate',
        'href':'disk_ledon',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks/0:30:0/led/onstate -X PATCH  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:40:03 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### get disk qualitys list
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'获取磁盘性能测试结果列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/qualitys',
        'href':'get_disk_quality_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_disk_quality_list_response',
                'type':'GetDiskQualityListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)disk_quality_infos',
                'type':'DiskQualityInfo',
                'must':True,
                'info':'磁盘性能测试结果详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qualitys  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 923 \n\
Server: Smartmgr-API/2.3 \n\
Date: Tue, 20 Sep 2016 05:56:51 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_disk_quality_list_response": { \n\
            "disk_quality_infos": [ \n\
                { \n\
                    "t_time": 1474380007,  \n\
                    "disk_count": 2,  \n\
                    "run_time": 120,  \n\
                    "ioengine": "libaio",  \n\
                    "block_size": "4k",  \n\
                    "iodepth": 8,  \n\
                    "num_jobs": 32 \n\
                },  \n\
                { \n\
                    "t_time": 1474350007,  \n\
                    "disk_count": 2,  \n\
                    "run_time": 120,  \n\
                    "ioengine": "libaio",  \n\
                    "block_size": "4k",  \n\
                    "iodepth": 8,  \n\
                    "num_jobs": 32 \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### get disk qualitys info
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'获取指定磁盘性能测试结果信息',
        'url':'GET : http://<ip:port>/api/<version>/instances/qualitys/<int:t_time>',
        'href':'get_disk_quality_info',
        'req_attr': 
        [
            {
                'name':'t_time',
                'type':'uint64',
                'must':True,
                'info':'测试时间, 该值为获取磁盘性能测试结果列表中任一项的t_time',
            },
        ],
        'res_attr': 
        [
            {
                'name':'get_disk_quality_info_response',
                'type':'GetDiskQualityInfoResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'disk_quality_info',
                'type':'DiskQualityInfo',
                'must':False,
                'info':'磁盘性能测试结果详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qualitys/1474350007  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 1052 \n\
Server: Smartmgr-API/2.3 \n\
Date: Tue, 20 Sep 2016 05:54:46 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_disk_quality_info_response": { \n\
            "disk_quality_info": { \n\
                "quality_test_result": [ \n\
                    { \n\
                        "path": "/dev/sdn",  \n\
                        "name": "sd01",  \n\
                        "randread_iops": 50150,  \n\
                        "read_bw": 491637 \n\
                    },  \n\
                    { \n\
                        "path": "/dev/sdo",  \n\
                        "name": "sd02",  \n\
                        "randread_iops": 49646,  \n\
                        "read_bw": 490789 \n\
                    } \n\
                ],  \n\
                "t_time": 1474350007,  \n\
                "disk_count": 2,  \n\
                "run_time": 120,  \n\
                "ioengine": "libaio",  \n\
                "block_size": "4k",  \n\
                "iodepth": 8,  \n\
                "num_jobs": 32 \n\
            } \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### disk replace 
    {
        'role':['storage', 'merge'],
        'platform':['pbdata', 'generic'],
        'type':"磁盘管理",
        'title':'磁盘替换',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/disks/hd01/replace',
        'href':'disk_replace',
        'req_attr':
        [
            {
                'name':'dev_name',
                'type':'string',
                'must':True,
                'info':'要替换的磁盘路径, 1.标准机型:使用ces地址; 2.通用机型:使用/dev设备名称',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/disks/hd01/replace -X PATCH  \n\
    -H "Content-Type: application/json" \n\
    -d \'{"dev_name":"1:1:0"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:40:03 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun add        
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'添加Lun',
        'url':'POST : http://<ip:port>/api/<version>/instances/luns',
        'href':'lun_add',
        'req_attr': 
        [
            {
                'name':'data_disk_name',
                'type':'string',
                'must':False,
                'info':'创建PAL-CACHE/PAL-RAW/BaseDisk/SmartCache类型卷时, 指定数据磁盘',
            },
            {
                'name':'basedisk',
                'type':'bool',
                'must':False,
                'info':'以裸盘方式创建lun, 指定该参数为PAL-RAW类型卷, 否则为BaseDisk类型卷',
            },
            {
                'name':'cache_disk_name',
                'type':'string',
                'must':False,
                'info':'创建SmartCache类型卷的时候, 指定Cache磁盘名称',
            },
            {
                'name':'pool_name',
                'type':'string',
                'must':False,
                'info':'创建PAL-CACHE/PAL-PMT类型卷时, 指定使用的pool名称',
            },
            {
                'name':'size',
                'type':'uint32',
                'must':False,
                'info':'创建PAL-PMT类型卷时, 指定卷的大小',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns -X POST \n\
    -H "Content-Type: application/json" \n\
    -d \'{"data_disk_name":"hd01p2", "pool_name":"pool01"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:50:42 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun drop       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'删除Lun',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/luns/<string:lun_name>',
        'href':'lun_drop',
        'req_attr': 
        [
            {
                'name':'rebalance',
                'type':'uint32',
                'must':False,
                'info':'删除active的lun，可以指定asm平衡度级别',
            },
            {
                'name':'force',
                'type':'bool',
                'must':False,
                'info':'强制删除lvvote/active的lun',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns/su001_lun03 -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:43 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun list       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'获取Lun列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/luns',
        'href':'get_lun_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_lun_list_response',
                'type':'GetLunListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)lun_infos',
                'type':'LunInfo',
                'must':True,
                'info':'Lun详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 3669 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:51:11 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_lun_list_response": { \n\
            "lun_infos": [ \n\
                { \n\
                    "config_state": true,  \n\
                    "lun_name": "lun01",  \n\
                    "ext_luninfo_node_name": "su000",  \n\
                    "ext_luninfo_data_disk_name": "hd01p1",  \n\
                    "ext_luninfo_lun_export_info": { \n\
                        "lun_name": "su000_lun01",  \n\
                        "t10_dev_id": "843c07f6-65b7-11e6-acfa",  \n\
                        "threads_num": 1,  \n\
                        "threads_pool_type": "per_initiator",  \n\
                        "io_error": 0,  \n\
                        "last_errno": 0,  \n\
                        "filename": "/dev/sdc1",  \n\
                        "size_mb": 1430511,  \n\
                        "exported": [ \n\
                            { \n\
                                "value": "0",  \n\
                                "key": "f452:1403:0021:7950" \n\
                            },  \n\
                            { \n\
                                "value": "0",  \n\
                                "key": "f452:1403:001b:5b10" \n\
                            } \n\
                        ] \n\
                    },  \n\
                    "actual_state": true,  \n\
                    "ext_luninfo_basedisk_id": "843c02ec-65b7-11e6-acfa-001e67ed992c",  \n\
                    "ext_luninfo_data_dev_name": "/dev/sdc1",  \n\
                    "lun_id": "843c07f6-65b7-11e6-acfa-001e67ed992c",  \n\
                    "last_heartbeat_time": 1471575069,  \n\
                    "lun_type": 2,  \n\
                    "ext_luninfo_size": 2929686528,  \n\
                    "ext_luninfo_scsiid": "xx" \n\
                },  \n\
                { \n\
                    "config_state": true,  \n\
                    "lun_name": "lun02",  \n\
                    "ext_luninfo_node_name": "su000",  \n\
                    "ext_luninfo_target_id": "a09f7260-bb0e-9f4f-9645-27121b28260a",  \n\
                    "ext_luninfo_lun_export_info": { \n\
                        "lun_name": "su000_lun02",  \n\
                        "t10_dev_id": "b7f4d1a4-65b7-11e6-acfa",  \n\
                        "threads_num": 1,  \n\
                        "threads_pool_type": "per_initiator",  \n\
                        "io_error": 0,  \n\
                        "last_errno": 0,  \n\
                        "filename": "/dev/target01",  \n\
                        "size_mb": 1430507,  \n\
                        "exported": [ \n\
                            { \n\
                                "value": "1",  \n\
                                "key": "f452:1403:0021:7950" \n\
                            },  \n\
                            { \n\
                                "value": "1",  \n\
                                "key": "f452:1403:001b:5b10" \n\
                            } \n\
                        ] \n\
                    },  \n\
                    "actual_state": true,  \n\
                    "ext_luninfo_data_dev_name": "/dev/sdc2",  \n\
                    "lun_id": "b7f4d1a4-65b7-11e6-acfa-001e67ed992c",  \n\
                    "ext_luninfo_cache_dev_name": [ \n\
                        "/dev/sda1" \n\
                    ],  \n\
                    "ext_luninfo_cache_disk_name": "pool01",  \n\
                    "ext_luninfo_cache_size": 468857999,  \n\
                    "last_heartbeat_time": 1471575069,  \n\
                    "lun_type": 3,  \n\
                    "ext_luninfo_data_disk_name": "hd01p2",  \n\
                    "ext_luninfo_size": 2929680351,  \n\
                    "ext_luninfo_scsiid": "xx" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun online
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'设置Lun上线',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/luns/<string:lun_name>/onlinestate',
        'href':'lun_online',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns/su000_lun01/onlinestate -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:23 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun offline       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'设置Lun离线',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/luns/<string:lun_name>/offlinestate',
        'href':'lun_online',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns/su000_lun01/offlinestate -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:02 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun active
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'设置Lun活跃',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/luns/<string:lun_name>/active',
        'href':'lun_active',
        'req_attr': 
        [
            {
                'name':'rebalance',
                'type':'uint32',
                'must':False,
                'info':'激活不在asm里的lun，可以指定asm平衡度级别',
            },
            {
                'name':'force',
                'type':'bool',
                'must':False,
                'info':'强制激活不在asm里的lun',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns/su000_lun01/active -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:02 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### lun inactive
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Lun管理",
        'title':'设置Lun闲置',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/luns/<string:lun_name>/inactive',
        'href':'lun_inactive',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/luns/su000_lun01/inactive -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:02 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos add
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'添加QoS模板',
        'url':'POST : http://<ip:port>/api/<version>/instances/qoss',
        'href':'qos_add',
        'req_attr':
        [
            {
                'name':'template_name',
                'type':'string',
                'must':True,
                'info': '模板名',
            },
            {
                'name':'items',
                'type':'string',
                'must':True,
                'info': 'qos项，支持的有read-iops/read-bps/write-iops/write-bps',
            },
        ],
        'res_attr':
        [
        ],
        'response':
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss -X POST \n\
    -H "Content-Type: application/json" \n\
    -d \'{"template_name":"template_001","items":"read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos drop
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'删除QoS模板',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/qoss/<string:template_name>',
        'href':'qos_drop',
        'req_attr':
        [
        ],
        'res_attr':
        [
        ],
        'response':
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss/template_001 -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos update
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'更新QoS模板',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/qoss/<string:template_name>/items',
        'href':'qos_update',
        'req_attr':
        [
            {
                'name':'items',
                'type':'string',
                'must':True,
                'info': 'qos项，可更新的有read-iops/read-bps/write-iops/write-bps',
            },
        ],
        'res_attr':
        [
        ],
        'response':
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss/template_001/items -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"items":"read-bps=1048576,read-iops=100,write-bps=1048576,write-iops=100"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos list
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'获取QoS模板列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/qoss',
        'href':'qos_list',
        'req_attr':
        [
        ],
        'res_attr':
        [
            {
                'name':'get_qos_template_list_response',
                'type':'GetQosTemplateListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response':
        [
            {
                'name':'(array)qos_template_infos',
                'type':'QosTemplateInfo',
                'must':True,
                'info':'QoS模板详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 1155 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 20 Jan 2017 10:27:40 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_qos_template_list_response": { \n\
            "template_infos": [ \n\
                { \n\
                    "template_name": "template_001", \n\
                    "qos_info": { \n\
                        "read_bps": 1048576, \n\
                        "write_bps": 1048576, \n\
                        "read_iops": 10000, \n\
                        "write_iops": 9999 \n\
                    }, \n\
                    "template_id": "7a693d5a-de63-11e6-931b-001e67ed9bd8" \n\
                }, \n\
                { \n\
                    "template_name": "template_003", \n\
                    "qos_info": { \n\
                        "read_bps": 1048576, \n\
                        "write_bps": 0, \n\
                        "read_iops": 100, \n\
                        "write_iops": 0 \n\
                    }, \n\
                    "template_id": "9d2fa664-de57-11e6-98c8-001e67ed9bd8", \n\
                    "lun_names": [ \n\
                        "lun02", \n\
                        "lun04", \n\
                        "lun05", \n\
                        "lun06" \n\
                    ] \n\
                } \n\
            ] \n\
        } \n\
    }, \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos link
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'关联QoS模板',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/qoss/<string:template>/link',
        'href':'qos_link',
        'req_attr':
        [
            {
                'name':'lun_name',
                'type':'string',
                'must':True,
                'info': '逻辑卷名',
            },
        ],
        'res_attr':
        [
        ],
        'response':
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss/template_001/link -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"lun_name":"su001_lun01",}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### qos unlink
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"QoS管理",
        'title':'取消关联QoS模板',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/qoss/<string:lun_name>/unlink',
        'href':'qos_unlink',
        'req_attr':
        [
        ],
        'res_attr':
        [
        ],
        'response':
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/qoss/su001_lun01/unlink -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool add        
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'添加存储池',
        'url':'POST : http://<ip:port>/api/<version>/instances/pools',
        'href':'pool_add',
        'req_attr': 
        [
            {
                'name':'disk_names',
                'type':'(array)string',
                'must':True,
                'info':'存储池所使用的磁盘列表, 目前仅支持单块盘',
            },
            {
                'name':'is_variable',
                'type':'bool',
                'must':False,
                'info':'指定为可变长palpool, 默认为非可变长',
            },
            {
                'name':'extent',
                'type':'uint64',
                'must':False,
                'info':'pool参数, 默认不需要指定',
            },
            {
                'name':'bucket',
                'type':'uint64',
                'must':False,
                'info':'pool参数, 默认不需要指定',
            },
            {
                'name':'sippet',
                'type':'uint64',
                'must':False,
                'info':'pool参数, 默认不需要指定',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i -u http://127.0.0.1:9000/api/v1.0/instances/pools -X POST \n\
    -H "Content-Type: application/json" \n\
    -d \'{"disk_names":["sd01p1"]}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool drop       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'删除存储池',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/pools/<string:pool_name>',
        'href':'pool_drop',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools/pool01 -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:44:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool resize       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'修改pool容量',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/pools/<string:pool_name>/size',
        'href':'pool_resize',
        'req_attr': 
        [
            {
                'name':'size',
                'type':'uint32',
                'must':True,
                'info':'Pool新容量, 单位为G',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools/pool01/size -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"size":100}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 43 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 25 Nov 2016 08:03:13 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool dirtythresh       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'存储池脏数据刷新阀值配置',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/pools/<string:pool_name>/dirtythresh',
        'href':'pool_dirtythresh',
        'req_attr': 
        [
            {
                'name':'dirty_thresh_lower',
                'type':'uint32',
                'must':True,
                'info':'Pool dirty 阀值下限, 0-100',
            },
            {
                'name':'dirty_thresh_upper',
                'type':'uint32',
                'must':True,
                'info':'Pool dirty 阀值上线, 0-100',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools/pool01/dirtythresh -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"dirty_thresh_upper":30, "dirty_thresh_lower":20}\' \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Sun, 09 Oct 2016 06:02:23 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool synclevel       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'存储池刷新速度等级配置',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/pools/<string:pool_name>/synclevel',
        'href':'pool_synclevel',
        'req_attr': 
        [
            {
                'name':'sync_level',
                'type':'uint32',
                'must':True,
                'info':'Pool刷新速度等级, 支持范围0-10',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools/pool01/synclevel -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"sync_level":3}\' \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Sun, 09 Oct 2016 06:02:23 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool cachemodel       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'存储池write模式',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/pools/<string:pool_name>/cachemodel',
        'href':'pool_cachemodel',
        'req_attr': 
        [
            {
                'name':'cache_model',
                'type':'string',
                'must':True,
                'info':'write模式, 仅支持through',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools/pool01/cachemodel -X PATCH \n\
    -H "Content-Type: application/json" \n\
    -d \'{"cache_model":"through"}\' \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Sun, 09 Oct 2016 06:02:23 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pool list       
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"存储池管理",
        'title':'获取存储池列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/pools',
        'href':'get_pool_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_pool_list_response',
                'type':'GetPoolListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)pool_infos',
                'type':'PoolInfo',
                'must':True,
                'info':'存储池详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pools \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 1169 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:48 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_pool_list_response": { \n\
            "pool_infos": [ \n\
                { \n\
                    "last_heartbeat_time": 1471574624,  \n\
                    "pool_name": "pool01",  \n\
                    "ext_poolinfo_pool_export_info": { \n\
                        "pool_name": "pool01",  \n\
                        "state": "OK,Running,Inactive" \n\
                    },  \n\
                    "pool_disk_infos": [ \n\
                        { \n\
                            "ext_pool_disk_info_size": 468857999,  \n\
                            "ext_pool_disk_info_dev_name": "/dev/sda1",  \n\
                            "ext_pool_disk_info_disk_name": "sd01p1",  \n\
                            "disk_part": 1,  \n\
                            "disk_id": "715e3a42-65b6-11e6-b07a-001e67ed992c" \n\
                        } \n\
                    ],  \n\
                    "actual_state": true,  \n\
                    "pool_id": "b250ae23-dd4f-2147-bb6e-d31c2d466f5f" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### license info
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"License管理",
        'title':'获取License信息',
        'url':'GET : http://<ip:port>/api/<version>/license/info',
        'href':'get_license_info',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_license_info_response',
                'type':'GetLicenseInfoResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)kvs',
                'type':'SimpleKV',
                'must':True,
                'info':'license具体信息key-value对',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/license/info \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 1835 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:54:58 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_license_info_response": { \n\
            "kvs": [ \n\
                { \n\
                    "value": "Enable",  \n\
                    "key": "Status" \n\
                },  \n\
                { \n\
                    "value": "Date",  \n\
                    "key": "LicMode" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartMgrSupport" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartQoSSupport" \n\
                },  \n\
                { \n\
                    "value": "2016-08-18",  \n\
                    "key": "InstTime" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartSnmpSupport" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartStoreSupport" \n\
                },  \n\
                { \n\
                    "value": "2010-11-11",  \n\
                    "key": "AuthTime" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "PALSupport" \n\
                },  \n\
                { \n\
                    "value": "2017-12-21",  \n\
                    "key": "LastTime" \n\
                },  \n\
                { \n\
                    "value": "ForeignLicense",  \n\
                    "key": "LicInitMode" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartCacheSupport" \n\
                },  \n\
                { \n\
                    "value": "Yes",  \n\
                    "key": "SmartMonSupport" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### get license
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"License管理",
        'title':'获取License文件',
        'url':'GET : http://<ip:port>/api/<version>/license/file',
        'href':'get_license_file',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_license_info_response',
                'type':'GetLicenseInfoResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'license_base64',
                'type':'string',
                'must':True,
                'info':'license文件base64编码后字符串',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/license/file \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 1137 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:55:13 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_license_file_response": { \n\
            "license_base64": "<...skip...>" \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### put license
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"License管理",
        'title':'上传License文件',
        'url':'PATCH : http://<ip:port>/api/<version>/license/file',
        'href':'put_license_file',
        'req_attr': 
        [
            {
                'name':'license_base64',
                'type':'string',
                'must':True,
                'info':'license文件base64编码后字符串',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/license/file -X PATCH  \n\
    -H "Content-Type:application/json" \n\
    -d \'{"license_base64":"<...skip...>"}\'  \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:55:45 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### 设置配置文件第二存储点的ip
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"配置文件备份管理",
        'title':'设置配置文件的第二存储点',
        'url':'GET : http://<ip:port>/api/<version>/storage/<string:ip>',
        'href':'set_second_storage',
        'req_attr': 
        [
            {
                'name':'second_storage_ip',
                'type':'string',
                'must':True,
                'info':'',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/storage/<string:ip> \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 43 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 06 Jan 2017 05:20:24 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },


    ### 获取配置文件第二存储点的ip
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"配置文件备份管理",
        'title':'获取配置文件的第二存储点',
        'url':'GET : http://<ip:port>/api/<version>/storage/get_ip',
        'href':'get_second_storage',
        'req_attr': 
        [
            {
                'name':'second_storage_ip',
                'type':'string',
                'must':True,
                'info':'',
            },
        ],
        'res_attr': 
        [
            {
                'name':'second_storage_ip',
                'type':'string',
                'must':False,
                'info':'',
            },

        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/storage/get_ip \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 164 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 06 Jan 2017 05:29:46 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_second_storage_response": { \n\
            "second_storage_ip": "172.16.9.217" \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### slot list
    {
        'role':['storage', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"Slot管理",
        'title':'获取slot列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/slots',
        'href':'get_slot_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_slot_list_response',
                'type':'GetSlotListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)slot_infos',
                'type':'SlotInfo',
                'must':True,
                'info':'Slot详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/slots \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 3669 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:51:11 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_slot_list_response": { \n\
            "slot_infos": [ \n\
                { \n\
                    "bus_address": "0000:00:1c.4",  \n\
                    "slot_id": "1" \n\
                },  \n\
                { \n\
                    "bus_address": "0000:80:01.0",  \n\
                    "slot_id": "3" \n\
                },  \n\
                { \n\
                    "bus_address": "0000:80:02.0",  \n\
                    "slot_id": "2" \n\
                },  \n\
                { \n\
                    "bus_address": "0000:00:03.0",  \n\
                    "slot_id": "5" \n\
                },  \n\
                { \n\
                    "bus_address": "0000:80:03.0",  \n\
                    "slot_id": "4" \n\
                },  \n\
                { \n\
                    "bus_address": "0000:00:02.0",  \n\
                    "slot_id": "6" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### asmdisk list
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"asmdisk管理",
        'title':'获取asmdisk列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/asmdisks',
        'href':'get_asmdisk_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_asm_list_response',
                'type':'GetASMDiskListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)asmdisk_infos',
                'type':'ASMDiskInfo',
                'must':True,
                'info':'asmdisk详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/asmdisks \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 3669 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:51:11 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_asmdisk_list_response": { \n\
            "asmdisk_infos": [ \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "16",  \n\
                    "filegroup": "",  \n\
                    "total_mb": 0,  \n\
                    "free_mb": 0,  \n\
                    "diskgroup_id": "0",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun07",  \n\
                    "asmdisk_name": "" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "14",  \n\
                    "filegroup": "",  \n\
                    "total_mb": 0,  \n\
                    "free_mb": 0,  \n\
                    "diskgroup_id": "0",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun08",  \n\
                    "asmdisk_name": "" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "50",  \n\
                    "filegroup": "",  \n\
                    "total_mb": 0,  \n\
                    "free_mb": 0,  \n\
                    "diskgroup_id": "0",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lvvote",  \n\
                    "asmdisk_name": "" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "2",  \n\
                    "filegroup": "",  \n\
                    "total_mb": 0,  \n\
                    "free_mb": 0,  \n\
                    "diskgroup_id": "0",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun09",  \n\
                    "asmdisk_name": "" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "0",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1892764,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun01",  \n\
                    "asmdisk_name": "DATA_DG_0000" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "3",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1892767,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun04",  \n\
                    "asmdisk_name": "DATA_DG_0003" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "16",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892631,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun08",  \n\
                    "asmdisk_name": "DATA_DG_0016" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "23",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892703,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun06",  \n\
                    "asmdisk_name": "DATA_DG_0023" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "19",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892659,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun02",  \n\
                    "asmdisk_name": "DATA_DG_0019" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "24",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892650,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun07",  \n\
                    "asmdisk_name": "DATA_DG_0024" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "22",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892661,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun05",  \n\
                    "asmdisk_name": "DATA_DG_0022" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "18",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892669,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun01",  \n\
                    "asmdisk_name": "DATA_DG_0018" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "21",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892661,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun04",  \n\
                    "asmdisk_name": "DATA_DG_0021" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "20",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892705,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun03",  \n\
                    "asmdisk_name": "DATA_DG_0020" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "25",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892663,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun08",  \n\
                    "asmdisk_name": "DATA_DG_0025" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "26",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892706,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun09",  \n\
                    "asmdisk_name": "DATA_DG_0026" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "12",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892615,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun04",  \n\
                    "asmdisk_name": "DATA_DG_0012" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "15",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892617,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun07",  \n\
                    "asmdisk_name": "DATA_DG_0015" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "9",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892647,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun01",  \n\
                    "asmdisk_name": "DATA_DG_0009" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "14",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892671,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun06",  \n\
                    "asmdisk_name": "DATA_DG_0014" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "11",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892674,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun03",  \n\
                    "asmdisk_name": "DATA_DG_0011" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "17",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1892665,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun09",  \n\
                    "asmdisk_name": "DATA_DG_0017" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "13",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892624,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun05",  \n\
                    "asmdisk_name": "DATA_DG_0013" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "10",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1892654,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun02",  \n\
                    "asmdisk_name": "DATA_DG_0010" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "4",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1892741,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun05",  \n\
                    "asmdisk_name": "DATA_DG_0004" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "5",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907537,  \n\
                    "free_mb": 1892808,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun06",  \n\
                    "asmdisk_name": "DATA_DG_0005" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "2",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907537,  \n\
                    "free_mb": 1892791,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun03",  \n\
                    "asmdisk_name": "DATA_DG_0002" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "1",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1892762,  \n\
                    "diskgroup_id": "1",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun02",  \n\
                    "asmdisk_name": "DATA_DG_0001" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "23",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1889518,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun18",  \n\
                    "asmdisk_name": "TEST_DG_0023" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "3",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1889824,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun13",  \n\
                    "asmdisk_name": "TEST_DG_0003" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "22",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889674,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun17",  \n\
                    "asmdisk_name": "TEST_DG_0022" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "0",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1889977,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun10",  \n\
                    "asmdisk_name": "TEST_DG_0000" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "9",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1890141,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun13",  \n\
                    "asmdisk_name": "TEST_DG_0009" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "12",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1890900,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun16",  \n\
                    "asmdisk_name": "TEST_DG_0012" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "5",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907537,  \n\
                    "free_mb": 1891215,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun15",  \n\
                    "asmdisk_name": "TEST_DG_0005" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "19",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889525,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun14",  \n\
                    "asmdisk_name": "TEST_DG_0019" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "8",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1891209,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun12",  \n\
                    "asmdisk_name": "TEST_DG_0008" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "1",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1889823,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun11",  \n\
                    "asmdisk_name": "TEST_DG_0001" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "21",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889527,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun16",  \n\
                    "asmdisk_name": "TEST_DG_0021" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "15",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889523,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun10",  \n\
                    "asmdisk_name": "TEST_DG_0015" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "10",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1891054,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun14",  \n\
                    "asmdisk_name": "TEST_DG_0010" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "11",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1891063,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun15",  \n\
                    "asmdisk_name": "TEST_DG_0011" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "14",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1891200,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun18",  \n\
                    "asmdisk_name": "TEST_DG_0014" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "7",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1891058,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun11",  \n\
                    "asmdisk_name": "TEST_DG_0007" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "2",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907537,  \n\
                    "free_mb": 1889823,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun12",  \n\
                    "asmdisk_name": "TEST_DG_0002" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "13",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889828,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun17",  \n\
                    "asmdisk_name": "TEST_DG_0013" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "20",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1889668,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun15",  \n\
                    "asmdisk_name": "TEST_DG_0020" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "6",  \n\
                    "filegroup": "SU002",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1890136,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lun10",  \n\
                    "asmdisk_name": "TEST_DG_0006" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "18",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889367,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun13",  \n\
                    "asmdisk_name": "TEST_DG_0018" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "17",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907342,  \n\
                    "free_mb": 1890594,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun12",  \n\
                    "asmdisk_name": "TEST_DG_0017" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "16",  \n\
                    "filegroup": "SU001",  \n\
                    "total_mb": 1907348,  \n\
                    "free_mb": 1889513,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su001_lun11",  \n\
                    "asmdisk_name": "TEST_DG_0016" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "4",  \n\
                    "filegroup": "HU003",  \n\
                    "total_mb": 1907541,  \n\
                    "free_mb": 1889979,  \n\
                    "diskgroup_id": "2",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun14",  \n\
                    "asmdisk_name": "TEST_DG_0004" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "0",  \n\
                    "filegroup": "VOTE_DG_0000",  \n\
                    "total_mb": 10240,  \n\
                    "free_mb": 9889,  \n\
                    "diskgroup_id": "3",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lvvote",  \n\
                    "asmdisk_name": "VOTE_DG_0000" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "1",  \n\
                    "filegroup": "VOTE_DG_0001",  \n\
                    "total_mb": 10240,  \n\
                    "free_mb": 9890,  \n\
                    "diskgroup_id": "3",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/su002_lvvote",  \n\
                    "asmdisk_name": "VOTE_DG_0001" \n\
                },  \n\
                { \n\
                    "mode_status": "ONLINE",  \n\
                    "asmdisk_id": "2",  \n\
                    "filegroup": "VOTE_DG_0002",  \n\
                    "total_mb": 10240,  \n\
                    "free_mb": 9889,  \n\
                    "diskgroup_id": "3",  \n\
                    "state": "NORMAL",  \n\
                    "path": "/dev/asmdisks/hu003_lun16",  \n\
                    "asmdisk_name": "VOTE_DG_0002" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### asmdisk add
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"asmdisk管理",
        'title':'添加asmdisk',
        'url':'POST : http://<ip:port>/api/<version>/instances/asmdisks',
        'href':'asmdisk_add',
        'req_attr': 
        [
            {
                'name':'asmdisk_path',
                'type':'string',
                'must':True,
                'info': 'asmdisk路径',
            },
            {
                'name':'diskgroup_name',
                'type':'string',
                'must':True,
                'info': '磁盘组名称',
            },
            {
                'name':'rebalance',
                'type':'uint32',
                'must':False,
                'info':'指定asm磁盘组平衡度级别',
            },
            {
                'name':'force',
                'type':'bool',
                'must':False,
                'info':'强制添加asm磁盘',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/asmdisks -X POST \n\
    -H "Content-Type: application/json" \n\
    -d \'{"asmdisk_path":"/dev/asmdisks/su001_lun01","diskgroup_name":"dg"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### asmdisk drop
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"asmdisk管理",
        'title':'删除asmdisk',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/asmdisks/<string:asmdisk_name>',
        'href':'asmdisk_drop',
        'req_attr': 
        [
            {
                'name':'rebalance',
                'type':'uint32',
                'must':False,
                'info':'指定asm磁盘组平衡度级别',
            },
            {
                'name':'force',
                'type':'bool',
                'must':False,
                'info':'强制删除asm磁盘',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/asmdisks/dg_0001 -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### asmdisk online
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"asmdisk管理",
        'title':'设置asmdisk上线',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/asmdisks/<string:asmdisk_name>/onlinestate',
        'href':'asmdisk_online',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/asmdisks/dg_0001/onlinestate -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### asmdisk offline
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"asmdisk管理",
        'title':'设置asmdisk下线',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/asmdisks/<string:asmdisk_name>/offlinestate',
        'href':'asmdisk_offline',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/asmdisks/dg_0001/offlinestate -X PATCH \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### diskgroup list
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"diskgroup管理",
        'title':'获取asm磁盘组列表',
        'url':'GET : http://<ip:port>/api/<version>/instances/diskgroups',
        'href':'get_diskgroup_list',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_diskgroup_response',
                'type':'GetDiskgroupListResponse',
                'must':False,
                'info':'',
            },
        ],
        'response' :
        [
            {
                'name':'(array)diskgroup_infos',
                'type':'DiskgroupInfo',
                'must':True,
                'info':'diskgroup详细信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/diskgroups \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 3669 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:51:11 GMT \n\
 \n\
{ \n\
    "body": { \n\
        "get_diskgroup_list_response": { \n\
            "diskgroup_infos": [ \n\
                { \n\
                    "diskgroup_id": "1",  \n\
                    "usable_file_mb": 14129197,  \n\
                    "offline_disks": 0,  \n\
                    "total_mb": 45777466,  \n\
                    "free_mb": 45424508,  \n\
                    "diskgroup_name": "DATA_DG",  \n\
                    "state": "CONNECTED",  \n\
                    "type": "NORMAL" \n\
                },  \n\
                { \n\
                    "diskgroup_id": "2",  \n\
                    "usable_file_mb": 14099012,  \n\
                    "offline_disks": 0,  \n\
                    "total_mb": 45777466,  \n\
                    "free_mb": 45364139,  \n\
                    "diskgroup_name": "TEST_DG",  \n\
                    "state": "MOUNTED",  \n\
                    "type": "NORMAL" \n\
                },  \n\
                { \n\
                    "diskgroup_id": "3",  \n\
                    "usable_file_mb": 9714,  \n\
                    "offline_disks": 0,  \n\
                    "total_mb": 30720,  \n\
                    "free_mb": 29668,  \n\
                    "diskgroup_name": "VOTE_DG",  \n\
                    "state": "MOUNTED",  \n\
                    "type": "NORMAL" \n\
                } \n\
            ] \n\
        } \n\
    },  \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### diskgroup add
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"diskgroup管理",
        'title':'添加diskgroup',
        'url':'POST : http://<ip:port>/api/<version>/instances/diskgroups',
        'href':'diskgroup_add',
        'req_attr': 
        [
            {
                'name':'diskgroup_name',
                'type':'string',
                'must':True,
                'info': '磁盘组名称',
            },
            {
                'name':'asmdisk_paths',
                'type':'string',
                'must':True,
                'info': '磁盘路径',
            },
            {
                'name':'redundancy',
                'type':'string',
                'must':False,
                'info': '冗余级别,支持external/normal/high, 默认是external',
            },
            {
                'name':'attr',
                'type':'string',
                'must':False,
                'info': '设置属性,支持compatible.asm/compatible.rdbms,默认是10.1',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/diskgroups -X POST \n\
    -H "Content-Type: application/json" \n\
    -d \'{"diskgroup_name":"dg","asmdisk_paths":"/dev/asmdisks/su001_lun01,/dev/asmdisks/su001_lun02","redundancy":"normal","attr":"compatible.asm=11.2,compatible.rdbms=11.2"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### diskgroup drop
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"diskgroup管理",
        'title':'删除diskgroup',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/diskgroups/<string:diskgroup_name>',
        'href':'diskgroup_drop',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/diskgroups/dg -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### diskgroup alter
    {
        'role':['database', 'merge', 'merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"diskgroup管理",
        'title':'修改diskgroup',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/diskgroups/<string:diskgroup_name>/alter',
        'href':'diskgroup_alter',
        'req_attr': 
        [
            {
                'name':'rebalance',
                'type':'uint32',
                'must':True,
                'info':'asm平衡度级别',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/diskgroups/dg/alter -X PATCH \n\
    -H "Content-Type: application/json"  \n\
    -d \'{"rebalance":5}\' \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:43:27 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### srbd init       
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"srbd管理",
        'title':'srbd节点初始化',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/srbd/init',
        'href':'srbd_init',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/init -x PATCH\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:44:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### srbd info     
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"srbd管理",
        'title':'srbd状态信息获取',
        'url':'GET : http://<ip:port>/api/<version>/instances/srbd/info',
        'href':'get_srbd_info',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_srbd_info_response',
                'type':'GetSrbdInfoResponse',
                'must':False,
                'info':'节点的srbd详细信息',
            },
        ],
        'response' :
        [
            {
                'name':'(array)srbd_infos',
                'type':'SrbdInfo',
                'must':False,
                'info':'节点的srbd信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/info \n\
',
        'res_demo':'\
HTTP/1.0 200 OK\n\
Content-Type: application/json; charset=utf-8\n\
Content-Length: 972\n\
Server: Smartmgr-API/2.3\n\
Date: Thu, 15 Jun 2017 09:24:54 GMT\n\
\n\
{\n\
    "body": {\n\
        "get_srbd_info_response": {\n\
            "srbd_infos": [\n\
                {\n\
                    "disk_status": "UpToDate", \n\
                    "role_status": "Secondary", \n\
                    "node_srbd_name": "dntohu002", \n\
                    "node_type": "node1", \n\
                    "node_srbd_netmask": "255.255.255.0", \n\
                    "node_srbd_netcard": "enp1s0f1", \n\
                    "con_status": "Connected", \n\
                    "node_srbd_ip": "10.0.0.2", \n\
                    "node_ipmi_ip": "172.16.9.204"\n\
                }, \n\
                {\n\
                    "disk_status": "UpToDate", \n\
                    "role_status": "Secondary", \n\
                    "node_srbd_name": "dntohu001", \n\
                    "node_type": "node2", \n\
                    "node_srbd_ip": "10.0.0.1", \n\
                    "node_ipmi_ip": "172.16.9.207"\n\
                }\n\
            ]\n\
        }\n\
    }, \n\
    "rc": {\n\
        "retcode": 0\n\
    }\n\
}\n\
'
    },
    ### srbd config       
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"srbd管理",
        'title':'srbd信息配置',
        'url':'POST : http://<ip:port>/api/<version>/instances/srbd/config ',
        'href':'srbd_config',
        'req_attr': 
        [
            {
                'name':'role',
                'type':'string',
                'must':False,
                'info':'配置本节点的role信息，primary/secondary',
            },
            {
                'name':'action',
                'type':'string',
                'must':False,
                'info':'打开或关闭srbd, on/off',
            },
            {
                'name':'srbd_config',
                'type':'SrbdConfig',
                'must':False,
                'info':'配置srbd节点的信息',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/config -X POST\n\
    -H "Content-Type: application/json" \n\
    -d \'{"role":"secondary"}\'\n\
\n\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/config -X POST\n\
    -H "Content-Type: application/json" \n\
    -d \'{"action":"on"}\'\n\
\n\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/config -X POST\n\
    -H "Content-Type: application/json" \n\
    -d \'{"nodeid":"node1","attr":"ipmi_ip=10.0.0.1"}\'\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:44:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### srbd sbr 脑裂恢复     
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"srbd管理",
        'title':'srbd脑裂恢复',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/srbd/sbr',
        'href':'srbd_sbr',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/srbd/sbr -x PATCH\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:44:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pcs init       
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"pcs管理",
        'title':'pcs集群初始化',
        'url':'PATCH : http://<ip:port>/api/<version>/instances/pcs/init',
        'href':'pcs_init',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pcs/init -X PATCH\n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:44:29 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },
    ### pcs config     
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"pcs管理",
        'title':'pcs集群操作(on/off, enable/disable)',
        'url':'GET : http://<ip:port>/api/<version>/instances/pcs/config/<string:action> -X PATCH',
        'href':'pcs_config',
        'req_attr': 
        [
            {
                'name':'action',
                'type':'string',
                'must':True,
                'info':'on/off 打开或关闭集群，enable/disable 启用或禁用stonith设备',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pcs/config/on -X PATCH\n\
',
        'res_demo':'\
HTTP/1.0 200 OK\n\
Content-Type: application/json; charset=utf-8\n\
Content-Length: 85\n\
Server: Smartmgr-API/2.3\n\
Date: Thu, 15 Jun 2017 11:08:36 GMT\n\
\n\
{\n\
    "rc": {\n\
        "message": "pcs online success", \n\
        "retcode": 0\n\
    }\n\
}\n\
'
    },

    ### pcs info     
    {
        'role':['merge-e',],
        'platform':['pbdata', 'generic'],
        'type':"pcs管理",
        'title':'获取pcs集群信息',
        'url':'GET : http://<ip:port>/api/<version>/instances/pcs/info',
        'href':'get_pcs_info',
        'req_attr': 
        [
        ],
        'res_attr': 
        [
            {
                'name':'get_pcs_info_response',
                'type':'GetPcsInfoResponse',
                'must':False,
                'info':'集群的详细信息',
            },
        ],
        'response' :
        [
            {
                'name':'pcs_info',
                'type':'PcsInfo',
                'must':False,
                'info':'集群的信息',
            },
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pcs/info \n\
',
        'res_demo':'\
HTTP/1.0 200 OK\n\
Content-Type: application/json; charset=utf-8\n\
Content-Length: 926\n\
Server: Smartmgr-API/2.3\n\
Date: Thu, 15 Jun 2017 10:03:53 GMT\n\
\n\
{\n\
    "body": {\n\
        "get_pcs_info_response": {\n\
            "pcs_info": {\n\
                "stonith_infos": [\n\
                    {\n\
                        "stonith_name": "dntohu001_fence", \n\
                        "stonith_status": "Started dntohu001-priv"\n\
                    }\n\
                ], \n\
                "pcs_nodes": [\n\
                    {\n\
                        "node_status": "online", \n\
                        "node_name": "dntohu001-priv"\n\
                    }, \n\
                    {\n\
                        "node_status": "online", \n\
                        "node_name": "dntohu002-priv"\n\
                    }\n\
                ], \n\
                "cluster_name": "srbd_cluster", \n\
                "corosync_status": "active/disabled", \n\
                "stonith_enabled": "true", \n\
                "pacemaker_status": "active/enabled"\n\
            }\n\
        }\n\
    }, \n\
    "rc": {\n\
        "retcode": 0\n\
    }\n\
}\n\
'
    },
    ### pcs drop       
    {
        'role':['merge-e'],
        'platform':['pbdata', 'generic'],
        'type':"pcs管理",
        'title':'删除fence设备',
        'url':'DELETE : http://<ip:port>/api/<version>/instances/pcs/drop/<string:stonith_name>',
        'href':'pcs_drop_stonith',
        'req_attr': 
        [
            {
                'name':'stonith_name',
                'type':'string',
                'must':True,
                'info':'删除指定的stonith，可通过pcs info获取',
            },
        ],
        'res_attr': 
        [
        ],
        'response' :
        [
        ],
        'req_demo':'\
curl -i http://127.0.0.1:9000/api/v1.0/instances/pcs/drop/dntohu001_fence -X DELETE \n\
',
        'res_demo':'\
HTTP/1.0 200 OK \n\
Content-Type: application/json; charset=utf-8 \n\
Content-Length: 177 \n\
Server: Smartmgr-API/2.3 \n\
Date: Fri, 19 Aug 2016 02:52:43 GMT \n\
 \n\
{ \n\
    "rc": { \n\
        "retcode": 0 \n\
    } \n\
} \n\
'
    },

]
struct_items = [ \
    {
        'title':'消息头部',
        'type':'Head',
        'attr':
        [
            {
                'name':'message_type',
                'type':'uint32',
                'must':True,
                'info':'消息类型',
            },
            {
                'name':'session',
                'type':'string',
                'must':True,
                'info':'session',
            },
            {
                'name':'flowno',
                'type':'uint64',
                'must':True,
                'info':'流水号',
            },
        ]
    },
    {
        'title':'返回码结构',
        'type':'ResponseCode',
        'attr':
        [
            {
                'name':'retcode',
                'type':'uint32',
                'must':True,
                'info':'错误返回码',
            },
            {
                'name':'message',
                'type':'string',
                'must':False,
                'info':'错误返回消息',
            },
        ]
    },
    {
        'title':'磁盘头信息',
        'type':'DiskHeader',
        'attr':
        [
            {
                'name':'uuid',
                'type':'string',
                'must':True,
                'info':'磁盘UUID',
            },
        ]
    },
    {
        'title':'磁盘信息',
        'type':'DiskInfo',
        'attr':
        [
            {
                'name':'disk_name',
                'type':'string',
                'must':False,
                'info':'磁盘逻辑id(hd01)',
            },
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'设备路径 /dev/sdx',
            },
            {
                'name':'disk_type',
                'type':'DISK_TYPE',
                'must':False,
                'info':'磁盘类型',
            },
            {
                'name':'size',
                'type':'uint64',
                'must':False,
                'info':'磁盘大小',
            },
            {
                'name':'diskparts',
                'type':'DiskPart',
                'must':True,
                'info':'磁盘分区信息',
            },
            {
                'name':'header',
                'type':'DiskHeader',
                'must':False,
                'info':'磁盘盘头信息',
            },
            {
                'name':'actual_state',
                'type':'bool',
                'must':False,
                'info':'实际状态(online/missing)',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳更新时间',
            },
            {
                'name':'raid_disk_info',
                'type':'RaidDiskInfo',
                'must':False,
                'info':'补充磁盘的raid信息',
            },
            {
                'name':'nvme_diskhealth_info',
                'type':'NvmeDiskHealthInfo',
                'must':False,
                'info':'nvme磁盘的健康检测信息',
            },

        ]
    },
    {
        'title':'磁盘raid信息',
        'type':'RaidDiskInfo',
        'attr':
        [
            {
                'name':'raid_type',
                'type':'RAID_TYPE',
                'must':True,
                'info':'raid类型',
            },
            {
                'name':'ctl',
                'type':'uint32',
                'must':True,
                'info':'控制器id',
            },
            {
                'name':'eid',
                'type':'uint32',
                'must':True,
                'info':'eid',
            },
            {
                'name':'slot',
                'type':'uint32',
                'must':True,
                'info':'slot',
            },
            {
                'name':'drive_type',
                'type':'string',
                'must':True,
                'info':'物理设备类型 ssd/hdd',
            },
            {
                'name':'protocol',
                'type':'string',
                'must':True,
                'info':'接口类型sas/sata',
            },
            {
                'name':'pci_addr',
                'type':'string',
                'must':True,
                'info':'raid卡的物理地址',
            },
            {
                'name':'size',
                'type':'string',
                'must':True,
                'info':'raid卡中看到的大小',
            },
            {
                'name':'model',
                'type':'string',
                'must':True,
                'info':'介质类型',
            },
            {
                'name':'state',
                'type':'string',
                'must':True,
                'info':'状态',
            },
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'如果有设备名称, 则补充设备名',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳更新时间',
            },
            {
                'name':'health',
                'type':'string',
                'must':False,
                'info':'磁盘的健康状态',
            },
            {
                'name':'ssd_diskhealth_info',
                'type':'SsdDiskHealthInfo',
                'must':False,
                'info':'ssd磁盘的健康检测详细信息',
            },
            {
                'name':'hdd_diskhealth_info',
                'type':'HddDiskHealthInfo',
                'must':False,
                'info':'hdd磁盘的健康检测详细信息',
            },

        ]
    },
    {
        'title':'磁盘分区信息',
        'type':'DiskPart',
        'attr':
        [
            {
                'name':'disk_part',
                'type':'uint32',
                'must':True,
                'info':'分区索引id',
            },
            {
                'name':'size',
                'type':'uint64',
                'must':True,
                'info':'分区大小',
            },
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'分区的dev_name(该字段仅用于前端显示, 不参与逻辑处理过程,逻辑处理过程使用disk_part定位)',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳更新时间',
            },
            {
                'name':'actual_state',
                'type':'bool',
                'must':False,
                'info':'实际状态(online/missing)',
            },
        ]
    },
    {
        'title':'ssd磁盘的健康检测详细信息',
        'type':'SsdDiskHealthInfo',
        'attr':
        [
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'设备名',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳时间',
            },
            {
                'name':'life',
                'type':'string',
                'must':False,
                'info':'磁盘的使用的剩余时间',
            },
            {
                'name':'offline_uncorrectable',
                'type':'string',
                'must':False,
                'info':'脱机无法校正的扇区计数',
            },
            {
                'name':'reallocated_event_count',
                'type':'string',
                'must':False,
                'info':'重定位事件计数',
            },
            {
                'name':'reallocated_sector_ct',
                'type':'string',
                'must':False,
                'info':'重定位磁电计数',
            },
            {
                'name':'power_on_hours',
                'type':'string',
                'must':False,
                'info':'硬件加电时间',
            },
            {
                'name':'temperature_celsius',
                'type':'string',
                'must':False,
                'info':'设备当前温度',
            },
            {
                'name':'raw_read_error_rate',
                'type':'string',
                'must':False,
                'info':'底层数据读取错误率',
            },
            {
                'name':'totallife',
                'type':'string',
                'must':False,
                'info':'硬盘总的使用时间',
            },
            {
                'name':'media_wearout_indicator',
                'type':'string',
                'must':False,
                'info':'介质损耗指标',
            },
            {
                'name':'spin_retry_count',
                'type':'string',
                'must':False,
                'info':'电机起转重试',
            },
            {
                'name':'command_timeout',
                'type':'string',
                'must':False,
                'info':'通信超时',
            },
            {
                'name':'uncorrectable_sector_ct',
                'type':'string',
                'must':False,
                'info':'无法校正的扇区计数',
            },
            {
                'name':'ssd_life_left',
                'type':'string',
                'must':False,
                'info':'ssd剩余寿命',
            },
        ]
    },
    {
        'title':'hdd磁盘的健康检测详细信息',
        'type':'HddDiskHealthInfo',
        'attr':
        [
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'设备名',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳时间',
            },
            {
                'name':'verifies_gb',
                'type':'string',
                'must':False,
                'info':'',
            },
            {
                'name':'life_left',
                'type':'string',
                'must':False,
                'info':'磁盘剩余寿命',
            },
            {
                'name':'uncorrected_reads',
                'type':'string',
                'must':False,
                'info':'未校正读',
            },
            {
                'name':'uncorrected_verifies',
                'type':'string',
                'must':False,
                'info':'为校正验证',
            },
            {
                'name':'corrected_reads',
                'type':'string',
                'must':False,
                'info':'校正读',
            },
            {
                'name':'writes_gb',
                'type':'string',
                'must':False,
                'info':'',
            },
            {
                'name':'load_cycle_pct_left',
                'type':'string',
                'must':False,
                'info':'硬盘加载/卸载次数的剩余百分比',
            },
            {
                'name':'load_cycle_count',
                'type':'string',
                'must':False,
                'info':'硬盘加载计数',
            },
            {
                'name':'corrected_writes',
                'type':'string',
                'must':False,
                'info':'校正写',
            },
            {
                'name':'reallocated_sector_ct',
                'type':'string',
                'must':False,
                'info':'重定位磁区计数',
            },
            {
                'name':'power_on_hours',
                'type':'string',
                'must':False,
                'info':'硬盘加电时间',
            },
            {
                'name':'non_medium_errors',
                'type':'string',
                'must':False,
                'info':'非媒介错误计数 ',
            },
            {
                'name':'reads_gb',
                'type':'string',
                'must':False,
                'info':'',
            },
            {
                'name':'load_cycle_spec',
                'type':'string',
                'must':False,
                'info':'硬盘加载/卸载次数的阀值',
            },
            {
                'name':'start_stop_pct_left',
                'type':'string',
                'must':False,
                'info':'硬盘主轴开始/停止旋转次数的剩余百分比',
            },
            {
                'name':'uncorrected_writes',
                'type':'string',
                'must':False,
                'info':'未校正写',
            },
            {
                'name':'start_stop_spec',
                'type':'string',
                'must':False,
                'info':'硬盘主轴开始/停止旋转的阀值',
            },
            {
                'name':'corrected_verifies',
                'type':'string',
                'must':False,
                'info':'校正验证',
            },
            {
                'name':'start_stop_cycles',
                'type':'string',
                'must':False,
                'info':'硬盘主轴开始/停止旋转的次数',
            },
        ]
    },
    {
        'title':'nvme磁盘的健康检测信息',
        'type':'NvmeDiskHealthInfo',
        'attr':
        [
            {
                'name':'life',
                'type':'uint32',
                'must':False,
                'info':'磁盘剩余寿命',
            },
            {
                'name':'totallife',
                'type':'uint32',
                'must':False,
                'info':'设备总的寿命周期',
            },
            {
                'name':'health',
                'type':'string',
                'must':False,
                'info':'设备状态',
            },
            {
                'name':'media_status',
                'type':'string',
                'must':False,
                'info':'存储介质状态',
            },

        ]
    },
    {
        'title':'Lun信息',
        'type':'LunInfo',
        'attr':
        [
            {
                'name':'lun_name',
                'type':'string',
                'must':True,
                'info':'lun逻辑id(lun001)',
            },
            {
                'name':'lun_id',
                'type':'string',
                'must':True,
                'info':'lun id (uuid)',
            },
            {
                'name':'lun_type',
                'type':'LUN_TYPE',
                'must':True,
                'info':'lun类型',
            },
            {
                'name':'config_state',
                'type':'bool',
                'must':True,
                'info':'配置状态(online/offline)',
            },
            {
                'name':'actual_state',
                'type':'bool',
                'must':False,
                'info':'实际状态(online/missing)',
            },
            {
                'name':'asm_status',
                'type':'string',
                'must':False,
                'info':'asm状态(online/active/sync/inactive/offline)',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳更新时间',
            },
            {
                'name':'qos_template_id',
                'type':'uint64',
                'must':False,
                'info':'关联的QoS模板id',
            },
        ]
    },
    {
        'title':'QoS模板信息',
        'type':'QosTemplateInfo',
        'attr':
        [
            {
                'name':'template_name',
                'type':'string',
                'must':True,
                'info':'qos模板名(template_001)',
            },
            {
                'name':'template_id',
                'type':'string',
                'must':True,
                'info':'qos模板id(uuid)',
            },
            {
                'name':'qos_info',
                'type':'Qosinfo',
                'must':True,
                'info':'qos详细信息',
            },
        ]
    },
    {
        'title':'QoS信息',
        'type':'QosInfo',
        'attr':
        [
            {
                'name':'read-iops',
                'type':'string',
                'must':False,
                'info':'读iops'
            },
            {
                'name':'read-bps',
                'type':'string',
                'must':False,
                'info':'读带宽'
            },
            {
                'name':'write-iops',
                'type':'string',
                'must':False,
                'info':'写iops'
            },
            {
                'name':'write-bps',
                'type':'string',
                'must':False,
                'info':'写bps'
            },
        ]
    },
    {
        'title':'Target信息',
        'type':'TargetInfo',
        'attr':
        [
            {
                'name':'target_id',
                'type':'string',
                'must':False,
                'info':'target id(uuid), 全局唯一, 由pal生成',
            },
            {
                'name':'target_name',
                'type':'string',
                'must':True,
                'info':'target name',
            },
            {
                'name':'pal_id',
                'type':'uint32',
                'must':False,
                'info':'target id(pal给出,局部)',
            },
            {
                'name':'pool_id',
                'type':'string',
                'must':True,
                'info':'存储池id',
            },
            {
                'name':'disk_id',
                'type':'string',
                'must':True,
                'info':'磁盘UUID',
            },
            {
                'name':'disk_part',
                'type':'uint32',
                'must':True,
                'info':'分区索引',
            },
        ]
    },
    {
        'title':'BaseDev信息',
        'type':'BaseDevInfo',
        'attr':
        [
            {
                'name':'basedev_id',
                'type':'string',
                'must':True,
                'info':'basedev id(uuid)',
            },
            {
                'name':'dev_name',
                'type':'string',
                'must':True,
                'info':'磁盘dev_name',
            },
            {
                'name':'size',
                'type':'uint64',
                'must':False,
                'info':'lun的size',
            },
        ]
    },
    {
        'title':'BaseDisk信息',
        'type':'BaseDiskInfo',
        'attr':
        [
            {
                'name':'basedisk_id',
                'type':'string',
                'must':True,
                'info':'basedisk id(uuid)',
            },
            {
                'name':'disk_id',
                'type':'string',
                'must':True,
                'info':'磁盘UUID',
            },
            {
                'name':'disk_part',
                'type':'uint32',
                'must':True,
                'info':'分区索引',
            },
        ]
    },
    {
        'title':'SmartCache信息',
        'type':'SmartCacheInfo',
        'attr':
        [
            {
                'name':'smartcache_id',
                'type':'string',
                'must':True,
                'info':'smartcahce id(uuid)',
            },
            {
                'name':'data_disk_id',
                'type':'string',
                'must':True,
                'info':'数据磁盘header.uuid',
            },
            {
                'name':'data_disk_part',
                'type':'uint32',
                'must':True,
                'info':'数据磁盘分区索引',
            },
            {
                'name':'cache_disk_id',
                'type':'string',
                'must':True,
                'info':'cache盘uuid',
            },
            {
                'name':'cache_disk_part',
                'type':'uint32',
                'must':True,
                'info':'cache盘磁盘分区索引',
            },
            {
                'name':'params',
                'type':'SimpleKV',
                'must':True,
                'info':'SmartCache的配置信息',
            },
        ]
    },
    {
        'title':'Pool信息',
        'type':'PoolInfo',
        'attr':
        [
            {
                'name':'pool_id',
                'type':'string',
                'must':False,
                'info':'存储池ID, 全局唯一, 由pal生成分配',
            },
            {
                'name':'pool_name',
                'type':'string',
                'must':True,
                'info':'存储池名称, 节点内部唯一',
            },
            {
                'name':'pool_disk_infos',
                'type':'PoolDiskInfo',
                'must':True,
                'info':'池中所使用的磁盘列表',
            },
            {
                'name':'extent',
                'type':'uint64',
                'must':False,
                'info':'pool的参数',
            },
            {
                'name':'bucket',
                'type':'uint64',
                'must':False,
                'info':'pool的参数',
            },
            {
                'name':'sippet',
                'type':'uint64',
                'must':False,
                'info':'pool的参数',
            },
            {
                'name':'sync_level',
                'type':'uin32',
                'must':True,
                'info':'pool刷新速度等级',
            },
            {
                'name':'actual_state',
                'type':'bool',
                'must':False,
                'info':'实际状态(online/missing)',
            },
            {
                'name':'last_heartbeat_time',
                'type':'uint64',
                'must':False,
                'info':'最后心跳更新时间',
            },
        ]
    },
    {
        'title':'pool所使用磁盘信息',
        'type':'PoolDiskInfo',
        'attr':
        [
            {
                'name':'disk_id',
                'type':'string',
                'must':True,
                'info':'磁盘UUID',
            },
            {
                'name':'disk_part',
                'type':'uint32',
                'must':True,
                'info':'分区索引',
            },
        ]
    },
    {
        'title':'简单kv',
        'type':'SimpleKV',
        'attr':
        [
            {
                'name':'key',
                'type':'string',
                'must':True,
                'info':'key',
            },
            {
                'name':'value',
                'type':'string',
                'must':True,
                'info':'value',
            },
        ]
    },
    {
        'title':'lun的smartscsi的导出信息',
        'type':'LunExportInfo',
        'attr':
        [
            {
                'name':'lun_name',
                'type':'string',
                'must':True,
                'info':'lun名称',
            },
            {
                'name':'t10_dev_id',
                'type':'string',
                'must':True,
                'info':'lun的scsi id',
            },
            {
                'name':'threads_num',
                'type':'uint32',
                'must':True,
                'info':'配置线程数',
            },
            {
                'name':'threads_pool_type',
                'type':'string',
                'must':True,
                'info':'配置线程类型',
            },
            {
                'name':'io_error',
                'type':'uint64',
                'must':True,
                'info':'io错误数量',
            },
            {
                'name':'last_errno',
                'type':'int32',
                'must':True,
                'info':'最后io错误类型',
            },
            {
                'name':'filename',
                'type':'string',
                'must':True,
                'info':'具体对应该的数据盘',
            },
            {
                'name':'size_mb',
                'type':'uint64',
                'must':True,
                'info':'实际大小',
            },
            {
                'name':'exported',
                'type':'SimpleKV',
                'must':True,
                'info':'导致状态',
            },
        ]
    },
    {
        'title':'Pool的pal实时信息',
        'type':'PoolExportInfo',
        'attr':
        [
            {
                'name':'pool_name',
                'type':'string',
                'must':True,
                'info':'pool名称',
            },
            {
                'name':'state',
                'type':'string',
                'must':True,
                'info':'pool状态',
            },
            {
                'name':'valid',
                'type':'uint64',
                'must':False,
                'info':'pool有效数量',
            },
            {
                'name':'p_valid',
                'type':'double',
                'must':False,
                'info':'pool有效百分比',
            },
            {
                'name':'dirty',
                'type':'uint64',
                'must':False,
                'info':'脏数据数量',
            },
            {
                'name':'p_dirty',
                'type':'double',
                'must':False,
                'info':'脏数据百分比',
            },
            {
                'name':'error',
                'type':'uint64',
                'must':False,
                'info':'错误数量',
            },
        ]
    },
    {
        'title':'节点信息',
        'type':'NodeInfo',
        'attr':
        [
            {
                'name':'node_name',
                'type':'string',
                'must':True,
                'info':'节点名称',
            },
        ]
    },
    {
        'title':'Disk质量信息',
        'type':'DiskQualityInfo',
        'attr':
        [
            {
                'name':'t_time',
                'type':'uint64',
                'must':False,
                'info':'测试时间',
            },
            {
                'name':'disk_count',
                'type':'uint32',
                'must':False,
                'info':'测试磁盘数量',
            },
            {
                'name':'ioengine',
                'type':'string',
                'must':False,
                'info':'io引擎',
            },
            {
                'name':'run_time',
                'type':'uint32',
                'must':False,
                'info':'运行时间',
            },
            {
                'name':'block_size',
                'type':'string',
                'must':False,
                'info':'单次io的块文件大小',
            },
            {
                'name':'num_jobs',
                'type':'uint32',
                'must':False,
                'info':'测试线程数',
            },
            {
                'name':'iodepth',
                'type':'uint32',
                'must':False,
                'info':'队列深度',
            },
            {
                'name':'curr_test',
                'type':'bool',
                'must':False,
                'info':'标识是否正在测试中',
            },
            {
                'name':'quality_test_result',
                'type':'QualityTestResult',
                'must':False,
                'info':'测试结果',
            },
        ]
    },
    {
        'title':'测试结果信息',
        'type':'QualityTestResult',
        'attr':
        [
            {
                'name':'name',
                'type':'string',
                'must':False,
                'info':'磁盘名称',
            },
            {
                'name':'path',
                'type':'string',
                'must':False,
                'info':'磁盘盘符',
            },
            {
                'name':'randread_iops',
                'type':'uint32',
                'must':False,
                'info':'每秒执行的IO读次数',
            },
            {
                'name':'read_bw',
                'type':'uint32',
                'must':False,
                'info':'读带宽，每秒的吞吐量',
            },
        ]
    },
    {
        'title':'Slot信息',
        'type':'SlotInfo',
        'attr':
        [
            {
                'name':'slot_id',
                'type':'string',
                'must':True,
                'info':'槽位id，如果是riser板的槽位，则用 riser板id-槽位id 表示'
            },
            {
                'name':'bus_address',
                'type':'string',
                'must':True,
                'info':'总线地址'
            },
            {
                'name':'dev_name',
                'type':'string',
                'must':False,
                'info':'设备名称'
            },
        ]
    },
    {
        'title':'asmdisk信息',
        'type':'ASMDiskInfo',
        'attr':
        [
            {
                'name':'asmdisk_name',
                'type':'string',
                'must':True,
                'info':'磁盘名'
            },
            {
                'name':'asmdisk_id',
                'type':'string',
                'must':True,
                'info':'磁盘编号'
            },
            {
                'name':'diskgroup_id',
                'type':'string',
                'must':False,
                'info':'所在磁盘组编号'
            },
            {
                'name':'path',
                'type':'string',
                'must':False,
                'info':'磁盘的完整路径'
            },
            {
                'name':'mode_status',
                'type':'string',
                'must':False,
                'info':'磁盘IO全局状态，有ONLINE和OFFLINE两种状态'
            },
            {
                'name':'state',
                'type':'string',
                'must':False,
                'info':'磁盘关于磁盘组的全局状态'
            },
            {
                'name':'filegroup',
                'type':'string',
                'must':False,
                'info':'磁盘所属的FAILGROUP，如创建磁盘组时未分配FAILGROUP，则缺省为每个磁盘单独一个FAILGROUP'
            },
            {
                'name':'total_mb',
                'type':'int32',
                'must':False,
                'info':'磁盘总容量'
            },
            {
                'name':'free_mb',
                'type':'int32',
                'must':False,
                'info':'磁盘剩余容量'
            },
            {
                'name':'type',
                'type':'string',
                'must':False,
                'info':'通过kfed获取到的kfbh.type'
            },
            {
                'name':'dskname',
                'type':'string',
                'must':False,
                'info':'通过kfed获取到的dskname'
            },
            {
                'name':'grpname',
                'type':'string',
                'must':False,
                'info':'通过kfed获取到的grpname'
            },
        ]
    },
    {
        'title':'diskgroup信息',
        'type':'DiskgroupInfo',
        'attr':
        [
            {
                'name':'diskgroup_name',
                'type':'string',
                'must':True,
                'info':'磁盘组名称'
            },
            {
                'name':'diskgroup_id',
                'type':'string',
                'must':True,
                'info':'磁盘组唯一编号'
            },
            {
                'name':'type',
                'type':'string',
                'must':False,
                'info':'磁盘组的冗余类型'
            },
            {
                'name':'state',
                'type':'string',
                'must':False,
                'info':'磁盘组的状态'
            },
            {
                'name':'offline_disks',
                'type':'uint32',
                'must':False,
                'info':'磁盘组中OFFLINE状态的磁盘个数'
            },
            {
                'name':'total_mb',
                'type':'uint64',
                'must':False,
                'info':'磁盘组总容量'
            },
            {
                'name':'free_mb',
                'type':'uint64',
                'must':False,
                'info':'磁盘组剩余容量'
            },
            {
                'name':'usable_file_mb',
                'type':'uint64',
                'must':False,
                'info':'可安全使用的空间'
            },
        ]
    },
    {
        'title':'srbd状态描述',
        'type':'SrbdInfo',
        'attr':
        [
            {
                'name':'role_status',
                'type':'string',
                'must':False,
                'info':'资源角色状态'
            },
            {
                'name':'con_status',
                'type':'string',
                'must':False,
                'info':'资源连接状态'
            },
            {
                'name':'disk_status',
                'type':'string',
                'must':False,
                'info':'硬盘状态'
            },
            {
                'name':'node_srbd_name',
                'type':'string',
                'must':False,
                'info':'node srbd网络name'
            },
            {
                'name':'node_srbd_ip',
                'type':'string',
                'must':False,
                'info':'node srbd网络ip'
            },
            {
                'name':'node_srbd_netmask',
                'type':'string',
                'must':False,
                'info':'node srbd网络掩码'
            },
            {
                'name':'node_ipmi_ip',
                'type':'string',
                'must':False,
                'info':'node ipmi ip'
            },
            {
                'name':'node_srbd_netcard',
                'type':'string',
                'must':False,
                'info':'node srbd使用网络'
            },
            {
                'name':'node_passwd',
                'type':'string',
                'must':False,
                'info':'node password'
            },
            {
                'name':'node_type',
                'type':'string',
                'must':False,
                'info':'node1 or node2'
            },
        ]
    },
    {
        'title':'修改srbd信息',
        'type':'SrbdConfig',
        'attr':
        [
            {
                'name':'nodeid',
                'type':'string',
                'must':False,
                'info':'node id'
            },
            {
                'name':'srbd_key',
                'type':'string',
                'must':False,
                'info':'修改srbd信息的键'
            },
            {
                'name':'srbd_value',
                'type':'string',
                'must':False,
                'info':'修改srbd信息的值'
            },
        ]
    },
    {
        'title':'stonith状态描述',
        'type':'StonithInfo',
        'attr':
        [
            {
                'name':'stonith_name',
                'type':'string',
                'must':False,
                'info':'stonish name'
            },
            {
                'name':'stonith_status',
                'type':'string',
                'must':False,
                'info':'stonish 状态'
            },
        ]
    },
    {
        'title':'pcs node 描述状态',
        'type':'PcsNode',
        'attr':
        [
            {
                'name':'node_name',
                'type':'string',
                'must':False,
                'info':'pcs node name'
            },
            {
                'name':'node_status',
                'type':'string',
                'must':False,
                'info':'pcs node status'
            },
        ]
    },
    {
        'title':'pcs状态描述',
        'type':'PcsInfo',
        'attr':
        [
            {
                'name':'cluster_name',
                'type':'string',
                'must':False,
                'info':'pcs集群name'
            },
            {
                'name':'corosync_status',
                'type':'string',
                'must':False,
                'info':'corosync状态'
            },
            {
                'name':'pacemaker_status',
                'type':'string',
                'must':False,
                'info':'pacemaker状态'
            },
            {
                'name':'pcs_nodes',
                'type':'PcsNode',
                'must':False,
                'info':'pcsd节点状态'
            },
            {
                'name':'stonith_infos',
                'type':'StonithInfo',
                'must':False,
                'info':'stonith info'
            },
            {
                'name':'stonith_enabled',
                'type':'string',
                'must':False,
                'info':'stonith-enable status'
            },

        ]
    },

]

enum_items = [ \
    {
        'title':'磁盘类型',
        'type':'DISK_TYPE',
        'attr':
        [
            {
                'name':'DISK_TYPE_UNDEFINE',
                'valu':'0',
                'info':'磁盘类型未定义',
            },
            {
                'name':'DISK_TYPE_HDD',
                'valu':'10',
                'info':'HDD类型磁盘',
            },
            {
                'name':'DISK_TYPE_SSD',
                'valu':'20',
                'info':'SSD类型磁盘',
            },
        ]
    },
    {
        'title':'Raid类型',
        'type':'RAID_TYPE',
        'attr':
        [
            {
                'name':'RAID_TYPE_MEGARAID',
                'valu':'1',
                'info':'9261/9271类型raid卡',
            },
            {
                'name':'RAID_TYPE_SAS2RAID',
                'valu':'2',
                'info':'9207类型raid卡',
            },
        ]
    },
    {
        'title':'Lun类型',
        'type':'LUN_TYPE',
        'attr':
        [
            {
                'name':'LUN_TYPE_SMARTCACHE',
                'valu':'1',
                'info':'使用SmartCache做cache类型lun',
            },
            {
                'name':'LUN_TYPE_BASEDISK',
                'valu':'2',
                'info':'使用裸盘类型lun',
            },
            {
                'name':'LUN_TYPE_TARGET',
                'valu':'3',
                'info':'使用pal pool做cache类型lun',
            },
            {
                'name':'LUN_TYPE_BASEDEV',
                'valu':'4',
                'info':'直接使用dev设备做lun, 目前仅支持/dev/mapper下lvvote开头的lvm',
            },
        ]
    },
]
