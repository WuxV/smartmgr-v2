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

#压缩文件名和临时压缩目录
TMP_DIR = "/tmp"
BAK_TAR = "backup.tar.gz"

# 最长需要24小时更新
MAX_UPDATE_TIME = 24*3600

class LoopSecondUploadConfigMachine(BaseMachine):
    __metaclass__ = MataMachine

    LOOP_TIME          = 60
    LAST_UPLOAD_TIME   = 0
    SECOND_UPLOAD_FLAG = False

    def INIT(self):
        if g.second_storage_ip == None:
            if not os.path.exists(g.second_storage_ip_file):
                return MS_FINISH
            else:
                with open(g.second_storage_ip_file,'rb') as f:
                    g.g.second_storage_ip = f.read()
                f.close()
                
        if int(time.time()) - LoopSecondUploadConfigMachine.LAST_UPLOAD_TIME > MAX_UPDATE_TIME:
            LoopSecondUploadConfigMachine.SECOND_UPLOAD_FLAG = True

        if LoopSecondUploadConfigMachine.SECOND_UPLOAD_FLAG == False:
            return MS_FINISH

        if not os.path.isdir(TMP_DIR):
            os.mkdir(TMP_DIR)
        target_file = os.path.join(TMP_DIR,BAK_TAR)
        source_file = g.bak_dir
        try:
            e, out = command("/bin/tar -zcvf %s %s"% (target_file,source_file))
        except:
            return MS_FINISH
        
        upload_info              = msg_pds.FileUploadInfo()
        upload_info.node_name    = g.node_info.node_name
        upload_info.first_upload = False
        try:
            with open(target_file,'rb') as f:
               content = f.read()
               f.close()
        except:
            logger.run.error("read %s file failed"%BAK_TAR)
            return MS_FINISH

        if LoopSecondUploadConfigMachine.SECOND_UPLOAD_FLAG == True:
            file_info              = upload_info.fileinfo.add()
            file_info.file_name    = BAK_TAR
            file_info.file_content = base64.b64encode(content)

        self.mds_request    = MakeRequest(msg_mds.UPLOAD_CONF_FILE_REQUEST)
        self.mds_request.body.Extensions[msg_mds.upload_conf_file_request].file_upload.CopyFrom(upload_info) 
        self.SendRequest(g.second_storage_ip, g.listen_port, self.mds_request, self.Entry_upload)
        LoopSecondUploadConfigMachine.LAST_UPLOAD_TIME = int(time.time())
        LoopSecondUploadConfigMachine.SECOND_UPLOAD_FLAG = False
        return MS_CONTINUE

    def Entry_upload(self,result):
        return MS_FINISH
