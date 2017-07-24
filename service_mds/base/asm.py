#!/usr/bin/env python
# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import re
import pyodbc
from pdsframe import *

class OraSQLPlus(object):
    def __init__(self, servicename,ip,port,uid,passwd):
        self.servicename = servicename
        self.ip = ip
        self.port = port
        self.uid = uid
        self.passwd = passwd
        self.connStr = False
        self.cursor = False

    def connect(self):
        if not self.connStr:
            try:
                dsn = "driver=Oracle;dbq=%s:%s/%s;uid=%s;pwd=%s" \
                        %(self.ip,self.port,self.servicename,self.uid,self.passwd)
                self.connStr = pyodbc.connect(dsn)
            except Exception, err:
                logger.run.error("Could not connect to oracle service: %s" %err)
                return (-1,"Could not connect to oracle service: %s" %err)
        if not self.cursor:
            try:
                self.cursor = self.connStr.cursor()
            except Exception, err:
                self.connStr.close()
                logger.run.error("Could not do oracle cursor: %s" %err)
                return (-1, "Could not do oracle cursor: %s" %err)
        return (0, "OK")
 
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connStr:
            self.connStr.close()

    def runSelect(self, stmt):
        ret, result = self.connect()
        if ret:
            return (ret, result)
        try:
            self.cursor.execute(stmt)
            rows = self.cursor.fetchall()
            if len(rows)==0:
                return(0,[("","")])
            return (0, rows)
        except Exception, err:
            logger.run.error("Execute sql failed: %s" %err)
            return (-1, "Execute sql failed: %s" %err)

    def list_asm_group(self):
        '''List all ASM Groups '''
        sql = "select group_number,name,type,state,OFFLINE_DISKS,to_char(TOTAL_MB, 'FM9999999999999999'),to_char(FREE_MB, 'FM9999999999999999'),\
                       to_char(USABLE_FILE_MB, 'FM9999999999999999') from v$asm_diskgroup ORDER BY 1"
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        lst = []
        for i in result:
            if len(i)>7:
                dg = {}
                dg["group_number"] = int(i[0])
                dg["name"] = i[1]
                dg["type"] = i[2]
                dg["state"] = i[3]
                dg["offline_disks"] = i[4]
                dg["total_mb"] = i[5]
                dg["free_mb"] = i[6]
                dg["usable_file_mb"] = i[7]
                lst.append(dg)
        return (ret, lst)

    def list_asm_disks(self):
        '''List all ASM Disks'''
        sql = "select group_number, disk_number,name,state,mode_status,path,failgroup,to_char(TOTAL_MB, 'FM9999999999999999'),\
                    to_char(FREE_MB, 'FM9999999999999999') from v$asm_disk order by 1"
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        lst = []
        for d in result:
            if len(d) > 8: 
                disk = {}
                disk["group_number"] = int(d[0])
                disk["disk_number"] = int(d[1])
                disk["name"] = d[2]
                disk["state"] = d[3]
                disk["mode_status"] = d[4]
                disk["path"] = d[5]
                disk["failgroup"] = d[6]
                disk["total_mb"] = d[7]
                disk["free_mb"] = d[8]
                lst.append(disk)
        return (ret, lst)

