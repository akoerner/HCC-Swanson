#!/usr/bin/env python
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from optparse import OptionParser
import HCCPlot, HCCRootParser

def getName(file):
    idx = file.rfind('.')
    return file[:idx] + '.png'

def main():
    #command line options
    parser = OptionParser()
    parser.add_option('--file', '-f', help='ROOT file to graph',dest='file')
    parser.add_option('--tree', '-t', help='Tree to parse', dest='treeName')
    parser.add_option('--display', '-d', dest='display', action='store_true' ,help='Show interactive matplotlib display')
    parser.add_option('--output_file','-o', dest = 'output', help='The name of the output file')
    parser.add_option('--list_trees', '-l', dest='list', action='store_true', help='List the available trees in file')
    (options,  args)= parser.parse_args()

    #require the file name and tree
    if options.file is None or options.treeName is None:
        print "File Name or Tree Name is missing"
        parser.print_help()
        exit(-1)

    #if list just list trees and exit
    if(options.list):
        HCCRootParser.listFileTrees(options.file)
        exit(0)
    
    #output file name 
    if options.output != None:
        outName = options.output
    else:
        outName = getName(options.file)
    #interactive display
    if options.display:
        display = True
    else:
        display = False
     
    #get data
    data = HCCRootParser.parseFile(options.file, options.treeName) 

    #no need to make graph if blank data
    if len(data) == 0:
        print 'No Branches in that tree'
        exit(0)

    data = HCCPlot.transformByteToMB(data)
    print len(data)
    #plot
    HCCPlot.plotFileLayout(data, display, outName)

if __name__ == '__main__':
    main()


