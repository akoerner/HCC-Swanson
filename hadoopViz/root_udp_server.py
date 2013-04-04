#!/usr/bin/env python

import socket
import sys, os
import csv
import getopt
import subprocess
import time



def rootUDPServer(dir, ip, port):

    command = "python root_udp_dump.py"
    files_in_dir = os.listdir(dir)
    for file_in_dir in files_in_dir:
        if not os.path.isdir(file_in_dir):
            process = subprocess.Popen(command + " " + file_in_dir, shell=True, stdout=subprocess.PIPE)
            stdout, stderr = process.communicate()
            reader = csv.DictReader(stdout.decode('ascii').splitlines(), delimiter=' ', skipinitialspace=False, fieldnames=["F.mOpenTime", "F.mCloseTime", "F.mRTotalMB", "U.mFromHost", "U.mFromDomain", "S.mHost", "S.mDomain"])
            for row in reader:
                time.sleep(1)
                print(row)

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










 
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MESSAGE = "Hello, World!"

#setup
sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP
					  
					  
					  
					  
					  
##blast data					  
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))