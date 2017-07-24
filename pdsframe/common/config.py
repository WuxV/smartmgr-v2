# -*- coding: utf-8 -*
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import re
import sys
import ConfigParser

class ExtendedConfigParser(ConfigParser.ConfigParser):
    def safe_get(self, section, option, default=None):
        try:
            value = str(self._safe_get(section, option, default))
            value_split_reg = ur"(@{\S+?})"
            value_reg = ur"@{([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)}"
            value_out = ""
            for v in re.split(value_split_reg, value):
                value_grp = re.search(value_reg, v)
                if value_grp == None:
                    value_out += v
                else:
                    value_out += self.safe_get(value_grp.group(1), value_grp.group(2))
            return value_out
        except Exception as e:
            print "Parse config '%s.%s' failed: %s" % (section, option, str(e))
            sys.exit(1)

    def _safe_get(self, section, option, default=None):
        try:
            return self.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            if default is None:
                raise
            else:
                return default

    def safe_get_int(self, section, option, default=None):
        try:
            return int(self.safe_get(section, option, default))
        except Exception as e:
            print "Parse config '%s.%s' failed: %s" % (section, option, str(e))
            sys.exit(1)

    def safe_set(self, section, key_option, value_option, default=None):
        try:
            return self.set(section, key_option, value_option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            if default is None:
                raise
            else:
                return default
def init_config(filename):
    try:
        config.read([filename])
    except ConfigParser.ParsingError, e:
        print "Parse config failed:%s" % str(e)
        sys.exit(1)


config = ExtendedConfigParser()
