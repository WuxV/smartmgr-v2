# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import struct

MAX_LEN = 2**(8*len(struct.pack('I', 0)))

MS_ERROR    = -1
MS_FINISH   = 0
MS_CONTINUE = 100

CONFIG_PATH = None
