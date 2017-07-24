# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import time,struct,socket,json
import base64
import hashlib
from pdsframe import *
from service_mds import g
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds
import message.ios_pb2 as msg_ios

# 定时配置8小时更新
MAX_UPDATE_TIME = 8*3600

#需要备份的配置文件,和该文件对应的md5值
upload_files    = {"/opt/smartmgr/conf/smartmgr.conf":None,"/opt/smartmgr/files/conf/pbdata.lic":None}

class LoopUploadFileConfMachine(BaseMachine):
    __metaclass__ = MataMachine
    
    LOOP_TIME         = 20
    LAST_UPLOAD_TIME  = 0
    FIRST_UPLOAD_FLAG = False

    def INIT(self):
        if int(time.time()) - LoopUploadFileConfMachine.LAST_UPLOAD_TIME > MAX_UPDATE_TIME:
            LoopUploadFileConfMachine.FIRST_UPLOAD_FLAG = True

        if g.smartmon_ip == None:
            return MS_FINISH

        upload_info              = msg_pds.FileUploadInfo()
        upload_info.node_name    = g.node_info.node_name
        upload_info.first_upload = True
        upload_info.listen_ip    = config.safe_get('network', 'listen-ip')
        backup_count = 0
        for fc in upload_files:
            file_name                = os.path.basename(fc)
            if not os.path.exists(fc):
                logger.run.error("%s not exists" % file_name)
                continue
            try:
                with open(fc,'rb') as f:
                   content = f.read()
                f.close()
            except:
                logger.run.error("read %s file failed"%file_name)
                continue
            m = hashlib.md5()
            m.update(content)
            md5 = m.hexdigest()
            if md5 != upload_files[fc] or LoopUploadFileConfMachine.FIRST_UPLOAD_FLAG == True:
                backup_count            += 1
                file_info                = upload_info.fileinfo.add()
                file_info.file_name      = file_name
                file_info.file_content   = base64.b64encode(content)
                upload_files[fc]         = md5

        if backup_count == 0:
            return MS_FINISH

        self.mds_request = MakeRequest(msg_mds.UPLOAD_CONF_FILE_REQUEST)
        self.mds_request.body.Extensions[msg_mds.upload_conf_file_request].file_upload.CopyFrom(upload_info) 
        self.SendRequest(g.smartmon_ip, g.listen_port, self.mds_request, self.Entry_Backup)
        logger.run.info("backup conf file to %s" % g.smartmon_ip)
        LoopUploadFileConfMachine.LAST_UPLOAD_TIME  = int(time.time())
        LoopUploadFileConfMachine.FIRST_UPLOAD_FLAG = False

        return MS_CONTINUE

    def Entry_Backup(self,result):
        return MS_FINISH

