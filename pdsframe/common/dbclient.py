# coding: utf-8

import sys, json, os
from pdsframe.common.logger import logger
from pdsframe.common.config import config

CURR_DB_VERSION = "v2"

RC_SUCCESS              = 0
RC_ERR_CONFIG_RW        = 10
RC_ERR_PATH_ILLEGAL     = 20
RC_ERR_NODE_EXIST       = 30
RC_ERR_NODE_NOT_EXIST   = 40
RC_ERR_PARENT_EXIST     = 50
RC_ERR_PARENT_NOT_EXIST = 60

class DBClient():
    def __init__(self, db_file):
        self.db_file = db_file

    # 检查地址是否合法
    # path    : 分目录节点和叶子节点
    # is_node : 分是否检查叶子节点
    def check_path(self, path, is_node):
        if not path.startswith("/"):
            return -1
        if is_node:
            if path.endswith("/"):
                return -1
            for item in path.split("/")[1:]:
                if item == "" or len(item) != len(item.strip()):
                    return -1
        else:
            if not path.endswith("/"):
                return -1
            for item in path.split("/")[1:-1]:
                if item == "" or len(item) != len(item.strip()):
                    return -1
        return 0
    
    # 获取列表
    # path: /p/p/p/
    def list(self, path):
        if self.check_path(path, False):
            return RC_ERR_PATH_ILLEGAL, None
        try:
            f = open(self.db_file, 'r')
            content = json.loads(f.read())
            f.close()
        except:
            return RC_ERR_CONFIG_RW, None
        s_paths = path.split("/")
        parent  = content
        for i, s_path in enumerate(s_paths[1:-1]):
            if s_path not in parent.keys():
                return RC_ERR_PARENT_NOT_EXIST, None
            parent = parent[s_path]
        return RC_SUCCESS, parent

    # 获取
    # path: /p/p/p/n
    def get(self, path):
        if self.check_path(path, True):
            return RC_ERR_PATH_ILLEGAL, None
        try:
            f = open(self.db_file, 'r')
            content = json.loads(f.read())
            f.close()
        except:
            return RC_ERR_CONFIG_RW, None
        s_paths = path.split("/")
        parent  = content
        for i, s_path in enumerate(s_paths[1:-1]):
            if s_path not in parent.keys():
                return RC_ERR_PARENT_NOT_EXIST, None
            parent = parent[s_path]
        if s_paths[-1] not in parent.keys():
            return RC_ERR_NODE_NOT_EXIST, None
        return RC_SUCCESS, parent[s_paths[-1]]

    # 创建
    # path: /p/p/p/n
    # data: dict
    def create(self, path, data):
        if self.check_path(path, True):
            return RC_ERR_PATH_ILLEGAL, None
        try:
            f = open(self.db_file, 'r')
            content = json.loads(f.read())
            f.close()
        except Exception as e:
            return RC_ERR_CONFIG_RW, None
        s_paths = path.split("/")
        parent  = content
        for i, s_path in enumerate(s_paths[1:-1]):
            if s_path not in parent.keys():
                parent[s_path] = {}
            parent = parent[s_path]
        if s_paths[-1] in parent.keys():
            return RC_ERR_NODE_EXIST, None
        parent[s_paths[-1]] = data
        try:
            tmp_db_file = "/opt/smartmgr/conf/.smartmgr.tmp"
            f = open(tmp_db_file, 'w', 0)
            f.write(json.dumps(content, indent=4))
            os.fdatasync(f)
            f.close()
            os.rename(tmp_db_file, self.db_file)
        except Exception as e:
            print "xxxxxxxxxxxxx"
            return RC_ERR_CONFIG_RW, None
        return RC_SUCCESS, None

    # 更新
    # path: /p/p/p/n
    # data: dict
    def update(self, path, data):
        if self.check_path(path, True):
            return RC_ERR_PATH_ILLEGAL, None
        try:
            f = open(self.db_file, 'r')
            content = json.loads(f.read())
            f.close()
        except:
            return RC_ERR_CONFIG_RW, None
        s_paths = path.split("/")
        parent  = content
        for i, s_path in enumerate(s_paths[1:-1]):
            if s_path not in parent.keys():
                return RC_ERR_PARENT_NOT_EXIST, None
            parent = parent[s_path]
        if s_paths[-1] not in parent.keys():
            return RC_ERR_NODE_NOT_EXIST, None
        parent[s_paths[-1]] = data
        try:
            tmp_db_file = "/opt/smartmgr/conf/.smartmgr.tmp"
            f = open(tmp_db_file, 'w', 0)
            f.write(json.dumps(content, indent=4))
            os.fdatasync(f)
            f.close()
            os.rename(tmp_db_file, self.db_file)
        except:
            return RC_ERR_CONFIG_RW, None
        return RC_SUCCESS, None

    # 删除
    # path: /p/p/p/n
    def delete(self, path):
        if self.check_path(path, True):
            return RC_ERR_PATH_ILLEGAL, None
        try:
            f = open(self.db_file, 'r')
            content = json.loads(f.read())
            f.close()
        except:
            return RC_ERR_CONFIG_RW, None
        s_paths = path.split("/")
        parent  = content
        for i, s_path in enumerate(s_paths[1:-1]):
            if s_path not in parent.keys():
                return RC_ERR_PARENT_NOT_EXIST, None
            parent = parent[s_path]
        if s_paths[-1] not in parent.keys():
            return RC_ERR_NODE_NOT_EXIST, None
        parent.pop(s_paths[-1])
        try:
            tmp_db_file = "/opt/smartmgr/conf/.smartmgr.tmp"
            f = open(tmp_db_file, 'w', 0)
            f.write(json.dumps(content, indent=4))
            os.fdatasync(f)
            f.close()
            os.rename(tmp_db_file, self.db_file)
        except:
            return RC_ERR_CONFIG_RW, None
        return RC_SUCCESS, None

