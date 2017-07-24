# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import cmd, socket, netifaces
from optparse import OptionParser
from cli_head import *
from diskmgr       import DiskMgr
from lunmgr        import LunMgr
from groupmgr      import GrpMgr
from poolmgr       import PoolMgr
from smartcachemgr import SmartCacheMgr
from basediskmgr   import BaseDiskMgr
from basedevmgr    import BaseDevMgr
from targetmgr     import TargetMgr
from nodemgr       import NodeMgr
from licensemgr    import LicenseMgr
from qosmgr        import QosMgr
from diskgroupmgr  import DiskgroupMgr
from asmdiskmgr    import ASMDiskMgr
from slotmgr       import SlotMgr
from srbdmgr       import SrbdMgr
from pcsmgr        import PcsMgr

sys.path.append(os.path.abspath(os.path.join(__file__, '../../../')))
from pdsframe.common.config import init_config, config

class CliOptionParser(OptionParser):
    def __init__(self, usage=""):
        OptionParser.__init__(self, usage)
        self.ret_code = 0
        self.ret_mess = ""

    def error(self, err_mgs):
        raise Exception(err_mgs)

    def exit(self):
        pass

class CLI(cmd.Cmd, object):
    def __init__(self):
        cmd.Cmd.__init__(self,'TAB')
        self.prompt   = PRODUCT_NAME+'> '
        self.intro    = IntroString
        self.srv      = {"ip":None, "port":None, 'role':None, 'platform':None, "cli_config":{}}
        self._hist    = [] # history

    def pre_init(self, cli_config):
        self.srv['cli_config'] = cli_config

    def post_init(self):
        self.disk       = DiskMgr(self.srv)
        self.lun        = LunMgr(self.srv)
        self.group      = GrpMgr(self.srv)
        self.pool       = PoolMgr(self.srv)
        self.smartcache = SmartCacheMgr(self.srv)
        self.basedisk   = BaseDiskMgr(self.srv)
        self.basedev    = BaseDevMgr(self.srv)
        self.target     = TargetMgr(self.srv)
        self.node       = NodeMgr(self.srv)
        self.license    = LicenseMgr(self.srv)
        self.qos        = QosMgr(self.srv)
        self.diskgroup  = DiskgroupMgr(self.srv)
        self.asmdisk    = ASMDiskMgr(self.srv)
        self.slot       = SlotMgr(self.srv)
        self.srbd       = SrbdMgr(self.srv)
        self.pcs        = PcsMgr(self.srv)
        # 载入历史动作
        self._hist = load_hist()

        # 根据当前机器类型，动态修改支持的操作
        cmd_list = []
        for cmd_name, cmd_items in cmd_option.items():
            for cmd_item in cmd_items.values():
                if self.srv['platform'] in cmd_item['platform'] and self.srv['role'] in cmd_item['role']:
                    if self.srv['cli_config']['detail'] == False and cmd_item.has_key('detail') and cmd_item['detail'] == True:
                        continue
                    cmd_list.append(cmd_name)
                    break;

        def create_do_cmd(cmd):
            def do_cmd(self, args):
                print self.action(cmd, args)
            return do_cmd
        
        def create_complete_cmd(cmd):
            def complete_cmd(self, text, line, begin_idx, end_idx):
                return self.op_complete(text,line)
            return complete_cmd

        for cmd in cmd_option.keys():
            if cmd in cmd_list:
                setattr(self.__class__, 'do_'+cmd, create_do_cmd(cmd))
                setattr(self.__class__, 'complete_'+cmd, create_complete_cmd(cmd))
            else:
                if hasattr(self.__class__, 'do_'+cmd):
                    delattr(self.__class__, 'do_'+cmd)
                    delattr(self.__class__, 'complete__'+cmd)

    def parse_cfg(self, opt={}, arg=""):
        params = {}
        dest_list = {}
        key = ""
        a=arg.strip().split()
        if (len(a) == 1 and a[0] in ['-h', '--help']) or (len(a) == 0):
            out  = []
            out += ["Options:"]
            find = 0
            for sub_cmd_pair in sorted(opt.iteritems(), key=lambda asd:asd[0]):
                k = sub_cmd_pair[0]
                v = sub_cmd_pair[1]
                if self.srv['cli_config']['detail'] == False and v.has_key('detail') and v['detail'] == True:
                    continue
                if not v.has_key("role") or not self.srv['role'] in v["role"]:
                    continue
                if not v.has_key("platform") or not self.srv['platform'] in v["platform"]:
                    continue
                out += [' '*4+'%-10s : %-10s' % (k, v['help'])] 
                find = find + 1
            if find == 0:
                return (7,"","")
            return (8, "\n".join(out), '')
    
        if not opt.has_key(a[0]):
            return (1, 'Unsupport option!', '')
        cmd = a[0]
        sub_opt = opt[cmd]
        if not sub_opt.has_key("role") or not self.srv['role'] in sub_opt["role"]:
            return (1, 'Unsupport option!', '')

        if not sub_opt.has_key("platform") or not self.srv['platform'] in sub_opt["platform"]:
            return (1, 'Unsupport option!', '')

        if self.srv['cli_config']['detail'] == False and sub_opt.has_key('detail') and sub_opt['detail'] == True:
            return (1, 'Unsupport option!', '')
        parser = CliOptionParser("")
        for item in sub_opt['opts']:
            if len(item['opt']) == 2:
                if not item.has_key("platform") or item["platform"] == self.srv['platform']:
                    if item.has_key('action'):
                        parser.add_option("-"+item['opt'][0], "--"+item['opt'][1], action=item['action'], metavar=item['metavar'], \
                                dest=item['dest'], help=item['help'])
                    else:
                        parser.add_option("-"+item['opt'][0], "--"+item['opt'][1], metavar=item['metavar'], dest=item['dest'], help=item['help'])
                    if item.has_key('cfun') and item['cfun'] != "": 
                        dest_list[item['dest']]= item['cfun']
                    else:
                        dest_list[item['dest']]= ""
            elif  len(item['opt']) == 0:
                key = item['dest']
        try:
            (options, args) = parser.parse_args(a[1:])
        except Exception as e:
            return (1, str(e), '')
        if parser.ret_code:
            return (1, 'parse arrgs', '')
    
        if "-h" in a[1:] or "--help" in a[1:]:
            out = []
            for item in sub_opt['opts']:
                if len(item['opt']) == 0:
                    out += ['  %s\t\t%s' % (item['metavar'], item['help'])] 
            out += ["Examples:"]
            if sub_opt['example'].has_key('common'):
                for line in sub_opt['example']['common']:
                    out += ["  %s" % line]
            if sub_opt['example'].has_key('generic') and self.srv['platform'] == 'generic':
                for line in sub_opt['example']['generic']:
                    out += ["  %s" % line]
            if sub_opt['example'].has_key('pbdata') and self.srv['platform'] == 'pbdata':
                for line in sub_opt['example']['pbdata']:
                    out += ["  %s" % line]
            return (9, "\n".join(out), '')
    
        if key != "" and len(args) != 1:
            return (1, 'miss object name', '')
    
        if key != "" and len(args) == 0:
            return (1, 'miss option', '')
    
        if key == "" and len(dest_list.keys()) == 0 and len(args) != 0:
            return (1, "Excess parameters", "")
        for d, cfun in dest_list.items():
            if getattr(options, d) != None:
                value = getattr(options, d)
                if cfun != "":
                    value = getattr(ChkParams(), "chk_"+cfun)(value)
                    if not value: return (1, "params --%s's value illegal." % d, '')
                params[d] = value
    
        if key != "":
            params[key] = args[0]
        return (0, cmd, params)
    
    def get_complet(self, opt):
        _list = []
        for key in opt.keys():
            if self.srv['role'] in opt[key]["role"] and self.srv['platform'] in opt[key]["platform"]:
                if self.srv['cli_config']['detail'] == False and opt[key].has_key('detail') and opt[key]['detail'] == True:
                    continue
                _list = _list + [key]
        return _list
    
    def op_complete(self,text,line):
        args=line.split()
        if line.endswith(' ') : 
            args+=['']
        ret = []
        opt = getattr(self,args[0]).opt
        list = self.get_complet(opt)
        if text == "":
             ret = list
        else:
             for i in list:
                if i.startswith(text):
                    ret = ret+[i]
        return ret
        
    def preloop(self):
        cmd.Cmd.preloop(self)
        self._locals  = {}
        self._globals = {}

    def postloop(self):
        cmd.Cmd.postloop(self)
        self.do_save()

    def _save_hist(self, line):
        l=line.strip()
        if l not in ['']:
            self._hist.append("[%s] %s" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time()))), l))
            save_hist(self._hist)

    # 命令预处理，去除掉不接受的字符
    def precmd(self, line):
        self._save_hist(line)
        if not re.match(r'^[\w /?<>!*%#=;:,.+_-]*$',line):
            print '\033[1;31mCommand Error : command contains invalid characters !\033[0m'
            return ''
        return line

    def postcmd(self, stop, line):
        return stop

    def emptyline(self):
        pass

    def default(self, line):
        a=line.strip().split()
        c=safepeek(a)
        print '\033[1;31m'+'Command Error : '+c+' is not a valid CLI command !'+"\033[0m"

    def action(self, type, args):
        obj = getattr(self, type)
        (e, cmd, params) = self.parse_cfg(obj.opt, args)
        if e == 7:
            return '\033[1;31m'+'Command Error : '+type+' is not a valid CLI command !'+"\033[0m"
        if e == 8: 
            return cmd
        if e == 9: 
            return cmd
        if e: 
            return '\033[1;31mCommand Error : %s\033[0m' % cmd

        for opt in obj.opt[cmd]['opts']:
            if len(opt['opt']) == 2 and opt['opt'][1] == "noconfirm":
                if not params.has_key('noconfirm') or params['noconfirm'] != True:
                    result = confirm(opt['info'])
                    if result in ['n', '']:
                        return "Canceled!"
        ret = getattr(obj, "cli_"+cmd)(params)
        return ret
    
    def do_hist(self, arg=''):
        if len(self._hist) > 0:
            print '\n'.join(self._hist)

    def do_quit(self, arg=''):
        print 'Bye..'
        sys.exit(0)

    def do_help(self, arg=''):
        status = None
        out = []
        out += ['help'] 
        out += [' '*14+' : Show this information.'] 
        for cmd_pair in sorted(cmd_option.iteritems(), key=lambda asd:asd[0]):
            cmd = cmd_pair[0]
            flag = False
            for sub_cmd_pair in sorted(cmd_pair[1].iteritems(), key=lambda asd:asd[0]):
                sub_cmd_name  = sub_cmd_pair[0]
                sub_cmd_param = sub_cmd_pair[1]
                flag = True
                if self.srv['cli_config']['detail'] == False and sub_cmd_param.has_key('detail') and sub_cmd_param['detail'] == True:
                    continue
                if not sub_cmd_param.has_key("role") or not self.srv['role'] in sub_cmd_param["role"]:
                    continue
                if not sub_cmd_param.has_key("platform") or not self.srv['platform'] in sub_cmd_param["platform"]:
                    continue
                if cmd != status:
                    out += ['%s' % cmd] 
                    status = cmd
                out += [' '*4+'%-10s : %-10s' % (sub_cmd_name, sub_cmd_param['help'])] 
        print "\n".join(out)

    do_q    = do_quit
    do_exit = do_quit

