#coding=utf-8
import threading, commands, time, os, json, sys, atexit

FIO  = "/usr/bin/fio"

def command(cmd,timeout=60*10):
    e, res = commands.getstatusoutput("/usr/bin/timeout %s %s" % (timeout, cmd))
    if e == 31744:
        return -2, "subprocess timeout" 
    return e, res

class ThreadFunc(object):
    def __init__(self,func,args):
        self.func=func
        self.args=args
        self.result = None

    def __call__(self):
        self.result = apply(self.func,self.args)

def fio_test(attr, device):
    cmd  = "%s -filename=%s -ioengine=%s -bs=%s -runtime=%s " % (FIO, device, attr['ioengine'], attr['bs'], attr['runtime'])
    cmd += "-iodepth=%s -numjobs=%s " % (attr['iodepth'], attr['numjobs'])
    cmd += "-direct=1 -thread -rw=randread -group_reporting -minimal -name=test"
    e, iops_result = command(cmd, attr['runtime']+60)
    if e: return -1, {'result':"", 'device':device}
    cmd  = "%s -filename=%s -ioengine=%s -bs=%s -runtime=%s " % (FIO, device, attr['ioengine'], "1M", attr['runtime'])
    cmd += "-iodepth=%s -numjobs=%s " % (attr['iodepth'], attr['numjobs'])
    cmd += "-direct=1 -thread -rw=read -group_reporting -minimal -name=test"
    e, rbw_result = command(cmd, attr['runtime']+60)
    if e: return -1, {'result':"", 'device':device}
    return 0, {'result':{'randread-iops':iops_result.split(';')[7], 'read-bw':rbw_result.split(';')[6]}, 'device':device}

def start_fio(attr, devices, t_time):
    threads=[]
    for device in devices.keys():
        task = ThreadFunc(fio_test,(attr,device))
        threads.append((threading.Thread(target=task), task))

    for thread in threads:
        thread[0].start()

    for thread in threads:
        thread[0].join()

    result = []
    for thread in threads:
        result.append(thread[1].result)
    return {'result':result, 'attr':attr, 't_time':t_time}

def start_test(option):
    try:
        result = start_fio(option['attr'], option['devices'], option['t_time'])
        for res in result['result']:
            res[1]['device'] = option['devices'][res[1].get('device')]
        file(os.path.join(option['out_dir'], "%s.result" % str(option['t_time'])), 'w+').write("%s\n" % json.dumps(result, indent=4))
    except:
        pass
    os.remove(option['cache_file'])
    return 0, ''

if __name__ == '__main__': 
    start_test(json.loads(file(sys.argv[1],'r+').read()))
