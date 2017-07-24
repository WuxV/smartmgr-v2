# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from pdsframe import *
from service_mds import g
import base64
import time
import re
import message.pds_pb2 as msg_pds
import message.mds_pb2 as msg_mds

class UploadConfFileMachine(BaseMachine):
    __metaclass__ = MataMachine

    MID = msg_mds.UPLOAD_CONF_FILE_REQUEST

    def INIT(self, request):
        self.response        = MakeResponse(msg_mds.UPLOAD_CONF_FILE_RESPONSE, request)
        self.request         = request
        self.request_body    = request.body.Extensions[msg_mds.upload_conf_file_request]

        self.LongWork(self.recv_file_and_storage,self.request_body.file_upload)

        self.response.rc.retcode = msg_pds.RC_SUCCESS
        self.SendResponse(self.response)
        return MS_FINISH

    def get_file_verison(self, node_dir, file_name):
        filenums = {}
        tmp = []
        files    = os.listdir(node_dir)
        for f in files:
            version_num = f.split('_')
            if file_name in f and len(version_num) == 3 and version_num[2].isdigit():
                filenums[version_num[2]] = version_num[1] 
        if len(filenums) == 0:
            return 0,0
        for i in filenums.keys():
            tmp.append(int(i))
        max_num = max(tmp)
        min_num = min(tmp)
        diff = max_num - min_num
        version = max_num + 1
        if diff >= 100:
            file_name = file_name + "_" + str(filenums[str(min_num)]) + "_" + str(min_num)
            file_name = node_dir + "/" + file_name
            if os.path.exists(file_name):
                os.remove(file_name)
        return 0,version

    def recv_file_and_storage(self, request_body):
        rc = msg_pds.ResponseCode()
        if request_body.HasField('first_upload') and request_body.first_upload == True:
            if not os.path.isdir(g.bak_dir):
                os.makedirs(g.bak_dir)
            try:
                for _file in request_body.fileinfo:
                    node_name = request_body.node_name + "_" + request_body.listen_ip
                    node_dir  = os.path.join(g.bak_dir, node_name)
                    if not os.path.isdir(node_dir):
                        os.mkdir(node_dir)
                    ret,version = self.get_file_verison(node_dir,_file.file_name)
                    local_time = time.strftime('%Y%m%d%H',time.localtime(time.time()))
                    file_name = _file.file_name + "_" + str(local_time) + "_" + str(version)
                    file_name = os.path.join(node_dir,file_name)
                    content   = base64.decodestring(_file.file_content)
                    with open(file_name,'wb') as f:
                        f.write(content)
                    f.close()
            except:
                logger.run.error("Recv upload file from %s error" % request_body.node_name) 
                rc.retcode = msg_mds.RC_MDS_UPLOAD_FILE_FAIL
                return rc,None

            logger.run.info("Recv upload file from %s success" % request_body.node_name)
            rc.retcode = msg_pds.RC_SUCCESS
            return rc,None

        elif request_body.HasField('first_upload') and request_body.first_upload == False:
            if not os.path.isdir(g.second_bak_dir):
                os.makedirs(g.second_bak_dir)
            try:
                for _file in request_body.fileinfo:
                    ret,version = self.get_file_verison(g.second_bak_dir,_file.file_name)
                    local_time = time.strftime('%Y%m%d%H',time.localtime(time.time()))
                    file_name = _file.file_name + "_" + str(local_time) + "_" + str(version)
                    file_name = os.path.join(g.second_bak_dir,file_name)
                    content = base64.decodestring(_file.file_content)
                    with open(file_name,'wb') as f:
                        f.write(content)
                    f.close()
            except:
                logger.run.error("Recv second  upload file from %s error" % request_body.node_name) 
                rc.retcode = msg_mds.RC_MDS_UPLOAD_FILE_FAIL
                return rc,None

            logger.run.info("Recv second upload file from %s success" % request_body.node_name)
            rc.retcode = msg_pds.RC_SUCCESS
            return rc,None

