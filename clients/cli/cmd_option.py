# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))
import message.pds_pb2 as msg_pds

cmd_option = { \
    'disk': {
        'list':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'List all disk',
            'opts':[
                {'opt':('P','part'),'action':'store_true','metavar':'<part view>','dest':'part','help':'Show disk by part view model'},
            ],
            'example': {
                'common':[
                    'disk list',
                    'disk list -P',
                ],
            },
        },
        'info':{
            'role':['storage','merge', 'merge-e'],
            'platform':['pbdata','generic'],
            'help':'Display specific disk info',
            'opts': [
                {'opt':('n', 'name'),'metavar':'<disk name>','dest':'disk_name','help':'Specify disk name'},
            ],
            'example': {
				'common':[
                'disk info -n hd01',
            ]},
        },
        'led':{
            'role':['storage','merge', 'merge-e'],
            'platform':['pbdata'],
            'help':'Change a disk raid light to on/off',
            'opts': [
                {'opt':('p','path'),'platform':'pbdata','metavar':'<disk path>','dest':'ces_addr','help':'Specify disk ces addr'},
                {'opt':('a','action'),'platform':'pbdata','metavar':'<on|off>','dest':'action','help':'Specify led action type, support on/off'},
                {'opt':('A','all'),'action':'store_true','metavar':'<all disk>','dest':'all','help':'Action to all disk'},
            ],
            'example': {'pbdata':[
                'disk led -a on  -p 0:16:1',
                'disk led -a off -p 0:16:1',
                'disk led -a on -A',
            ]},
        },
        'drop':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop a disk',
            'opts':[
                {'opt':('n','name'),'metavar':'<disk name>','dest':'disk_name','help':'Specify disk name'},
            ],
            'example': {
                'common':[
                    'disk drop -n hd01',
                ],
            },
        },
        'add':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Initialize and add a new disk',
            'opts':[
                {'opt':('p','path'),'metavar':'<disk path>','dest':'dev_name','help':'Specify disk path addr'},
                {'opt':('c','count'),'metavar':'<partition count>','dest':'partition_count','help':'Specify partition count'},
                {'opt':('t','type'),'metavar':'<disk type ssd|hdd>','dest':'disk_type','help':'Specify disk type'},
            ],
            'example': {
                'generic':[
                    'disk add -p /dev/sdb -t ssd',
                    'disk add -p /dev/sdb -t hdd -c 2',
                ],
                'pbdata':[
                    'disk add -p 0:16:1',
                    'disk add -p 0:16:1 -c 2',
                    'disk add -p /dev/nvme0n1 -t ssd -c 6',
                ]
            },
        },
        'quality':{
            'role':['storage','merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Detail of disk quality',
            'opts': [
                {'opt':('l','list'),'action':'store_true','metavar':'<list quality>','dest':'list','help':'List all disk quality test'},
                {'opt':('t','test'),'action':'store_true','metavar':'<start quality test>','dest':'test','help':'Start a new disk quality test'},
                {'opt':('i','info'),'metavar':'<test quality time>','dest':'info','help':'Specify test quality time'},
                {'opt':('f','force'),'action':'store_true','metavar':'<force test disk quality>','dest':'force','help':'Do not confirm notice'},
            ],
            'example': {'common':[
                'disk quality -l',
                'disk quality -t',
                'disk quality -i 2016-10-21.22:33:54',
            ]},
        },
        'replace':{
            'role':['storage','merge'],
            'platform':['pbdata', 'generic'],
            'help':'Replace the disk',
            'opts': [
                {'opt':('n','name'),'metavar':'<disk name>','dest':'disk_name','help':'Specify the replace disk name'},
                {'opt':('p','path'),'metavar':'<disk path>','dest':'dev_name','help':'Specify disk path addr'},
            ],
            'example': {
                'generic':[
                    'disk replace -n hd01 -p /dev/sdb',
                ],
                'pbdata':[
                    'disk replace -n hd01 -p /dev/sdb',
                    'disk replace -n hd01 -p 0:16:1',
                ]
            },
        },
    },
    'pool': {
        'list':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'List all pal pool',
            'opts':[
            ],
            'example': {
                'common':[
                    'pool list',
                ],
            },
        },
        'disable':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Disable a pal pool for pool\'s dev is missing',
            'opts':[
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
            ],
            'example': {
                'common':[
                    'pool disable -p pool01',
                ],
            },
        },
        'drop':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop a pal pool',
            'opts':[
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
            ],
            'example': {
                'common':[
                    'pool drop -p pool01',
                ],
            },
        },
        'add':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Add pal pool',
            'opts':[
                {'opt':('n','name'),'metavar':'<disk name>','dest':'disk_names','help':'Specify disk name'},
                {'opt':('v','variable'),'action':'store_true','metavar':'<pool length variable>','dest':'variable','help':'Specify pool\'s length is variable, default is fixed'},
                {'opt':('a','attr'),'metavar':'arg=value','dest':'attr','help':'Set pool attribute'},
            ],
            'example': {
                'common':[
                    'pool add -n sd01p1',
                    'pool add -n sd01p1 -v',
                    'pool add -n sd01p1 -a extent=1G,bucket=8M,sippet=8K',
                ],
            },
        },
        'info':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get pal pool',
            'opts':[
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
            ],
            'example': {
                'common':[
                    'pool info -p pool01',
                ],
            },
        },
        'resize':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Resize pal pool capacity',
            'opts':[
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
                {'opt':('s','size'),'metavar':'<pool newsize>','dest':'size','help':'Set pool new size'},
            ],
            'example': {
                'common':[
                    'pool resize -p pool01 -s 200G',
                ],
            },
        },
        'rebuild':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Rebuild a pal pool for new disk',
            'opts':[
                {'opt':('n','name'),'metavar':'<disk name>','dest':'disk_names','help':'Specify disk name'},
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
            ],
            'example': {
                'common':[
                    'pool rebuild -p pool01 -n sd01p1',
                ],
            },
        },
        'config':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Config pal pool attributes',
            'opts':[
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
                {'opt':('l','level'),'metavar':'<sync level>','dest':'level','help':'Specify pool sync level, support 0-10'},
                {'opt':('k','skip'),'metavar':'<skip thresh>','dest':'skip_thresh','help':'Specify pool skip thresh, support 0-1024k'},
                {'opt':('d','dirty'),'metavar':'<pool dirty thresh>','dest':'dirty_thresh','help':'Specify pool dirty thresh, [lower,upper], min is 0, max is 100'},
                {'opt':('m','model'),'metavar':'<pool cache model>','dest':'model','help':'Specify pool cache model, only support through'},
                {'opt':('S','stop'),'action':'store_true','metavar':'<stop flag>','dest':'stop_through','help':'Stop change cache mode to through'},
            ],
            'example': {
                'common':[
                    'pool config -p pool01 -l 5',
                    'pool config -p pool01 -k 8k',
                    'pool config -p pool01 -d 30,70',
                    'pool config -p pool01 -m through',
                    'pool config -p pool01 -m through -S',
                ],
            },
        },
    },

   'group':{
        'add':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Add node group',
            'opts':[
                {'opt':('n','name'),'metavar':'<group name>','dest':'group_name','help':'Specify lun group name'},
            ],
            'example': {
                'common':[
                    'group add -n group01',
                ],
            },
        },
        'drop':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop node group',
            'opts':[
                {'opt':('n','name'),'metavar':'<group name>','dest':'group_name','help':'Specify lun group name'},
            ],
            'example': {
                'common':[
                    'group drop -n group01',
                ],
            },
        },
        'list':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'List node group',
            'opts':[
            ],
            'example': {
                'common':[
                    'group list',
                ],
            },
        },
    },

    'lun': {
        'add':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Add a new lun',
            'opts':[
                {'opt':('n','name'),'metavar':'<disk name>','dest':'data_disk_name','help':'Specify disk name'},
                {'opt':('g','gname'),'metavar':'<group name>','dest':'group_name','help':'Specify lun group'},
                {'opt':('c','cache'),'metavar':'<cache disk name>','dest':'cache_disk_name','help':'Specify cache disk name'},
                {'opt':('p','pool'),'metavar':'<pool name>','dest':'pool_name','help':'Specify pool name'},
                {'opt':('B','basedisk'),'action':'store_true','metavar':'<basedisk>','dest':'basedisk','help':'Specify basedisk type lun, default is palraw'},
                {'opt':('s','size'),'metavar':'<lun size>','dest':'size','help':'Specify lun size, if create pmt lun'},
            ],
            'example': {
                'common':[
                    'lun add -n hd01p1 -g group01',
                    'lun add -n hd01p1 -c sd01p1 -g group01',
                    'lun add -n hd01p1 -p pool01 -g group01',
                    'lun add -p pool01 -s 100G -g group01',
                ],
            },
        },

    
        'config':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Config a lun device to group',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
                {'opt':('g','gname'),'metavar':'<group name>','dest':'group_name','help':'Specify lun group'},
                {'opt':('d','del_group'),'action':'store_true','metavar':'<del group>','dest':'del_group','help':'delete lun from group'},
            ],
            'example': {
                'common':[
                    'lun config -n su001_lun01 -g group01',
                    'lun config -n su001_lun01 -g group01 -d',
                ],
            },
        },

        'online':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Online a lun device',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
            ],
            'example': {
                'common':[
                    'lun online -n su001_lun01',
                ],
            },
        },

        'offline':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Offline a lun device',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
            ],
            'example': {
                'common':[
                    'lun offline -n su001_lun01',
                ],
            },
        },
        'drop':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop a lun device',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
                {'opt':('r','rebalance'),'metavar':'<rebalance>','dest':'rebalance','help':'Specify asm rebalance power, for active lun'},
                {'opt':('f','force'),'action':'store_true','metavar':'<force>','dest':'force','help':'Force drop lvvote/active lun'},
            ],
            'example': {
                'common':[
                    'lun drop -n lun01',
                    'lun drop -n lun01 -r 5',
                    'lun drop -n lun01 -f',
                    'lun drop -n su001_lvvote -f',
                ],
            },
        },
        'list':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get lun list',
            'opts':[
                {'opt':('q','qos'),'metavar':'<qos name>','dest':'qos_name','help':'Specify the qos '},
                {'opt':('n','node'),'action':'store_true','metavar':'<qos name>','dest':'node','help':'list lun for node'},
                {'opt':('g','group_name'),'metavar':'<group name>','dest':'group_name','help':'list lun for group'},
            ],
            'example': {
                'common':[
                    'lun list',
                    'lun list -q qos_01',
                    'lun list -g group01',
                ],
            },
        },
        'active':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Set lun active',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
                {'opt':('r','rebalance'),'metavar':'<rebalance>','dest':'rebalance','help':'Specify asm rebalance power'},
                {'opt':('f','force'),'action':'store_true','metavar':'<force>','dest':'force','help':'Force add lun to asm'},
            ],
            'example': {
                'common':[
                    'lun active -n su001_lun01',
                    'lun active -n su001_lun01 -r 5',
                    'lun active -n su001_lun01 -f',
                ],
            },
        },
        'inactive':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Set lun inactive',
            'opts':[
                {'opt':('n','name'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
            ],
            'example': {
                'common':[
                    'lun inactive -n su001_lun01',
                ],
            },
        },
    },
    'qos': {
        'add':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Add a QoS',
            'opts':[
                {'opt':('n','name'),'metavar':'<qos name>','dest':'qos_name','help':'Specify qos name'},
                {'opt':('I','items'),'metavar':'<qos items>','dest':'items','help':'Specify qos items, support read-bps/write-bps/read-iops/write-iops, bps=Kilo Byte per second'},
            ],
            'example': {
                'common':[
                'qos add -n qos_01 -I read-bps=1048576,read-iops=100',
                'qos add -n qos_02 -I read-bps=1048576,write-bps=1048576,read-iops=100,write-iops=100',
                ],
            },
        },
        'drop':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop a QoS',
            'opts':[
                {'opt':('n','name'),'metavar':'<qos name>','dest':'qos_name','help':'Specify qos name'},
            ],
            'example': {
                'common':[
                'qos drop -n qos_01',
                ],
            },
        },
        'update':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Update a QoS',
            'opts':[
                {'opt':('n','name'),'metavar':'<qos name>','dest':'qos_name','help':'Specify qos name'},
                {'opt':('I','items'),'metavar':'<qos items>','dest':'items','help':'Specify qos items, support read-iops/read-bps/write-iops/write-bps, bps=Kilo Byte per second'},
            ],
            'example': {
                'common':[
                'qos update -n qos_01 -I read-bps=1048576,read-iops=100',
                'qos update -n qos_01 -I read-bps=1048576,write-bps=1048576,read-iops=100,write-iops=100',
                ],
            },
        },
        'list':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get QoS list',
            'opts':[
            ],
            'example': {
                'common':[
                'qos list'
                ],
            },
        },
        'link':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Link QoS with lun',
            'opts':[
                {'opt':('n','name'),'metavar':'<qos name>','dest':'qos_name','help':'Specify qos name'},
                {'opt':('l','lun'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
            ],
            'example': {
                'common':[
                'qos link -n qos_01 -l lun_001',
                ],
            },
        },
        'unlink':{
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Unlink QoS with lun',
            'opts':[
                {'opt':('l','lun'),'metavar':'<lun name>','dest':'lun_name','help':'Specify lun name'},
            ],
            'example': {
                'common':[
                'qos unlink -l lun_001',
                ],
            },
        },
    },
    'basedisk': {
        'list':{
            'detail':True,
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get basedisk list',
            'opts':[
            ],
            'example': {
                'common':[
                    'basedisk list',
                ],
            },
        },
    },
    'basedev': {
        'list':{
            'detail':True,
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get basedev list',
            'opts':[
            ],
            'example': {
                'common':[
                    'basedev list',
                ],
            },
        },
    },
    'smartcache': {
        'list':{
            'detail':True,
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get smartcache list',
            'opts':[
            ],
            'example': {
                'common':[
                    'smartcache list',
                ],
            },
        },
    },
    'target': {
        'list':{
            'detail':True,
            'role':['storage', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get target list',
            'opts':[
                {'opt':('t','type'),'metavar':'<target type>','dest':'type','help':'Specify target type, support cache/raw'},
            ],
            'example': {
                'common':[
                    'target list -t cache',
                    'target list -t raw',
                ],
            },
        },
    },
    'license': {
        'info':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Get license info',
            'opts':[
            ],
            'example': {
                'common':[
                    'license info',
                ],
            },
        },
    },
    'node': {
        'info':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Get node info',
            'opts':[
            ],
            'example': {
                'common':[
                    'node info',
                ],
            },
        },
        'config':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Config node attr',
            'opts':[
                {'opt':('a','attr'),'metavar':'arg=value','dest':'attr','help':'Set node attribute'},
                {'opt':('n','node_name'),'metavar':'<node name>','dest':'node_index','help':'add node'},
                {'opt':('g','group_name'),'metavar':'<group name>','dest':'group_name','help':'add node to group'},
                {'opt':('d','del_node'),'action':'store_true','metavar':'<del node>','dest':'del_node','help':'delete node from group'},
            ],
            'example': {
                'common':[
                    'node config -a nodename=su001',
                    'node config -n node01 -g group01',
                    'node config -n node01 -g group01 -d',
                ],
            },
        },

        'add':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'add node',
            'opts':[
                {'opt':('n','node_name'),'metavar':'<node name>','dest':'node_name','help':'add node'},
                {'opt':('g','group_name'),'metavar':'<group name>','dest':'group_name','help':'add node to group'},
            ],
            'example': {
                'common':[
                    'node add -n du001',
                    'node add -n du001 -g group01',
                ],
            },
        },

        'drop':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'drop node',
            'opts':[
                {'opt':('n','node_index'),'metavar':'<node index>','dest':'node_index','help':'drop node'},
            ],
            'example': {
                'common':[
                    'node drop -n node01',
                ],
            },
        },


        'list':{
            'role':['storage', 'merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Get node list by broadcast',
            'opts':[
            ],
            'example': {
                'common':[
                    'node list',
                ],
            },
        },
    },
    'asmdisk': {
        'list':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Get asm disk list',
            'opts':[
            ],
            'example': {
                'common':[
                    'asmdisk list',
                ],
            },
        },
        'add':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Add asm disk to diskgroup',
            'opts':[
                {'opt':('p','path'),'metavar':'<asmdisk path>','dest':'asmdisk_path','help':'Specify asmdisk path'},
                {'opt':('g','diskgroup'),'metavar':'<diskgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
                {'opt':('r','rebalance'),'metavar':'<rebalance>','dest':'rebalance','help':'Specify diskgroup rebalance power'},
                {'opt':('f','failgroup'),'metavar':'<failgroup>','dest':'failgroup','help':'Specify failgroup'},
                {'opt':('F','force'),'action':'store_true','metavar':'<force add asmdisk>','dest':'force','help':'Force add asmdisk'},
            ],
            'example': {
                'common':[
                    'asmdisk add -p /dev/asmdisks/su001_lun01 -g dg',
                    'asmdisk add -p /dev/asmdisks/su001_lun01 -g dg -f fg1 -r 5',
                    'asmdisk add -p /dev/asmdisks/su001_lun01 -g dg -F',
                ],
            },
        },
        'drop':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Drop asm disk from diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<asmdisk name>','dest':'asmdisk_name','help':'Specify asm disk name'},
                {'opt':('r','rebalance'),'metavar':'<rebalance>','dest':'rebalance','help':'Specify diskgroup rebalance power'},
                {'opt':('F','force'),'action':'store_true','metavar':'<force add asmdisk>','dest':'force','help':'Force drop asmdisk'},
            ],
            'example': {
                'common':[
                    'asmdisk drop -n dg_0001',
                    'asmdisk drop -n dg_0001 -r 5',
                    'asmdisk drop -n dg_0001 -F',
                ],
            },
        },
        'online':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Online asm disk or asm disks in failgroup and diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<asmdisk name>','dest':'asmdisk_name','help':'Specify asm disk name'},
                {'opt':('g','diskgroup'),'metavar':'<diskgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
                {'opt':('f','failgroup'),'metavar':'<failgroup>','dest':'failgroup','help':'Specify failgroup'},
            ],
            'example': {
                'common':[
                    'asmdisk online -n dg_0001',
                    'asmdisk online -g dg_0001 -f fg1',
                ],
            },
        },
        'offline':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Offline asm disk or asm disks in failgroup and diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<asmdisk name>','dest':'asmdisk_name','help':'Specify asm disk name'},
                {'opt':('g','diskgroup'),'metavar':'<diskgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
                {'opt':('f','failgroup'),'metavar':'<failgroup>','dest':'failgroup','help':'Specify failgroup'},
            ],
            'example': {
                'common':[
                    'asmdisk offline -n dg_0001',
                    'asmdisk offline -g dg_0001 -f fg1',
                ],
            },
        },
    },
    'diskgroup': {
        'list':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Get asm diskgroup list',
            'opts':[
            ],
            'example': {
                'common':[
                    'diskgroup list',
                ],
            },
        },
        'add':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Add asm diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<diskgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
                {'opt':('p','path'),'metavar':'<asmdisk paths>','dest':'asmdisk_paths','help':'Specify asmdisk paths'},
                {'opt':('r','redundancy'),'metavar':'<redundancy>','dest':'redundancy','help':'Specify redundancy level, support external/normal/high, default external'},
                {'opt':('f','failgroups'),'metavar':'<failgroups>','dest':'failgroups','help':'Specify failgroups'},
                {'opt':('A','attr'),'metavar':'<arg=value>','dest':'attr','help':'Specify attribute, support compatible.asm/compatible.rdbms, default 10.1'},
            ],
            'example': {
                'common':[
                    'diskgroup add -n dg -p /dev/asmdisks/su001_lun01',
                    'diskgroup add -n dg -p /dev/asmdisks/su001_lun01,/dev/asmdisks/su001_lun02 -r normal -A compatible.asm=11.2,compatible.rdbms=11.2',
                    'diskgroup add -n dg -p /dev/asmdisks/su001_lun01,/dev/asmdisks/su001_lun02 -f fg1,fg2 -r normal -A compatible.asm=11.2,compatible.rdbms=11.2',
                ],
            },
        },
        'drop':{
            'role':['merge', 'merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Drop asm diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<disgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
            ],
            'example': {
                'common':[
                    'diskgroup drop -n dg',
                ],
            },
        },
        'config':{
            'role':['merge','merge-e', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Config asm diskgroup rebalance power',
            'opts':[
                {'opt':('n','name'),'metavar':'<disgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
                {'opt':('r','rebalance'),'metavar':'<rebalance>','dest':'rebalance','help':'Specify diskgroup rebalance power'},
            ],
            'example': {
                'common':[
                    'diskgroup config -n dg -r 5',
                ],
            },
        },
        'mount':{
            'role':['merge', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Mount diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<disgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
            ],
            'example': {
                'common':[
                    'diskgroup mount -n dg',
                ],
            },
        },
        'umount':{
            'role':['merge', 'database'],
            'platform':['pbdata', 'generic'],
            'help':'Umount diskgroup',
            'opts':[
                {'opt':('n','name'),'metavar':'<disgroup name>','dest':'diskgroup_name','help':'Specify asm diskgroup name'},
            ],
            'example': {
                'common':[
                    'diskgroup umount -n dg',
                ],
            },
        },
    },
    'slot': {
        'list':{
            'role':['storage', 'database', 'merge', 'merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Get slot list',
            'opts':[
            ],
            'example': {
                'common':[
                    'slot list',
                ],
            },
        },
    },
    'srbd': {
        'init':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'srbd init',
            'opts':[
            ],
            'example': {
                'common':[
                    'srbd init',
                ],
            },
        },
        'info':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'srbd info',
            'opts':[
            ],
            'example': {
                'common':[
                    'srbd info',
                ],
            },
        },
        'config':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Config srbd attr',
            'opts':[
                {'opt':('n','nodeid'),'metavar':'<nodeid>','dest':'nodeid','help':'Specify srbd node id'},
                {'opt':('k','key'),'metavar':'arg=value','dest':'key','help':'Set srbd config'},
                {'opt':('r','role'),'metavar':'<role>','dest':'role','help':'Set srbd node role'},
                {'opt':('a','action'),'metavar':'<on|off|disconnect|connect>','dest':'action','help':'Specify srbd action type, support on/off connect/disconnect srbd'},
                ],
            'example': {
                'common':[
                    'srbd config -n node1 -k srbd_ip=192.168.0.1',
                    'srbd config -n node2 -k ipmi_ip=172.16.9.204',
                    'srbd config -r primary',
                    'srbd config -r secondary',
                    'srbd config -a on',
                    'srbd config -a disconnect',
                ],
            },
        },
        'sbr':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'split brain recovery',
            'opts':[
            ],
            'example': {
                'common':[
                    'srbd sbr' ,
                ],
            },
        },
    },
    'pcs': {
        'init':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'pcs init',
            'opts':[
            ],
            'example': {
                'common':[
                    'pcs init',
                ],
            },
        },
        'info':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'pcs info',
            'opts':[
            ],
            'example': {
                'common':[
                    'pcs info',
                ],
            },
        },
        'config':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'pcs on/off',
            'opts':[
                {'opt':('a','action'),'metavar':'<on|off>','dest':'action','help':'Specify pcs action type, support on/off cluster or enable/disable'},
                {'opt':('f','force'),'action':'store_true','metavar':'<force>','dest':'force','help':'force off cluster'},
                ],
            'example': {
                'common':[
                    'pcs config -a on',
                    'pcs config -a off',
                    'pcs config -a enable',
                    'pcs config -a disable',
                ],
            },
        },
        'drop':{
            'role':['merge-e'],
            'platform':['pbdata', 'generic'],
            'help':'Drop a stonith',
            'opts':[
                {'opt':('n','name'),'metavar':'<stonith name>','dest':'stonith_name','help':'Specify stonith id'},
            ],
            'example': {
                'common':[
                    'pcs drop -n dnthu001_fence',
                ],
            },
        },
    },
}
