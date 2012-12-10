#!/usr/bin/env python
import random
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from optparse import OptionParser
from time import time
import HCCPlot, HCCRootParser

def getName(file):
    '''Get the default name for the output file in all cases it will be
        the name of the passed root file with .png appeneded to it'''
    idx = file.rfind('.')
    return file[:idx] + '.png'

def main():
    '''main options for program'''
    #command line options
    parser = OptionParser()
    parser.add_option('--file', '-f', help='ROOT file to graph',dest='file')
    parser.add_option('--tree', '-t', help='Tree to parse', dest='treeName')
    parser.add_option('--display', '-d', dest='display', action='store_true' ,help='Show interactive matplotlib display')
    parser.add_option('--output_file','-o', dest = 'output', help='The name of the output file')
    parser.add_option('--list_trees', '-l', dest='list', action='store_true', help='List the available trees in file')
    parser.add_option('--branch_regex', '-r', dest='branchRegex', help='Regular expression to filter out branches')
    (options,  args)= parser.parse_args()


    #If now file we have an error
    if options.file is None:
        print "File root file is required"
        parser.print_help()
        exit(0)

    #if list just list trees and exit
    if(options.list):
        HCCRootParser.listFileTrees(options.file)
        exit(0)

    #require the file name and tree
    if options.treeName is None:
        print "Tree Name is required"
        parser.print_help()
        exit(-1)

    
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

    #regular expression
    if options.branchRegex != None:
        brex = re.compile(options.branchRegex)
    else:
        brex = None
    print brex
    #get data
    firstS = time()
    s = time()
    data = HCCRootParser.parseFile(options.file, options.treeName, brex) 
    e = time()
    print "Parse time %d"%(e-s)
    #no need to make graph if blank data
    if len(data) == 0:
        print 'No Branches in that tree'
        exit(0)

    s = time()
    data = HCCPlot.transformByteToMB(data)
    e = time()
    print "Transform time %d"%(e-s)
    print "Baskets found %d"%len(data)
    #plot
    if brex != None:
        HCCPlot.plotFileLayoutOneColor(data, display, outName)
    else:   
        HCCPlot.plotFileLayout(data, display, outName)
    fEnd = time()
    print "Total time %d"%(fEnd-firstS)

if __name__ == '__main__':
    main()


