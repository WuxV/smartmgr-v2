# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, time, atexit
from signal import signal, SIGTERM

def sigterm_handler(signal, frame):
    sys.exit(0)

def init_static_operations():
    pass

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', front=False):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.front = front

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        # 注册程序退出时候,执行的动作
        atexit.register(self.delpid)
        pid = str(os.getpid())
        # 讲自己的进程号,写入
        file(self.pidfile,'w+').write("%s\n" % pid)

    # 在程序退出的时候调用
    def delpid(self):
        """
        The description of delpid comes here.
        @return
        """
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        if self.status():
            print "pidfile already exist. Daemon already running?\n"
            sys.exit(1)

        # do pre stuff
        r=self.pre_start()
        if r: sys.exit(r)
        if not self.front:
            # Start the daemon
            self.daemonize()
        
        # t = MyThread("","","")
        # t.setDaemon(True)
        # t.start()

        signal(SIGTERM, sigterm_handler)
        try:
            self.run()
        except Exception as e:
            print "Stop ... %s " % e

    def status(self):
        """
        Check if pid exists and running (/proc/pid)
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, ValueError):
            pid = None

        if pid and os.path.isdir('/proc/%s' % pid):
            return True

        return False

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, ValueError):
            pid = None

        if not pid:
            return

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def pre_start(self):
        """
        Override this method to initialize stuff before daemonizing.
        return code other than 0 will fail daemonizing.
        """
        return 0

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass
