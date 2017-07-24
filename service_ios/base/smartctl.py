#!/usr/bin/env python
# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Python built-ins
'''
Created on 2016年5月23日

@author: qing_wang
'''

#from __future__ import print_function
import string
import ctypes
import os
import platform
# from subprocess import Popen, PIPE
import warnings
import re  # Don't delete this 'un-used' import
import commands

from pdsframe.common.logger import logger

def command_stdout_stderr(cmd,timeout = 60*10):
    e, res = commands.getstatusoutput("/usr/bin/timeout %s %s" % (timeout, cmd))
    if e:
        return "", res
    return res, ""

def command_stdout(cmd,timeout = 60*10):
    e, res = commands.getstatusoutput("/usr/bin/timeout %s %s" % (timeout, cmd))
    return res, ""

# Configuration definitions
_min_smartctl_ver = {
    'Windows' : {
        'maj' : 6,
        'min' : 1
        },
    'Linux' : {
        'maj' : 5,
        'min' : 42
        },
    'FreeBSD' : {
        'maj' : 6,
        'min' : 1
        }
    }
"""
(dict of dict of int): Outer dict contains operating system names as keys.
Inner dict has keys 'maj' and 'min' with int values representing the minimum
required major and minor versions, respectively.
"""

OS = platform.system()
"""**(str):** The operating system's name, generally 'Linux' or 'Windows'"""

_req_ma, _req_mi = _min_smartctl_ver[OS]['maj'], _min_smartctl_ver[OS]['min']
"""Major and minor version requirements, parsed from the version string."""

smartctl_type = {
    'ata' : 'ata',
    'csmi' : 'ata',
    'sas' : 'scsi',
    'sat' : 'sat',
    'sata' : 'ata',
    'scsi' : 'scsi'
}
"""
**(dict of str):** Contains actual interface types (ie: sas, csmi) as keys and
the corresponding smartctl interface type (ie: scsi, ata) as values.
"""
smartctl_raid_type =["megaraid","cciss"]
"""
支持的raid列表
"""
        

# Helper functions
def admin():
    """Determine whether this scrpt is running with administrative privilege.

    ### Returns:
    * **(bool):** True if running as an administrator, False otherwise.
    """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin


# Verify smartctl is on the system path and meets the minimum required version
# cmd = Popen('smartctl --version', shell=True, stdout=PIPE, stderr=PIPE)
# _stdout, _stderr = cmd.communicate()
cmd = 'smartctl --version'
_stdout, _stderr = command_stdout_stderr(cmd)
if _stdout == '':
    raise Exception(
        "Required package 'smartmontools' is not installed, or 'smartctl'\n"
        "component is not on the system path. Please install and try again.")
else:
    for line in _stdout.split('\n'):
        if 'release' in line:
            _ma, _mi = line.strip().split(' ')[2].split('.')
            if (int(_ma) < _req_ma or
                    (int(_ma) == _req_ma and int(_mi) < _req_mi)):
                raise Exception(
                    "Installed version of smartctl [{0}.{1}] is below the "
                    "minimum requirement of [{2}.{3}]. Please upgrade and "
                    "try again.".format(_ma, _mi, _req_ma, _req_mi))

# Check for admin rights
if not admin():
    logger.run.warn(
        "_NOT_ADMIN_: smartctl is intended to be run as administrator/root "
        "and may not detect all device types, or may parse device information "
        "incorrectly, if run without these permissions.")

class Attribute(object):
    """
    Contains all of the information associated with a single SMART attribute
    in a `Device`'s SMART table. This data is intended to exactly mirror that
    obtained through smartctl.
    """
    def __init__(self, num, name, flags, value, worst, thresh, attr_type,
                 updated, when_failed, raw):
        self.num = num
        """**(str):** Attribute's ID as a decimal value (1-255)."""
        self.name = name
        """
        **(str):** Attribute's name, as reported by smartmontools' drive.db.
        """
        self.flags = flags
        """**(str):** Attribute flags as a hexadecimal value (ie: 0x0032)."""
        self.value = value
        """**(str):** Attribute's current normalized value."""
        self.worst = worst
        """**(str):** Worst recorded normalized value for this attribute."""
        self.thresh = thresh
        """**(str):** Attribute's failure threshold."""
        self.type = attr_type
        """**(str):** Attribute's type, generally 'pre-fail' or 'old-age'."""
        self.updated = updated
        """
        **(str):** When is this attribute updated? Generally 'Always' or
        'Offline'
        """
        self.when_failed = when_failed
        """
        **(str):** When did this attribute cross below
        `pySMART.attribute.Attribute.thresh`? Reads '-' when not failed.
        Generally either 'FAILING_NOW' or 'In_the_Past' otherwise.
        """
        self.raw = raw
        """**(str):** Attribute's current raw (non-normalized) value."""

    def __repr__(self):
        """Define a basic representation of the class object."""
        return "<SMART Attribute %r %s/%s raw:%s>" % (
            self.name, self.value, self.thresh, self.raw)

    def __str__(self):
        """
        Define a formatted string representation of the object's content.
        In the interest of not overflowing 80-character lines this does not
        print the value of `pySMART.attribute.Attribute.flags_hex`.
        """
        return "{0:>3} {1:24}{2:4}{3:4}{4:4}{5:9}{6:8}{7:12}{8}".format(
            self.num, self.name, self.value, self.worst, self.thresh,
            self.type, self.updated, self.when_failed, self.raw)

class Test_Entry(object):
    """
    Contains all of the information associated with a single SMART Self-test
    log entry. This data is intended to exactly mirror that obtained through
    smartctl.
    """
    def __init__(self, format, num, test_type, status, hours, LBA, remain=None,
                 segment=None, sense=None, ASC=None, ASCQ=None):
        self._format = format
        """
        **(str):** Indicates whether this entry was taken from an 'ata' or
        'scsi' self-test log. Used to display the content properly.
        """
        self.num = num
        """
        **(str):** Entry's position in the log from 1 (most recent) to 21
        (least recent).  ATA logs save the last 21 entries while SCSI logs
        only save the last 20.
        """
        self.type = test_type
        """
        **(str):** Type of test run.  Generally short, long (extended), or
        conveyance, plus offline (background) or captive (foreground).
        """
        self.status = status
        """
        **(str):** Self-test's status message, for example 'Completed without
        error' or 'Completed: read failure'.
        """
        self.hours = hours
        """
        **(str):** The device's power-on hours at the time the self-test
        was initiated.
        """
        self.LBA = LBA
        """
        **(str):** Indicates the first LBA at which an error was encountered
        during this self-test. Presented as a decimal value for ATA/SATA devices
        and in hexadecimal notation for SAS/SCSI devices.
        """
        self.remain = remain
        """
        **(str):** Percentage value indicating how much of the self-test is
        left to perform. '00%' indicates a complete test, while any other
        value could indicate a test in progress or one that failed prior to
        completion. Only reported by ATA devices.
        """
        self.segment = segment
        """
        **(str):** A manufacturer-specific self-test segment number reported
        by SCSI devices on self-test failure. Set to '-' otherwise.
        """
        self.sense = sense
        """
        **(str):** SCSI sense key reported on self-test failure. Set to '-'
        otherwise.
        """
        self.ASC = ASC
        """
        **(str):** SCSI 'Additonal Sense Code' reported on self-test failure.
        Set to '-' otherwise.
        """
        self.ASCQ = ASCQ
        """
        **(str):** SCSI 'Additonal Sense Code Quaifier' reported on self-test
        failure. Set to '-' otherwise.
        """

    def __repr__(self):
        """Define a basic representation of the class object."""
        return "<SMART Self-test [%s|%s] hrs:%s LBA:%s>" % (
            self.type, self.status, self.hours, self.LBA)

    def __str__(self):
        """
        Define a formatted string representation of the object's content.
        Looks nearly identical to the output of smartctl, without overflowing
        80-character lines.
        """
        if self._format == 'ata':
            return "{0:>2} {1:17}{2:30}{3:5}{4:7}{5:17}".format(
                self.num, self.type, self.status, self.remain, self.hours,
                self.LBA)
        else:
            # 'Segment' could not be fit on the 80-char line. It's of limited
            # utility anyway due to it's manufacturer-proprietary nature...
            return ("{0:>2} {1:17}{2:23}{3:7}{4:14}[{5:4}{6:5}{7:4}]".format(
                        self.num, self.type, self.status, self.hours,
                        self.LBA, self.sense, self.ASC, self.ASCQ))

class Device(object):
    """
    Represents any device attached to an internal storage interface, such as a
    hard drive or DVD-ROM, and detected by smartmontools. Includes eSATA
    (considered SATA) but excludes other external devices (USB, Firewire).
    """
    def __init__(self, name, interface=None,did=None,raidtype=None):
        """Instantiates and initializes the `pySMART.device.Device`."""
        assert interface is None or interface.lower() in [
            'ata', 'csmi', 'sas', 'sat', 'sata', 'scsi']
        self.name = name.replace('/dev/', '')
        """
        **(str):** Device's hardware ID, without the '/dev/' prefix.
        (ie: sda (Linux))
        """

        self.model = None
        """**(str):** Device's model number."""
        self.serial = None
        """**(str):** Device's serial number."""
        self.interface = interface
        """
        **(str):** Device's interface type. Must be one of:
            * **ATA** - Advanced Technology Attachment
            * **SATA** - Serial ATA
            * **SCSI** - Small Computer Systems Interface
            * **SAS** - Serial Attached SCSI
            * **SAT** - SCSI-to-ATA Translation (SATA device plugged into a
            SAS port)
            * **CSMI** - Common Storage Management Interface (Intel ICH /
            Matrix RAID)
        Generally this should not be specified to allow auto-detection to occur.
        Otherwise, this value overrides the auto-detected type and could
        produce unexpected or no data.
        """
        self.did = did
        """
            当磁盘是通过raid时 did为必须的 raid卡中的device id
        """
        self.raidtype = raidtype
        """
            当指定raid卡类型时用
            smartctl -a -d megaraid,2 /dev/sda 命令 "2" device id
        """
        self.capacity = None
        """**(str):** Device's user capacity."""
        self.firmware = None
        """**(str):** Device's firmware version."""
        self.device_in_database=False
        """
        判断当前磁盘信息标志是否在smartctl数据库中
        """
        self.supports_smart = False
        """
        **(bool):** True if the device supports SMART (or SCSI equivalent) and
        has the feature set enabled. False otherwise.
        """
        self.assessment = None
        """**(str):** SMART health self-assessment as reported by the device."""
        self.messages = []
        """
        **(list of str):** Contains any SMART warnings or other error messages
        reported by the device (ie: ASCQ codes).
        """
        self.is_ssd = None
        """
        **(bool):** True if this device is a Solid State Drive.
        False otherwise.
        """
        self.attributes = [None] * 256
        """
        **(list of `Attribute`):** Contains the complete SMART table information
        for this device, as provided by smartctl. Indexed by attribute #,
        values are set to 'None' for attributes not suported by this device.
        """
        self.tests = []
        """
        **(list of `Log_Entry`):** Contains the complete SMART self-test log
        for this device, as provided by smartctl. If no SMART self-tests have
        been recorded, contains a `None` type instead.
        """
        self._test_running = False
        """
        **(bool):** True if a self-test is currently being run. False otherwise.
        """
        self._test_ECD = None
        """
        **(str):** Estimated completion time of the running SMART selftest.
        Not provided by SAS/SCSI devices.
        """
        self.diags = {}
        """
        **(dict of str):** Contains parsed and processed diagnostic information
        extracted from the SMART information. Currently only populated for
        SAS and SCSI devices, since ATA/SATA SMART attributes are manufacturer
        proprietary.
        """

        #print self.name
        if self.name is None:
            # logger.run.warn("\nDevice '{0}' does not exist! " "This object should be destroyed.".format(name))
            return
        # If no interface type was provided, scan for the device
        elif self.interface is None:
            _grep = 'find' if OS == 'Windows' else 'grep'
            # cmd = Popen('smartctl --scan-open | {0} "{1}"'.format(
            #     _grep, self.name), shell=True, stdout=PIPE, stderr=PIPE)
            # _stdout, _stderr = cmd.communicate()
            name = self.name[:-1] if len(self.name.strip()) > 3 else self.name
            cmd = 'smartctl --scan-open | {0} "{1}"'.format( _grep, name)
            _stdout, _stderr = command_stdout_stderr(cmd)
            if _stdout != '':
                if not _stdout.startswith("#"):
                    self.interface = _stdout.split(' ')[2]
                else:
                    self.interface = _stdout.split(' ')[3]

                # Disambiguate the generic interface to a specific type
                self._classify()
            else:
                # logger.run.warn("\nDevice '{0}' does not exist! " "This object should be destroyed.".format(name))
                return
        # If a valid device was detected, populate its information
        #print self.interface
        if self.interface is not None:
            self.update()

    def __repr__(self):
        """Define a basic representation of the class object."""
        return "<%s device on /dev/%s mod:%s sn:%s>" % (
            self.interface.upper(), self.name, self.model, self.serial)

    def all_attributes(self):
        """
        Prints the entire SMART attribute table, in a format similar to
        the output of smartctl.
        """
        lis = []
        header_printed = False
        #print self.attributes
        #print self.diags
        for attr in self.attributes:
            if attr is not None:
                #print attr.__dict__
                tmp = {}
                value_list=[]
                if not header_printed:
                    #print("{0:>3} {1:24}{2:4}{3:4}{4:4}{5:9}{6:8}{7:12}"
                    #      "{8}".format(
                    #          'ID#', 'ATTRIBUTE_NAME', 'CUR', 'WST', 'THR',
                    #          'TYPE', 'UPDATED', 'WHEN_FAIL', 'RAW'))
                    header_printed = True

                #tmp[attr.name] =[attr.value]  + [attr.raw]
                #lis.append(tmp)
                lis.append(attr.__dict__)
        if not header_printed:
            # logger.run.error("This device does not support SMART attributes.")
            return None
        return lis

    def all_selftests(self):
        """
        Prints the entire SMART self-test log, in a format similar to
        the output of smartctl.
        """
        if self.tests is not None:
            if smartctl_type[self.interface] == 'scsi':
                print("{0:3}{1:17}{2:23}{3:7}{4:14}{5:15}".format(
                    'ID', 'Test Description', 'Status', 'Hours',
                    '1st_Error@LBA', '[SK  ASC  ASCQ]'))
            else:
                print("{0:3}{1:17}{2:30}{3:5}{4:7}{5:17}".format(
                    'ID', 'Test_Description', 'Status', 'Left', 'Hours',
                    '1st_Error@LBA'))
            for test in self.tests:
                print(test)
        else:
            print("No self-tests have been logged for this device.")

    def _classify(self):
        """
        Disambiguates generic device types ATA and SCSI into more specific
        ATA, SATA, SAS, SAT and SCSI.
        """
        # SCSI devices might be SCSI, SAS or SAT
        # ATA device might be ATA or SATA
        if self.interface in ['scsi', 'ata']:
            if self.interface == 'scsi':
                test = 'sat'
            else:
                test = 'sata'
            # Look for a SATA PHY to detect SAT and SATA
            # cmd = Popen('smartctl -d {0} -l sataphy /dev/{1}'.format(
            #     smartctl_type[test], self.name), shell=True,
            #             stdout=PIPE, stderr=PIPE)
            # _stdout, _stderr = cmd.communicate()
            cmd = 'smartctl -d {0} -l sataphy /dev/{1}'.format(smartctl_type[test], self.name)
            _stdout, _stderr = command_stdout(cmd)
            if 'GP Log 0x11' in _stdout.split('\n')[3]:
                self.interface = test
        # If device type is still SCSI (not changed to SAT above), then
        # check for a SAS PHY
        if self.interface == 'scsi':
            # cmd = Popen('smartctl -d scsi -l sasphy /dev/{0}'.format(
            #     self.name), shell=True, stdout=PIPE, stderr=PIPE)
            # _stdout, _stderr = cmd.communicate()
            cmd = 'smartctl -d scsi -l sasphy /dev/{0}'.format(self.name)
            _stdout, _stderr = command_stdout(cmd)
            if len(_stdout.split('\n')) > 4 and 'SAS SSP' in _stdout.split('\n')[4]:
                self.interface = 'sas'
            # Some older SAS devices do not support the SAS PHY log command.
            # For these, see if smartmontools reports a transport protocol.
            else:
                # cmd = Popen('smartctl -d scsi -a /dev/{0}'.format(
                #     self.name), shell=True, stdout=PIPE, stderr=PIPE)
                # _stdout, _stderr = cmd.communicate()
                cmd = 'smartctl -d scsi -a /dev/{0}'.format(self.name)
                _stdout, _stderr = command_stdout(cmd)
                for line in _stdout.split('\n'):
                    if 'Transport protocol' in line and 'SAS' in line:
                        self.interface = 'sas'

    def get_selftest_result(self, output=None):
        """
        Refreshes a device's `pySMART.device.Device.tests` attribute to obtain
        the latest test results. If a new test result is obtained, its content
        is returned.

        ###Args:
        * **output (str, optional):** If set to 'str', the string
        representation of the most recent test result will be returned, instead
        of a `Test_Entry` object.

        ##Returns:
        * **(int):** Return status code. One of the following:
            * 0 - Success. Object (or optionally, string rep) is attached.
            * 1 - Self-test in progress. Must wait for it to finish.
            * 2 - No new test results.
        * **(`Test_Entry` or str):** Most recent `Test_Entry` object (or
        optionally it's string representation) if new data exists.  Status
        message string on failure.
        * **(str):** Estimated completion time of a test in-progess, if known.
        Otherwise 'None'.
        """
        # SCSI self-test logs hold 20 entries while ATA logs hold 21
        if smartctl_type[self.interface] == 'scsi':
            maxlog = 20
        else:
            maxlog = 21
        # If we looked only at the most recent test result we could be fooled
        # by two short tests run close together (within the same hour) appearing
        # identical. Comparing the length of the log adds some confidence until
        # it maxes, as above. Comparing the least-recent test result greatly
        # diminishes the chances that two sets of two tests each were run within
        # an hour of themselves, but with 16-17 other tests run in between them.
        if self.tests is not None:
            _first_entry = self.tests[0]
            _len = len(self.tests)
            _last_entry = self.tests[_len - 1]
        else:
            _len = 0
        self.update()
        # Check whether the list got longer (ie: new entry)
        if self.tests is not None and len(self.tests) != _len:
            # If so, for ATA, return the newest test result
            if not ('in progress' in self.tests[0].status or
                    'NOW' in self.tests[0].hours):
                self._test_running = False
                self._test_ECD = None
                if output == 'str':
                    return (0, str(self.tests[0]), None)
                else:
                    return (0, self.tests[0], None)
            else:
                self._test_running = True
        elif _len == maxlog:
            # If not, because it's max size already, check for new entries
            if ((_first_entry.type != self.tests[0].type or
                    _first_entry.hours != self.tests[0].hours or
                    _last_entry.type != self.tests[len(self.tests) - 1].type or
                    _last_entry.hours != self.tests[len(self.tests) - 1].hours)
                and not 'NOW' in self.tests[0].hours):
                self._test_running = False
                self._test_ECD = None
                if output == 'str':
                    return (0, str(self.tests[0]), None)
                else:
                    return (0, self.tests[0], None)
            else:
                if 'NOW' in self.tests[0].hours:
                    self._test_running = True
                # If nothing new was found, see if we know of a running test.
                if self._test_running:
                    if (not ('in progress' in self.tests[0].status or
                             'NOW' in self.tests[0].hours) and
                            smartctl_type[self.interface] == 'scsi'):
                        self._test_running = False
                        self._test_ECD = None
                        if output == 'str':
                            return (0, str(self.tests[0]), None)
                        else:
                            return (0, self.tests[0], None)
                    else:
                        return (1, 'Self-test in progress. Please wait.',
                                self._test_ECD)
                else:
                    return (2, 'No new self-test results found.', None)
        else:
            # If log is still empty, or did not get longer, see whether we
            # know of a running test.
            if self._test_running:
                if (not ('in progress' in self.tests[0].status or
                         'NOW' in self.tests[0].hours) and
                        smartctl_type[self.interface] == 'scsi'):
                    self._test_running = False
                    self._test_ECD = None
                    if output == 'str':
                        return (0, str(self.tests[0]), None)
                    else:
                        return (0, self.tests[0], None)
                else:
                    return (1, 'Self-test in progress. Please wait.',
                            self._test_ECD)
            else:
                return (2, 'No new self-test results found.', None)

    def _guess_SMART_type(self, line):
        """
        This function is not used in the generic wrapper, however the header
        is defined so that it can be monkey-patched by another application.
        """
        pass

    def _make_SMART_warnings(self):
        """
        Parses an ATA/SATA SMART table for attributes with the 'when_failed'
        value set. Generates an warning message for any such attributes and
        updates the self-assessment value if necessary.
        """
        if smartctl_type[self.interface] == 'scsi':
            return
        for attr in self.attributes:
            if attr is not None:
                if attr.when_failed == 'In_the_past':
                    self.messages.append("".join(
                        [attr.name, " failed in the past with value ",
                         attr.worst, ". [Threshold: ", attr.thresh, ']']))
                    if not self.assessment == 'FAIL':
                        self.assessment = 'WARN'
                elif attr.when_failed == 'FAILING_NOW':
                    self.assessment = 'FAIL'
                    self.messages.append("".join(
                        [attr.name, " is failing now with value ",
                         attr.value, ". [Threshold: ", attr.thresh, ']']))
                elif not attr.when_failed == '-':
                    self.messages.append("".join(
                        [attr.name, " says it failed '", attr.when_failed,
                         "'. [V=", attr.value, ",W=", attr.worst, ",T=",
                         attr.thresh, ']']))
                    if not self.assessment == 'FAIL':
                        self.assessment = 'WARN'

    def run_selftest(self, test_type):
        """
        Instructs a device to begin a SMART self-test. All tests are run in
        'offline' / 'background' mode, allowing normal use of the device while
        it is being tested.

        ##Args:
        * **test_type (str):** The type of test to run. Accepts the following
        (not case sensitive):
            * **short** - Brief electo-mechanical functionality check.
            Generally takes 2 minutes or less.
            * **long** - Thorough electro-mechanical functionality check,
            including complete recording media scan. Generally takes several
            hours.
            * **conveyance** - Brief test used to identify damage incurred in
            shipping. Generally takes 5 minutes or less. **This test is not
            supported by SAS or SCSI devices.**

        ##Returns:
        * **(int):** Return status code.  One of the following:
            * 0 - Self-test initiated successfully
            * 1 - Previous self-test running. Must wait for it to finish.
            * 2 - Unknown or illegal test type requested.
            * 3 - Unspecified smartctl error. Self-test not initiated.
        * **(str):** Return status message.
        * **(str):** Estimated self-test completion time if a test is started.
        Otherwise 'None'.
        """
        if self._test_running:
            return (1, 'Self-test already in progress. Please wait.',
                    self._test_ECD)
        if test_type.lower() in ['short', 'long', 'conveyance']:
            if (test_type.lower() == 'conveyance' and
                    smartctl_type[self.interface] == 'scsi'):
                return (2, "Cannot perform 'conveyance' test on SAS/SCSI "
                        "devices.", None)
            # cmd = Popen('smartctl -d {0} -t {1} /dev/{2}'.format(
            #     smartctl_type[self.interface], test_type, self.name),
            #             shell=True, stdout=PIPE, stderr=PIPE)
            # _stdout, _stderr = cmd.communicate()
            cmd = 'smartctl -d {0} -t {1} /dev/{2}'.format(smartctl_type[self.interface], test_type, self.name)
            _stdout, _stderr = command_stdout(cmd)
            _success = False
            _running = False
            for line in _stdout.split('\n'):
                if 'has begun' in line:
                    _success = True
                    self._test_running = True
                if 'aborting current test' in line:
                    _running = True
                if _success and 'complete after' in line:
                    self._test_ECD = line[25:].rstrip()
            if _success:
                return (0, "Self-test started successfully", self._test_ECD)
            else:
                if _running:
                    return (1, 'Self-test already in progress. Please wait.',
                            self._test_ECD)
                else:
                    return (3, 'Unspecified Error. Self-test not started.',
                            None)
        else:
            return (2, "Unknown test type '{0}' requested.".format(test_type),
                    None)

    def update(self):
        """
        Queries for device information using smartctl and updates all
        class members, including the SMART attribute table and self-test log.
        Can be called at any time to refresh the `pySMART.device.Device`
        object's data content.
        """
        logger.run.debug("[%s/%s]"%(self.did,self.raidtype))
        if self.did !=None and self.raidtype in smartctl_raid_type:
            logger.run.debug('smartctl -d {0},{1} -a /dev/{2}'.format(
                self.raidtype,self.did,self.name))
            # cmd = Popen('smartctl -d {0},{1} -a /dev/{2}'.format(
            #     self.raidtype,self.did,self.name), shell=True,
            #         stdout=PIPE, stderr=PIPE)
            cmd = 'smartctl -d {0},{1} -a /dev/{2}'.format(self.raidtype,self.did,self.name)
        else:
            logger.run.debug('smartctl -d {0} -a /dev/{1}'.format(
                smartctl_type[self.interface], self.name))
            # cmd = Popen('smartctl -d {0} -a /dev/{1}'.format(
            #     smartctl_type[self.interface], self.name), shell=True,
            #             stdout=PIPE, stderr=PIPE)
            cmd = 'smartctl -d {0} -a /dev/{1}'.format(smartctl_type[self.interface], self.name)
        # _stdout, _stderr = cmd.communicate()
        _stdout, _stderr = command_stdout(cmd)
        parse_self_tests = False
        parse_ascq = False
        self.tests = []
        for line in _stdout.split('\n'):
            if line.strip() == '':  # Blank line stops sub-captures
                if parse_self_tests == True:
                    parse_self_tests = False
                    if len(self.tests) == 0:
                        self.tests = None
                if parse_ascq:
                    parse_ascq = False
                    self.messages.append(message)
            if parse_ascq:
                message += ' ' + line.lstrip().rstrip()
            if parse_self_tests:
                num = line[1:3]
                if smartctl_type[self.interface] == 'scsi':
                    format = 'scsi'
                    test_type = line[5:23].rstrip()
                    status = line[23:46].rstrip()
                    segment = line[46:55].lstrip().rstrip()
                    hours = line[55:65].lstrip().rstrip()
                    LBA = line[65:78].lstrip().rstrip()
                    line_ = ' '.join(line.split('[')[0].split()).split(' ')
                    sense = line_[0]
                    ASC = line_[1]
                    ASCQ = line_[2][:-1]
                    self.tests.append(Test_Entry(
                        format, num, test_type, status, hours, LBA,
                        segment=segment, sense=sense, ASC=ASC, ASCQ=ASCQ))
                else:
                    format = 'ata'
                    test_type = line[5:25].rstrip()
                    status = line[25:54].rstrip()
                    remain = line[54:58].lstrip().rstrip()
                    hours = line[60:68].lstrip().rstrip()
                    LBA = line[77:].rstrip()
                    self.tests.append(Test_Entry(
                        format, num, test_type, status, hours, LBA,
                        remain=remain))
            # Basic device information parsing
            if 'Model Family' in line:
                self._guess_SMART_type(line.lower())
            if 'Device Model' in line or 'Product' in line:
                self.model = line.split(':')[1].lstrip().rstrip()
                self._guess_SMART_type(line.lower())
            if 'Serial Number' in line or 'Serial number' in line:
                self.serial = line.split(':')[1].split()[0].rstrip()
            if 'LU WWN' in line:
                self._guess_SMART_type(line.lower())
            if 'Firmware Version' in line or 'Revision' in line:
                self.firmware = line.split(':')[1].lstrip().rstrip()
            if 'User Capacity' in line:
                self.capacity = (
                    line.replace(']', '[').split('[')[1].lstrip().rstrip())
            if 'Device is' in line:
                if 'In smartctl database' in line:
                    self.device_in_database=True
                if "Not in smartctl database" in line:
                    self.device_in_database=False

            if 'SMART support' in line:
                self.supports_smart = 'Enabled' in line
            if 'does not support SMART' in line:
                self.supports_smart = False
            if 'Rotation Rate' in line:
                if 'Solid State Device' in line:
                    self.is_ssd = True
                elif 'rpm' in line:
                    self.is_ssd = False
            if 'SMART overall-health self-assessment' in line:  # ATA devices
                if line.split(':')[1].strip() == 'PASSED':
                    self.assessment = 'PASS'
                else:
                    self.assessment = 'FAIL'
            if 'SMART Health Status' in line:  # SCSI devices
                if line.split(':')[1].strip() == 'OK':
                    self.assessment = 'PASS'
                else:
                    self.assessment = 'FAIL'
                    parse_ascq = True  # Set flag to capture status message
                    message = line.split(':')[1].lstrip().rstrip()
            # SMART Attribute table parsing
            if '0x0' in line and '_' in line:
                # Replace multiple space separators with a single space, then
                # tokenize the string on space delimiters
                line_ = ' '.join(line.split()).split(' ')
                if not '' in line_:
                    self.attributes[int(line_[0])] = Attribute(
                        line_[0], line_[1], line[2], line_[3], line_[4],
                        line_[5], line_[6], line_[7], line_[8], line_[9])
            if 'Description' in line and '(hours)' in line:
                parse_self_tests = True  # Set flag to capture test entries
            if 'No self-tests have been logged' in line:
                self.tests = None
            # Everything from here on is parsing SCSI information that takes
            # the place of similar ATA SMART information
            if 'used endurance' in line:
                pct = int(line.split(':')[1].strip()[:-1])
                self.diags['Life_Left'] = str(100 - pct) + '%'
            if 'Specified cycle count' in line:
                self.diags['Start_Stop_Spec'] = line.split(':')[1].strip()
                if self.diags['Start_Stop_Spec'] == '0':
                    self.diags['Start_Stop_Pct_Left'] = '-'
            if 'Accumulated start-stop cycles' in line:
                self.diags['Start_Stop_Cycles'] = line.split(':')[1].strip()
                if not 'Start_Stop_Pct_Left' in self.diags:
                    self.diags['Start_Stop_Pct_Left'] = str(int(round(
                        100 - (int(self.diags['Start_Stop_Cycles']) /
                               int(self.diags['Start_Stop_Spec'])), 0))) + '%'
            if 'Specified load-unload count' in line:
                self.diags['Load_Cycle_Spec'] = line.split(':')[1].strip()
                if self.diags['Load_Cycle_Spec'] == '0':
                    self.diags['Load_Cycle_Pct_Left'] = '-'
            if 'Accumulated load-unload cycles' in line:
                self.diags['Load_Cycle_Count'] = line.split(':')[1].strip()
                if not 'Load_Cycle_Pct_Left' in self.diags:
                    self.diags['Load_Cycle_Pct_Left'] = str(int(round(
                        100 - (int(self.diags['Load_Cycle_Count']) /
                               int(self.diags['Load_Cycle_Spec'])), 0))) + '%'
            if 'Elements in grown defect list' in line:
                self.diags['Reallocated_Sector_Ct'] = line.split(':')[1].strip()
            if 'read:' in line and smartctl_type[self.interface] == 'scsi':
                line_ = ' '.join(line.split()).split(' ')
                if (line_[1] == '0' and line_[2] == '0' and
                        line_[3] == '0' and line_[4] == '0'):
                    self.diags['Corrected_Reads'] = '0'
                elif line_[4] == '0':
                    self.diags['Corrected_Reads'] = str(
                        int(line_[1]) + int(line_[2]) + int(line_[3]))
                else:
                    self.diags['Corrected_Reads'] = line_[4]
                self.diags['Reads_GB'] = line_[6]
                self.diags['Uncorrected_Reads'] = line_[7]
            if 'write:' in line and smartctl_type[self.interface] == 'scsi':
                line_ = ' '.join(line.split()).split(' ')
                if (line_[1] == '0' and line_[2] == '0' and
                        line_[3] == '0' and line_[4] == '0'):
                    self.diags['Corrected_Writes'] = '0'
                elif line_[4] == '0':
                    self.diags['Corrected_Writes'] = str(
                        int(line_[1]) + int(line_[2]) + int(line_[3]))
                else:
                    self.diags['Corrected_Writes'] = line_[4]
                self.diags['Writes_GB'] = line_[6]
                self.diags['Uncorrected_Writes'] = line_[7]
            if 'verify:' in line and smartctl_type[self.interface] == 'scsi':
                line_ = ' '.join(line.split()).split(' ')
                if (line_[1] == '0' and line_[2] == '0' and
                        line_[3] == '0' and line_[4] == '0'):
                    self.diags['Corrected_Verifies'] = '0'
                elif line_[4] == '0':
                    self.diags['Corrected_Verifies'] = str(
                        int(line_[1]) + int(line_[2]) + int(line_[3]))
                else:
                    self.diags['Corrected_Verifies'] = line_[4]
                self.diags['Verifies_GB'] = line_[6]
                self.diags['Uncorrected_Verifies'] = line_[7]
            if 'non-medium error count' in line:
                self.diags['Non-Medium_Errors'] = line.split(':')[1].strip()
            if 'Accumulated power on time' in line:
                self.diags['Power_On_Hours'] = line.split(':')[1].split(' ')[1]

        if not smartctl_type[self.interface] == 'scsi':
            # Parse the SMART table for below-threshold attributes and create
            # corresponding warnings for non-SCSI disks
            self._make_SMART_warnings()
        else:
            # For SCSI disks, any diagnostic attribute which was not captured
            # above gets set to '-' to indicate unsupported/unavailable.
            for diag in ['Corrected_Reads', 'Corrected_Writes',
                         'Corrected_Verifies', 'Uncorrected_Reads',
                         'Uncorrected_Writes', 'Uncorrected_Verifies',
                         'Reallocated_Sector_Ct',
                         'Start_Stop_Spec', 'Start_Stop_Cycles',
                         'Load_Cycle_Spec', 'Load_Cycle_Count',
                         'Start_Stop_Pct_Left', 'Load_Cycle_Pct_Left',
                         'Power_On_Hours', 'Life_Left', 'Non-Medium_Errors',
                         'Reads_GB', 'Writes_GB', 'Verifies_GB']:
                if not diag in self.diags:
                    self.diags[diag] = '-'
            # If not obtained above, make a direct attempt to extract power on
            # hours from the background scan results log.
            if self.diags['Power_On_Hours'] == '-':
                # cmd = Popen('smartctl -d scsi -l background /dev/{1}'.format(
                #     smartctl_type[self.interface], self.name), shell=True,
                #             stdout=PIPE, stderr=PIPE)
                # _stdout, _stderr = cmd.communicate()
                cmd = 'smartctl -d scsi -l background /dev/{1}'.format(smartctl_type[self.interface], self.name)
                _stdout, _stderr = command_stdout(cmd)
                for line in _stdout.split('\n'):
                    if 'power on time' in line:
                        self.diags['Power_On_Hours'] = line.split(
                            ':')[1].split(' ')[1]


if __name__=='__main__':
    print "----------------------------"
    sda = Device('/dev/sdl')
    #sda = Device('/dev/sdh')
    print "----------------------------"
    sda
    print "-----is_ssd-----------------------"
    print sda.is_ssd
    print "------model----------------------"
    print sda.model
    print "------assessment----------------------"
    print sda.assessment
    print "------name----------------------"
    print sda.name
    print "------supports_smart----------------------"
    print sda.supports_smart
    print "------interface----------------------"
    print sda.interface
    print "------attributes----------------------"
    print sda.attributes
    print "------capacity----------------------"
    print sda.capacity
    print "------supports_smart----------------------"
    print sda.supports_smart
    print "------tests----------------------"
    print sda.tests
    print "-----all-tests----------------------"
    sda.all_selftests()
    
    print "-----all_attributes----------------------"
    sda.all_attributes() 
    #print "----------DeviceList------------------"
    #devlist = DeviceList()
    #print "----------------------------"
    #devlist
    #print "----------------------------"
    #devlist.devices[0].attributes[5]
   #print "----------------------------"