class DBService():
    def init(self, db_file):
        self.srv = DBClient(db_file)

    def check_version(self, db_file):
        try:
            f = open(db_file, 'r')
            content = json.loads(f.read())
            f.close()
            version = content['version'].lower()
            if version != CURR_DB_VERSION:
                logger.run.info("Start update config from %s" % version)
                getattr(self, "_update_config_from_%s" % version)(db_file)
        except Exception as e:
            logger.run.info("Update config failed: %s" % e)
            sys.exit(-1)
            return -1

    def _update_config_from_v1(self, db_file):
        f = open(db_file, 'r')
        content = f.read()
        f.close()
        content = content.replace('target_id',       'palcache_id')
        content = content.replace('target_name',     'palcache_name')
        content = content.replace('"target"',        '"palcache"')
        content = content.replace('"version": "v1"', '"version": "%s"' % CURR_DB_VERSION)

        tmp_db_file = "%s.v2" % db_file
        f = open(tmp_db_file, 'w', 0)
        f.write(content)
        os.fdatasync(f)
        f.close()
        os.rename(db_file, "%s.v1.bak" % db_file)
        os.rename(tmp_db_file,  db_file)

def init_dbservice():
    db_file = config.safe_get('model-config', 'db_file')
    if not os.path.exists(db_file):
        try:
            f = open(db_file, 'w', 0)
            f.write(json.dumps({"version":CURR_DB_VERSION}, indent=4))
            f.close()
        except Exception as e:
            logger.run.error("Init db file '%s' failed : %s" % (db_file, e))
            assert(0)

    dbservice.check_version(db_file)
    dbservice.init(db_file)

dbservice = DBService()

# if __name__ == "__main__":
#     init_dbservice()
# 
#     # 获取
#     print dbservice.srv.get("/version")
# 
#     # 创建
#     data = {}
#     data['logical_name'] = "hd01"
#     data['uuid']         = "cadaaefc-48ab-11e6-a372-525400eb54ec"
#     print dbservice.srv.create("/disk/cadaaefc-48ab-11e6-a372-525400eb54ed", data)
# 
#     # 列表
#     print dbservice.srv.list("/disk/")
# 
#     # 获取
#     print dbservice.srv.get("/disk/cadaaefc-48ab-11e6-a372-525400eb54ed")
# 
#     # 更新
#     data = {}
#     data['logical_name'] = "hd09"
#     data['uuid']         = "cadaaefc-48ab-11e6-a372-525400eb54ec"
#     print dbservice.srv.update("/disk/cadaaefc-48ab-11e6-a372-525400eb54ed", data)
# 
#     # 删除
#     print dbservice.srv.delete("/disk/cadaaefc-48ab-11e6-a372-525400eb54ed")
