#!/usr/bin/python

import os
import re
import sys
import sets
import time
import socket
import struct
import logging
import optparse
import cStringIO
import threading
import traceback
import logging.handlers

import gratia.common.Gratia as Gratia
from gratia.common.Gratia import DebugPrint

log = None
timestamp = time.time()
SLEEP_TIME = 1*60
XRD_NAME = 'Xrootd'
XRD_WAIT_TIME = 10 # Seconds to wait after closing the file before sending a
                   # record.
XRD_EXPIRE_TIME = 3600 # Records are assumed to have lost the "close" packet if
                       # no activity has happened in this amount of time.
XRD_AUTH_EXPIRE_TIME = 4*3600 # Time for authentication session to expire


# Author: Chad J. Schroeder
# Copyright: Copyright (C) 2005 Chad J. Schroeder
# This script is one I've found to be very reliable for creating daemons.
# The license is permissible for redistribution.
# I've modified it slightly for my purposes.  -BB
UMASK = 0
WORKDIR = "/"

if (hasattr(os, "devnull")):
   REDIRECT_TO = os.devnull
else:
   REDIRECT_TO = "/dev/null"

def daemonize(pidfile):
   """Detach a process from the controlling terminal and run it in the
   background as a daemon.

   The detached process will return; the process controlling the terminal
   will exit.

   If the fork is unsuccessful, it will raise an exception; DO NOT CAPTURE IT.

   """

   try:
      pid = os.fork()
   except OSError, e:
      raise Exception("%s [%d]" % (e.strerror, e.errno))

   if (pid == 0):	# The first child.
      os.setsid()
      try:
         pid = os.fork()	# Fork a second child.
      except OSError, e:
         raise Exception("%s [%d]" % (e.strerror, e.errno))

      if (pid == 0):	# The second child.
         os.chdir(WORKDIR)
         os.umask(UMASK)
         for i in range(3):
             os.close(i)
         os.open(REDIRECT_TO, os.O_RDWR|os.O_CREAT) # standard input (0)
         os.dup2(0, 1)                        # standard output (1)
         os.dup2(0, 2)                        # standard error (2)
         try:
             fp = open(pidfile, 'w')
             fp.write(str(os.getpid()))
             fp.close()
         except:
             pass
      else:
         os._exit(0)	# Exit parent (the first child) of the second child.
   else:
      os._exit(0)	# Exit parent of the first child.

def gratia_log_traceback(lvl=0):
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    tb = traceback.format_exception(exceptionType, exceptionValue,
        exceptionTraceback)
    tb_str = ''.join(tb)
    if DebugPrint: # Make sure this has been initialized
        DebugPrint(lvl, "Encountered exception:\n%s" % tb_str)

def print_handler(obj, addr):
    DebugPrint(-1, '%s (from %s)' % (str(obj), '%s:%i' % addr))

def udp_server(data_handler, port=3334, bind="0.0.0.0"):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((bind, port))
    buf = 64*1024
    while 1:
        data, addr = server_socket.recvfrom(buf)
        try:
            data_handler.handle(data, addr)
        except:
            gratia_log_traceback()

