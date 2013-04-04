#!/usr/bin/env python

import socket
import sys, os
import csv
import getopt
import subprocess
import time



def rootUDPServer(dir, ip, port):

    UDP_IP = ip
    UDP_PORT = int(port)
    
    sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP
    command = "python root_udp_dump.py"
    files_in_dir = os.listdir(dir)
    for file_in_dir in files_in_dir:
        if not os.path.isdir(file_in_dir):
            process = subprocess.Popen(command + " " + file_in_dir, shell=True, stdout=subprocess.PIPE)
            stdout, stderr = process.communicate()
            reader = csv.DictReader(stdout.decode('ascii').splitlines(), delimiter=' ', skipinitialspace=False, fieldnames=["F.mOpenTime", "F.mCloseTime", "F.mRTotalMB", "U.mFromHost", "U.mFromDomain", "S.mHost", "S.mDomain"])
            for row in stdout.decode('ascii').splitlines():
                time.sleep(1)
                sock.sendto(row, (UDP_IP, UDP_PORT))

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
            if(len(args) > 0):
                if(len(args)>1):
                    return rootUDPServer(args[0], args[1], args[2])
        except getopt.error, msg:
             raise Usage(msg)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())










 