def load_platform():
    try:
        f = open("/boot/installer/platform", 'r')
        c = f.read()
        f.close()
    except:
        print "Load /boot/installer/platform failed!"
        sys.exit(1)
    kvs = {}
    for line in c.splitlines():
        item = line.split()
        kvs[item[0].lower()] = item[1].lower()
    return kvs

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

def main():
    if "--help" in sys.argv:
        print "Usage: smartmgrcli [option]"
        sys.exit(0)

    cli = CLI()

    mds_config = "/opt/smartmgr/conf/service.mds.ini"

    if "--config" in sys.argv:
        if len(sys.argv) == sys.argv.index("--config") + 1 :
            print "Miss config file"
            sys.exit(1)
        mds_config = sys.argv[sys.argv.index("--config") + 1]
        if not os.path.exists(mds_config):
            print "Please cheack your config file path"
            sys.exit(1)
        del sys.argv[sys.argv.index('--config')+1]
        del sys.argv[sys.argv.index('--config')]

    init_config(mds_config)
    platform = load_platform()

    if platform.has_key('sys_mode') and platform.has_key('merge_mode'):
        cli.srv['role']     = platform['merge_mode']
    else:
        cli.srv['role']     = platform['sys_mode']
    cli.srv['platform'] = platform['platform']
    cli.srv['ip']       = config.safe_get('network', 'listen-ip')
    cli.srv['port']     = config.safe_get_int('network', 'listen-port')
    check_netconfig(cli.srv['ip'])

    cli_config = {'debug':False, 'json':False,'detail':False}

    if "--debug" in sys.argv:
        del sys.argv[sys.argv.index('--debug')]
        cli_config['debug'] = True

    if "--detail" in sys.argv:
        del sys.argv[sys.argv.index('--detail')]
        cli_config['detail'] = True

    if "--json" in sys.argv:
        del sys.argv[sys.argv.index('--json')]
        cli_config['json'] = True

    cli.pre_init(cli_config)
    cli.post_init()

    # shell 命令行方式调用
    if len(sys.argv) > 1 :
        try:
            cli._save_hist(' '.join(sys.argv[1:]))
            cli.onecmd(' '.join(sys.argv[1:]))
        except KeyboardInterrupt:
            print "Stopped.."
            cli.do_quit('')
    else:
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print "Stopped.."
            cli.do_quit('')

if __name__ == '__main__':
    main()