def test_udp_socket(port=3334, bind="0.0.0.0"):
    """
    Test the UDP socket to see if we can bind to it.
    Will throw a "Address already in use" exception if it's not usable.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((bind, port))
    server_socket.close()

def file_handler(data_handler, input_file):
    raise NotImplementedError("Sorry, file handlers have not been implemented.")

class XrdMonInfo(object):

    """
    Monitoring information from Xrootd.  An object-oriented
    representation of the UDP packet described here:
    http://xrootd.slac.stanford.edu/doc/prod/xrd_monitoring.htm
    """

    def __init__(self, uniq_id):
        self.uniq_id = str(uniq_id)

    def __str__(self):
        return "XrdMonInfo %s" % self.uniq_id

    def __del__(self):
        DebugPrint(5, "Deleting XrdMonInfo object: %s" % self)

class XrdMonMapInfo(XrdMonInfo):

    def __init__(self, uniq_id):
        super(XrdMonMapInfo, self).__init__(uniq_id)

    def __str__(self):
        return "XrdMonMapInfo %s" % self.uniq_id

class XrdMonMapLoginInfo(XrdMonMapInfo):

    def __init__(self, uniq_id, user):
        super(XrdMonMapLoginInfo, self).__init__(uniq_id)
        self.user = user

    def __str__(self):
        return "XrdMonMapLoginInfo %s: %s" % (self.uniq_id, self.user)

class XrdMonMapAuthInfo(XrdMonMapInfo):

    def __init__(self, uniq_id, user, prot=None, name=None, hostname=None,
            org=None, role=None, **kw):
        super(XrdMonMapAuthInfo, self).__init__(uniq_id)
        self.prot = prot
        self.dn = name
        self.hostname = hostname
        self.org = org
        self.role = role
        self.user = user

    def __str__(self):
        s = "XrdMonMapAuthInfo %s: %s;" % (self.uniq_id, self.user)
        if prot:
            s += " " + self.prot
        if name:
            s += " " + self.dn
        if hostname:
            s += " " + self.hostname
        if org:
            s += " " + self.org
        if role:
            s += " " + self.role
        print s
        return s

class XrdMonMapStageInfo(XrdMonMapInfo):

    def __init__(self, uniq_id, user, stg_info=None):
        super(XrdMonMapStageInfo, self).__init__(uniq_id)
        self.user = user
        self.stg_info = stg_info

    def __str__(self):
        return "XrdMonMapStageInfo %s: user=%s, stage info=%s" % (self.uniq_id,
            self.user, self.stg_info)

class XrdMonMapSessionInfo(XrdMonMapInfo):

    def __init__(self, uniq_id, user, app_info=None):
        super(XrdMonMapSessionInfo, self).__init__(uniq_id)
        self.user = user
        self.app_info = app_info

    def __str__(self):
        return "XrdMonMapSessionInfo %s: user=%s, app info=%s" % (self.uniq_id,
            self.user, self.app_info)

class XrdMonMapOpenInfo(XrdMonMapInfo):

    def __init__(self, uniq_id, user, path=None):
        super(XrdMonMapOpenInfo, self).__init__(uniq_id)
        self.user = user
        self.path = path

    def __str__(self):
        return "XrdMonMapOpenInfo %s: user=%s, path=%s" % (self.uniq_id,
            self.user, self.path)

class XrdMonWindowInfo(object):

    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def __str__(self):
        return "XrdMonWindowInfo from %i to %i (len %i)" % (self.start,
            self.stop, self.stop-self.start) 

class XrdMonAppidInfo(XrdMonInfo):

    def __init__(self, uniq_id, info):
        super(XrdMonAppidInfo, self).__init__(uniq_id)
        self.info = info

    def __str__(self):
        return "XrdMonAppidInfo %s: %s" % (self.uniq_id, self.info)

class XrdMonCloseInfo(XrdMonInfo):

    def __init__(self, uniq_id, read, write):
        super(XrdMonCloseInfo, self).__init__(uniq_id)
        self.read = read
        self.write = write

    def __str__(self):
        return "XrdMonCloseInfo %s: read=%i, write=%i" % (self.uniq_id,
            self.read, self.write)

class XrdMonDiscInfo(XrdMonInfo):

    def __init__(self, uniq_id, length):
        super(XrdMonDiscInfo, self).__init__(uniq_id)
        self.length = length

    def __str__(self):
        return "XrdMonDiscInfo %s: connection time %i" % (self.uniq_id,
            self.length)

class XrdMonOpenInfo(XrdMonInfo):

    def __init__(self, uniq_id, size):
        super(XrdMonOpenInfo, self).__init__(uniq_id)
        self.size = size

    def __str__(self):
        return "XrdMonOpenInfo %s: file size %i" % (self.uniq_id,
            self.size)

class XrdMonReadInfo(XrdMonInfo):

    def __init__(self, uniq_id, offset, len):
        super(XrdMonReadInfo, self).__init__(uniq_id)
        self.offset = offset
        self.len = len

    def __str__(self):
        return "XrdMonReadInfo %s: offset %i, len %i" % (self.uniq_id,
            self.offset, self.len)

class XrdMonWriteInfo(XrdMonInfo):

    def __init__(self, uniq_id, offset, len):
        super(XrdMonWriteInfo, self).__init__(uniq_id)
        self.offset = offset
        self.len = len

    def __str__(self):
        return "XrdMonWriteInfo %s: offset %i, len %i" % (self.uniq_id,
            self.offset, self.len)

MonMapCodes = ('d', 'i', 's', 'u', 'v')
XROOTD_MON_OPEN = 0x80
XROOTD_MON_APPID = 0xa0
XROOTD_MON_CLOSE = 0xc0
XROOTD_MON_DISC = 0xd0
XROOTD_MON_WINDOW = 0xe0

# Verify that we have the integer/long/short lengths we desire.
assert struct.calcsize("!i") == 4
assert struct.calcsize("!q") == 8
class XrdMonHandler(object):

    """
    Handler for the XrdMon UDP packet format as documented here:
    http://xrootd.slac.stanford.edu/doc/prod/xrd_monitoring.htm
    """

    def __init__(self, callback):
        self.callback = callback

    def handle(self, data, addr):
        header, rest = data[:8], data[8:]
        # Parse header:
        code, pseq, plen, stod = struct.unpack("!cchi", header)
        result = None
        # XrdXrootdMonMap
        if code in MonMapCodes:
            info_len = plen-8-4
            dictid, info = struct.unpack("!i%is" % info_len, rest)
            uniq_id = "%i.%i" % (stod, dictid)
            if code == 'u':
                result = XrdMonMapLoginInfo(uniq_id, info)
            elif code == 'v':
                info = info.splitlines()
                if len(info) > 1:
                    kw = dict([i.split("=", 1) for i in info[1].split("&")])
                    result = XrdMonMapAuthInfo(uniq_id, info[0], **kw)
                else:
                    result = XrdMonMapAuthInfo(uniq_id, info[0])
            elif code == "s":
                # Yes, the next 3 entries are all the same... keeping them sep.
                # if I decide to implement more detailed parsing.
                info = info.splitlines()
                if len(info) > 1:
                    result = XrdMonStageInfo(uniq_id, info[0], info[1])
                else:
                    result = XrdMonStageInfo(uniq_id, info[0], None)
            elif code == "d":
                info = info.splitlines()
                if len(info) > 1:
                    result = XrdMonMapOpenInfo(uniq_id, info[0], info[1])
                else:
                    result = XrdMonMapOpenInfo(uniq_id, info[0], None)
            elif code == "i":
                info = info.splitlines()
                if len(info) > 1:
                    result = XrdMonSessionInfo(uniq_id, info[0], info[1])
                else:
                    result = XrdMonSessionInfo(uniq_id, info[0], None)
        elif code == 't':
            msg, rest = rest[:16], rest[16:]
            while msg:
                id0, = struct.unpack("!B", msg[0])
                if id0 == XROOTD_MON_OPEN:
                    new_msg = '\x00' + msg[1:]
                    size, dictid = struct.unpack("!QxxxxI", new_msg)
                    uniq_id = "%i.%i" % (stod, dictid)
                    result = XrdMonOpenInfo(uniq_id, size)
                elif id0 == XROOTD_MON_APPID:
                    appid = struct.unpack("!12s", msg[4:])
                    result = XrdMonAppidInfo(str(stod), appid)
                elif id0 == XROOTD_MON_CLOSE:
                    rshift, wshift, rTot, wTot, dictid = struct.unpack( \
                        "!BBxIII", msg[1:])
                    rTot = rTot << rshift
                    wTot = wTot << wshift
                    uniq_id = "%i.%i" % (stod, dictid)
                    result = XrdMonCloseInfo(uniq_id, rTot, wTot)
                elif id0 == XROOTD_MON_DISC:
                    conn_time, dictid = struct.unpack("!iI", msg[8:])
                    uniq_id = "%i.%i" % (stod, dictid)
                    result = XrdMonDiscInfo(uniq_id, conn_time)
                elif id0 == XROOTD_MON_WINDOW:
                    start, end = struct.unpack("!ii", msg[8:])
                    result = XrdMonWindowInfo(start, end)
                else: # Read or write request.
                    offset, mylen, dictid = struct.unpack("!qiI", msg[:16])
                    uniq_id = "%i.%i" % (stod, dictid)
                    if mylen >= 0:
                        result = XrdMonReadInfo(uniq_id, offset, mylen)
                    else:
                        result = XrdMonWriteInfo(uniq_id, offset, mylen)
                try:
                    self.callback(result, addr)
                except:
                    gratia_log_traceback(lvl=1)
                result = None
                msg, rest = rest[:16], rest[16:]
        else:
            raise Exception("Unknown message code: %s" % code)
        if result:
            self.callback(result, addr)

def get_se():
    config_se = Gratia.Config.getConfigAttribute("SiteName")
    if not config_se:
        raise Exception("SiteName attribute not found in ProbeConfig")
    return config_se

def get_rpm_version():
    cmd = "rpm -q gratia-probe-xrootd-transfer --queryformat '%{VERSION}-%{RELEASE}'"
    fd = os.popen(cmd)
    output = fd.read()
    if fd.close():
        raise Exception("Unable to successfully query rpm for %s "
            "version information." % XRD_NAME)
    return output

version_cache = None
def get_version():
    global version_cache
    if version_cache != None:
        return version_cache
    config_version = Gratia.Config.getConfigAttribute("%sVersion" % XRD_NAME)
    if not config_version:
        config_version = get_rpm_version()
        #raise Exception("XrootdVersion attribute not found in ProbeConfig")
    version_cache = config_version
    return version_cache


class XrdFileEvent(object):
    """
    An Xrootd Event is defined to be the collection of all xrootd monitoring
    messages recieved for a unique user session / file descriptor.
    """

    def __init__(self, uniq_id, start_timestamp):
        self.uniq_id = uniq_id
        self.start_window = start_timestamp
        self.last_window = start_timestamp
        self.closed = False
        self.messages = []
        self.io_count = 0
        self.read_bytes = 0
        self.write_bytes = 0
        self.open_size = 0
        self.user = None
        self.auth = None
        self.path = None
        self.addr = None

    def handle(self, msg, addr):
        self.addr = addr
        self.messages.append(msg)
        if isinstance(msg, XrdMonReadInfo):
            self.read_bytes += msg.len
            self.io_count += 1
        elif isinstance(msg, XrdMonWriteInfo):
            self.write_bytes += msg.len
            self.io_count += 1
        elif isinstance(msg, XrdMonWindowInfo):
            self.last_window = msg.stop
        elif isinstance(msg, XrdMonOpenInfo):
            self.open_size = msg.size
        elif isinstance(msg, XrdMonCloseInfo):
            if self.read_bytes <= msg.read:
                self.read_bytes = msg.read
            if self.write_bytes <= msg.write:
                self.write_bytes = msg.write
            self.closed = True
        elif isinstance(msg, XrdMonMapAuthInfo):
            self.auth = msg
        elif isinstance(msg, XrdMonMapLoginInfo):
            self.user = msg.user
        elif isinstance(msg, XrdMonMapOpenInfo):
            self.user = msg.user
            self.path = msg.path

    def last_timestamp(self):
        return self.last_window

    def is_closed(self):
        return self.closed

def isAuthInfo(evt):
   return isinstance(evt, XrdMonMapLoginInfo) or \
       isinstance(evt, XrdMonMapAuthInfo)

class GratiaHandler(object):

    def __init__(self):
        self.cur_host = None
        self.stop = False
        self.stop_exception = None
        self.lock = threading.Lock()
        self.events = {}
        self.last_window = int(time.time())
        self.prev_events = []
        self.auth_info = {}
        self.handle = self.make_sync(self.handle)
        self.summary = self.make_sync(self.summary)
        self.exit_summary = self.make_sync(self.exit_summary)

    def make_sync(self, fcn):
        def lock_fcn(*args, **kw):
             self.lock.acquire()
             try:
                 return fcn(*args, **kw)
             finally:
                 self.lock.release()
        return lock_fcn

    def handle(self, xrdMon, addr):
        DebugPrint(4, "GratiaHandler processed message: %s" %  xrdMon)
        if self.stop:
            raise self.stop_exception
        if isAuthInfo(xrdMon):
            self.auth_info[xrdMon.user] = [xrdMon, time.time()]
        if isinstance(xrdMon, XrdMonWindowInfo):
            for evt in self.prev_events:
                evt.handle(xrdMon, addr)
            self.prev_events = []
            self.last_window = xrdMon.stop
            return
        if not isinstance(xrdMon, XrdMonInfo):
            return
        if not isAuthInfo(xrdMon):
            uniq_id = xrdMon.uniq_id
            evt = self.events.get(uniq_id, None)
            if not evt and not isinstance(xrdMon, XrdMonDiscInfo):
                evt = XrdFileEvent(uniq_id, self.last_window)
                self.events[uniq_id] = evt
                DebugPrint(4, "Creating new event object; global count is %i." \
                    % len(self.events))
            # We just ignore disconnect messages that we haven't recorded the
            # corresponding connect message for.
            if not evt:
                return
            self.prev_events.append(evt)
            evt.handle(xrdMon, addr)
            if isinstance(xrdMon, XrdMonMapOpenInfo) and (xrdMon.user in \
                    self.auth_info):
                evt.handle(self.auth_info[xrdMon.user][0], addr)
                self.auth_info[xrdMon.user][1] = time.time()

    def send_gratia_record(self, evt):

        # We sometimes get idle records ... ignore these
        if evt.read_bytes+evt.write_bytes == 0:
            return

        user = evt.user
        hostname = None
        if user:
            info = user.split("@")
            if len(info) > 1:
                hostname = info[-1]
            user = info[0].split(".")[0]

        my_addr = evt.addr[0]
        try:
            if my_addr:
                my_addr = socket.getfqdn(my_addr)
        except:
            my_addr = None

        try:
            if hostname:
                hostname = socket.getfqdn(hostname)
        except:
            pass

        if not hostname:
            hostname = "UNKNOWN"
        if not my_addr:
            my_addr = "UNKNOWN"

        isNew = True
        srcHost = hostname
        dstHost = my_addr
        if evt.open_size > 0 or evt.write_bytes == 0:
            isNew = False
            srcHost = my_addr
            dstHost = hostname

        r = Gratia.UsageRecord("Storage")
        r.AdditionalInfo("Source", srcHost)
        r.AdditionalInfo("Destination", dstHost)
        r.AdditionalInfo("Protocol", "xrootd")
        r.AdditionalInfo("IsNew", isNew)
        r.AdditionalInfo("File", evt.path)
        r.LocalJobId(evt.uniq_id)
        r.Grid("Local")
        r.StartTime(evt.start_window)
        duration = evt.last_window - evt.start_window
        r.Network(evt.read_bytes+evt.write_bytes, 'b', duration, "transfer")
        r.WallDuration(duration)
        if user:
            r.LocalUserId(user)
        if hostname:
            r.SubmitHost(hostname)
        r.Status(0)
        if evt.auth and evt.auth.dn:
            r.DN(evt.auth.dn)
        elif user:
            r.DN("/OU=UnixUser/CN=%s" % user)
        Gratia.Send(r)

    def summary(self):
        # Update our global timestamp so we don't have to do this in all the
        # Gratia send functions.
        global timestamp
        timestamp = time.time()

        to_delete = []
        start_events = len(self.events)
        DebugPrint(2, "Number of events at the start of the summary call: %i" %\
            start_events)
        for id, evt in self.events.items():
            if evt.is_closed() and timestamp - evt.last_window > XRD_WAIT_TIME \
                    or timestamp - evt.last_timestamp() > XRD_EXPIRE_TIME:
                self.send_gratia_record(evt)
                to_delete.append(id)
        for id in to_delete:
            del self.events[id]
        end_events = len(self.events)
        DebugPrint(2, "Number of events at the end of the summary call: %i" % \
            end_events)

        to_delete = []
        DebugPrint(2, "Number of auth items prior to pruning: %i" % \
            len(self.auth_info))
        for id, tmp in self.auth_info.items():
            auth_info, last_used = tmp
            if timestamp - last_used > XRD_AUTH_EXPIRE_TIME:
                to_delete.append(id)
        for id in to_delete:
            del self.auth_info[id]
        DebugPrint(2, "Number of auth item after pruning: %i" % \
            len(self.auth_info))

    def exit_summary(self):
        global timestamp
        timestamp = time.time()
       
        DebugPrint(2, "Sending %i records prior to exit." % len(self.events)) 
        for evt in self.events.values():
            self.send_gratia_record(evt)

def parse_opts():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--daemon", help="Run as daemon; automatically " \
        "background the process.", default=False, action="store_true",
        dest="daemon")
    parser.add_option("-l", "--logfile", help="Log file location.  Defaults " \
        "to the Gratia logging infrastructure.", dest="logfile")
    parser.add_option("-i", "--input", help="Input file name; if this option" \
        " is given, the process does not listen for UDP messages", dest="input")
    parser.add_option("-p", "--port", help="UDP Port to listen on for " \
        "messages.  Overridden by Gratia ProbeConfig.", type="int",
        default=3334, dest="port")
    parser.add_option("--gratia_config", help="Location of the Gratia config;" \
        " defaults to /etc/gratia/xrootd-transfer/ProbeConfig",
        dest="gratia_config")
    parser.add_option("-b", "--bind", help="Listen for messages on a " \
        "specific address; defaults to 0.0.0.0.  Overridden by Gratia " \
        "ProbeConfig", default="0.0.0.0", dest="bind")
    parser.add_option("-v", "--verbose", help="Enable verbose logging to " \
        "stdout.", default=False, action="store_true", dest="verbose")
    parser.add_option("--print_only", help="Only print data recieved; do not" \
        " send to Gratia.", dest="print_only", action="store_true")
    parser.add_option("-r", "--report_period", help="Time in minutes between" \
        " reports to Gratia.", dest="report_period", type="int")

    opts, args = parser.parse_args()

    # Expand our input paths:
    if opts.input:
        opts.input = os.path.expanduser(opts.input)
    if opts.logfile:
        opts.logfile = os.path.expanduser(opts.logfile)
    if opts.gratia_config:
        opts.gratia_config = os.path.expanduser(opts.gratia_config)

    # Adjust sleep time as necessary
    if opts.report_period:
        global SLEEP_TIME
        SLEEP_TIME = opts.report_period*60

    # Initialize logging
    logfile = "/var/log/gratia/xrootd-transfer.log"
    if opts.logfile:
        logfile = opts.logfile
    path, _ = os.path.split(logfile)
    if path and not os.path.exists(path):
        os.makedirs(path)
    try:
        fp = open(logfile, 'w')
    except Exception, e:
        raise Exception("Could not open %s-Storage logfile, %s, for " \
            "write.  Error: %s." % (XRD_NAME, logfile, str(e)))
    global log
    log = logging.getLogger("XrdStorage")
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=20*1024*1024, backupCount=5)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    if opts.verbose:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        log.addHandler(handler)

    # Initialize Gratia
    gratia_config = None
    if opts.gratia_config and os.path.exists(opts.gratia_config):
        gratia_config = opts.gratia_config
    else:
        tmp = "/etc/gratia/xrootd-transfer/ProbeConfig"
        if os.path.exists(tmp):
            gratia_config = tmp
    if not gratia_config:
        raise Exception("Unable to find a suitable ProbeConfig to use!")
    Gratia.Initialize(gratia_config)

    if opts.verbose:
        Gratia.Config.__DebugLevel = 5

    return opts

def main():
    opts = parse_opts()

    if opts.print_only:
        my_handler = print_handler
    else:
        gratia_handler = GratiaHandler()
        my_handler = gratia_handler.handle

    # Do all the daemon-specific tests.
    if not opts.input:
        if opts.daemon:
            # Test the socket first before we daemonize and lose the ability
            # to alert the user of potential errors.
            test_udp_socket(port=opts.port, bind=opts.bind)
            # Test to see if the pidfile is writable.
            pidfile = "/var/run/xrd_transfer_probe.pid"
            open(pidfile, 'w').close()
            daemonize(pidfile)
            # Must re-initialize here because we changed processes and lost
            # the previous thread
            if not opts.print_only:
                gratia_handler = GratiaHandler()
                my_handler = gratia_handler.handle


    se = get_se()
    version = get_version()
    DebugPrint(1, "Running %s version %s for SE %s." % (XRD_NAME, version, se))

    handler = XrdMonHandler(my_handler)
    if not opts.input:
        try:
        udpserverthread = threading.Thread(target=udp_server,args=(handler, opts.port, opts.bind))
        udpserverthread.setDaemon(True)
        udpserverthread.setName("Gratia udp_server Thread")
        udpserverthread.start()
        finally:
            if not opts.print_only:
                gratia_handler.exit_summary()
    else:
        input = opts.input
        try:
            fp = open(input, 'r')
        except Exception, e:
            raise Exception("Could not open input file, %s, for read due to " \
                "exception %s." % (input, str(e)))
        try:
            file_handler(my_handler, opts.input)
        finally:
            if not opts.print_only:
                gratia_handler.exit_summary()
    try:
        while 1 == 1:
        try:
            DebugPrint(0, "Will send new Gratia data in %i seconds." % SLEEP_TIME)
            time.sleep(SLEEP_TIME)
        except KeyboardInterrupt, SystemExit:
            raise
        except Exception, e:
            gratia_log_traceback(lvl=1)
        try:
            DebugPrint(1, "Creating a new Xrootd Gratia report.")
            gratia_handler.summary()
        except KeyboardInterrupt, SystemExit:
            raise
        except Exception, e:
            gratia_log_traceback(lvl=1)
    finally:
        if not opts.print_only:
            gratia_handler.exit_summary()

if __name__ == '__main__':
    try:
        main()
    except:
        gratia_log_traceback()
        raise
