#coding=utf-8
import threading, commands, time, os, json, sys, atexit

class DiskTest():
    def __init__(self, cache_file, out_dir, max_count=10):
        self.max_count = max_count
        self.cache_file = cache_file
        self.out_dir   = out_dir
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

    def clear_old_result(self):
        result = filter(lambda f:len(f.split('.')) >= 2 and f.split('.')[1]=="result", os.listdir(self.out_dir))
        result.sort()
        result.reverse()
        if len(result) > self.max_count:
            for r in result[self.max_count:]:
                os.remove(os.path.join(self.out_dir, r))
    
    def get_curr_test(self):
        if os.path.exists(self.cache_file):
            try:
                return json.loads(file(self.cache_file,'r+').read())
            except:
                return None
        return None
    
    def get_result_list(self):
        result = filter(lambda f:len(f.split('.')) >= 2 and f.split('.')[1]=="result", os.listdir(self.out_dir))
        result.sort()
        result.reverse()
        out = []
        for r in result:
            out.append(json.loads(file(os.path.join(self.out_dir, r),'r+').read()))
        return 0, out

    def start_test(self, params={}):
        # test进程已经存在，则退出
        fio_test_ps = "ps -ef |grep python | grep %s | grep %s | grep -v grep | awk '{print $2}'" % (params['test_script'], self.cache_file)
        if commands.getstatusoutput(fio_test_ps)[1] != '':
            return -1, "a disk quality task is doing now, please try later"
        option = {}
        option['attr']      = params['attr']
        option['devices']   = params['devices']
        option['out_dir']   = self.out_dir
        option['t_time']    = int(time.time())
        option['cache_file'] = self.cache_file
        file(self.cache_file,'w+').write("%s\n" % json.dumps(option, indent=4))
        os.system("nohup python %s %s > /dev/null 2>&1 &" % (params['test_script'], self.cache_file))
        return 0, ''
