# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import logging
import logging.handlers
from pdsframe.common.config import config

class Logger:
    def init(self):
        log_level    =  config.safe_get('log', 'level')
        log_path     =  config.safe_get('log', 'path')
        log_maxsize  =  int(config.safe_get('log', 'maxsize'))
        log_maxcount =  int(config.safe_get('log', 'maxcount'))
        log_prefix   =  config.safe_get('log', 'prefix')
        
        if log_level == "debug":
            log_level = logging.DEBUG
        elif log_level == "info":
            log_level = logging.INFO
        elif log_level == "warning":
            log_level = logging.WARNING
        elif log_level == "error":
            log_level = logging.ERROR
        elif log_level == "critical":
            log_level = logging.CRITICAL
        else:
            log_level = logging.DEBUG
        
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        
        logfile = lambda file_name: os.path.join(log_path, file_name)
        
        run_log_file = logfile("%s.log" % config.safe_get("log","prefix"))
        
        # 运行日志
        self.run = logging.getLogger('run')
        hdlr = logging.handlers.RotatingFileHandler(run_log_file, maxBytes=log_maxsize, backupCount=log_maxcount)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        hdlr.setFormatter(formatter)
        self.run.setLevel(log_level)

        # 终端日志
        console = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        console.setFormatter(formatter)
        console.setLevel(logging.INFO)

        self.run.addHandler(hdlr)
        self.run.addHandler(console)

def init_logger():
    logger.init()

logger = Logger()