class AsmOraSQLPlus(object):
    def __init__(self,home):
        self.home = home
        cmd = 'sqlplus'
        self.sqlplus = os.path.join(self.home, 'bin', cmd)

    def runSelect(self, stmt):
        cmd_str = 'su - grid -c "%s -S / as sysasm <<EOF\n%s;\nEOF"' % (self.sqlplus,stmt)
        e, out = command(cmd_str)
        if e:
            logger.run.error("Call Oracle sql[%s] failed: %s" % (stmt, out))
            return (-1, out)

        txt = out.splitlines()
        ora = []
        for k in range(len(txt)):
            m = re.search(r"(ORA-\d+):\s+([^\r\n]*)", txt[k])
            if m:
                ora.append(m.group(1) + ": " + m.group(2))
        if ora:
            logger.run.error("Search Oracle sql[%s] select result find: %s" % (stmt, ', '.join(ora)))
            return (-1, ', '.join(ora))
        # Get lines and strip away the prefix and post-fix of SQL*Plus
        lines = out.strip().split('\n')
        return (0, [[col.strip() for col in line.split('|')] for line in lines])
 
    def add_asm_group(self, group_name, disk_paths, failgroups, redundancy='external', compatible_asm='10.1', compatible_rdbms='10.1'):
        part_sql = ""
        for i in range(len(disk_paths)):
            if len(failgroups) > i:
                part_sql += " failgroup %s disk '%s'" % (failgroups[i], disk_paths[i])
            else:
                part_sql += " disk '%s'" % disk_paths[i]

        sql = "create diskgroup %s %s redundancy%s attribute 'compatible.asm'='%s','compatible.rdbms'='%s'" % (group_name, redundancy, part_sql, compatible_asm, compatible_rdbms)
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def drop_asm_group(self, group_name):
        sql = "drop diskgroup %s including contents" % group_name
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def mount_asm_group(self, group_name):
        sql = "alter diskgroup %s mount" % group_name
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def umount_asm_group(self, group_name):
        sql = "alter diskgroup %s dismount" % group_name
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def add_asm_disk(self, group_name, disk_path, force, failgroup):
        if failgroup and not force:
            sql = "alter diskgroup %s add failgroup %s disk '%s'" % (group_name, failgroup, disk_path)
        elif failgroup and force:
            sql = "alter diskgroup %s add failgroup %s disk '%s' force" % (group_name, failgroup, disk_path)
        elif not failgroup and force:
            sql = "alter diskgroup %s add disk '%s' force" % (group_name, disk_path)
        else:
            sql = "alter diskgroup %s add disk '%s'" % (group_name, disk_path)
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def drop_asm_disk(self, group_name, disk_name, force):
        if force:
            sql = "alter diskgroup %s drop disk %s force" % (group_name, disk_name)
        else:
            sql = "alter diskgroup %s drop disk %s" % (group_name, disk_name)
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')
        
    def online_asm_disk(self, group_name, disk_name="", failgroup=""):
        if disk_name:
            sql = "alter diskgroup %s online disk %s" % (group_name, disk_name)
        elif failgroup:
            sql = "alter diskgroup %s online disks in failgroup %s" % (group_name, failgroup)
        else:
            return (-1, "Must be specified disk_name or failgroup")

        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def offline_asm_disk(self, group_name, disk_name="", failgroup=""):
        if disk_name:
            sql = "alter diskgroup %s offline disk %s" % (group_name, disk_name)
        elif failgroup:
            sql = "alter diskgroup %s offline disks in failgroup %s" % (group_name, failgroup)
        else:
            return (-1, "Must be specified disk_name or failgroup")

        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

    def alter_asm_rebalance(self, group_name, power):
        sql = "alter diskgroup %s rebalance power %d" % (group_name, power)
        ret, result = self.runSelect(sql)
        if ret:
            logger.run.error("Execute sql[%s] failed: %s" %(sql,result))
            return (ret, result)

        return (0, '')

def get_grid_env():
    cmd = "ps -ef|grep pmon |grep asm|grep -v grep|grep -v sed| awk '{print $NF}'| sed 's/ora_pmon_//g'"
    e, out = command(cmd)
    found = 0
    ins = {}
    if not e:
        out = out.strip()
        if out:
            lines = out.splitlines()
            for line in lines:
                if "+" in line:
                    ins["asm_instance"] = "+" + line.split("+")[1]
                    found = 1
            if not found:
                return (-1, "No online instance found")
        else:
            return (-1, "No online instance found")
    else:
        return (-1, out)
    found = 0
    cmd = "ps -ef|grep ohasd.bin|grep -v grep|grep -v sed| awk '{print $8}'"
    e, out = command(cmd)
    if not e:
        out = out.strip()
        if out:
            lines = out.splitlines()
            for line in lines:
                if "ohasd" in line:
                    ins["grid_home"] = line.split("/bin/ohasd")[0]
                    found = 1

            if not found:
                return (-1, "Not find grid home from %s" % cmd)
        if not found:
            return (-1, "Not find grid home from %s" % cmd)
    else:
        return (-1, out)
    return (0, ins)

if __name__ == '__main__':
    params = {}
    params["servicename"]="DBM"
    params["ip"]="172.16.9.215"
    params["port"]="1521"
    params["uname"]="smartmon"
    params["upass"]="123456"
    sqlplus = OraSQLPlus(params["servicename"], params["ip"], params["port"], params["uname"], params["upass"])
    print sqlplus.list_asm_group()
    print sqlplus.list_asm_disks()
