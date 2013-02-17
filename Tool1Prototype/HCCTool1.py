#!/usr/bin/env python

# copyright 2013 UNL Holland Computing Center
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#  
#        http://www.apache.org/licenses/LICENSE-2.0
#  
#    Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import random
import re
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from optparse import OptionParser
from time import time
import HCCPlot, HCCRootParser
import operator

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
    parser.add_option('--firstN', '-N', help='Include only the first N branches on the graph', dest='maxBranch')
    parser.add_option('--display', '-d', dest='display', action='store_true' ,help='Show interactive matplotlib display')
    parser.add_option('--top_only', '-c', dest='topLevel', action='store_true' ,help='Color by only the top level branch')
    parser.add_option('--output_file','-o', dest = 'output', help='The name of the output file')
    parser.add_option('--top_n','-n', dest = 'topN' , help='Color Only the top N branches in the file')
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

    numOfBranches = None
    if options.maxBranch:
        numOfBranches = int(options.maxBranch)

    
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

    if options.topLevel:
        topLevel = True
    else:
        topLevel  = False 
    
    #color only top ten files
    topN = None
    if options.topN:
        topN = options.topTen

    if topN == None or topN > 30:
        topN = 30 

    #regular expression
    if options.branchRegex != None:
        brex = re.compile(options.branchRegex)
    else:
        brex = None

    #get data
    data = HCCRootParser.parseFile(options.file, options.treeName, brex, topLevel) 

    tenBig= getTenBig(data, topN)

    if (numOfBranches != None):
       data =  truncateData(data, numOfBranches)

    #no need to make graph if blank data
    if len(data) == 0:
        print 'No Branches in that tree'
        exit(0)

    data = HCCPlot.transformByteToMB(data)

    #plot
    if brex != None:
        colorMap = {} 
        HCCPlot.plotFileLayout(data, display, outName, colorMap, tenBig)
    else:   
        colorMap = createColorMap(data, False, tenBig)
        HCCPlot.plotFileLayout(data, display, outName, colorMap, tenBig)


def getTenBig(data, num):
    dict = {}
    for i in data:
        name = i[3]
        size = i[1]
        if name in dict:
            dict[name] = dict[name] + size
        else:
            dict[name] = size
    sortedDict = sorted(dict.iteritems(), key=operator.itemgetter(1))
    ans = sortedDict[-num:]
    ans = [i[0] for i in ans]
    return ans


def truncateData(data, num):
    sortedData = sorted(data, key=lambda tup: tup[0])
    sortedData = sortedData[:num]
    sortedData = sorted(sortedData, key=lambda tup: tup[3])
    return sortedData


def createColorMap(data, colorByBranchName, branchNames):
    if branchNames != None:
        size = len(branchNames)
    else:
        size = len(data)
    cm = get_cmap('gist_ncar')

    #create colors
    colors = []
    for i in range(size):
        color = cm(1. * i/size)
        colors.append(color)
    colorMap = {}
    colorIdx = 0

    if branchNames != None:
        for point in data:
            if point[3] in branchNames:
                if point[3] not in colorMap: 
                    colorMap[point[3]] = colors[colorIdx % len(colors)]
                    colorIdx = colorIdx + 1
    else:
        for point in data:
            if point[3] not in colorMap: 
                colorMap[point[3]] = colors[colorIdx % len(colors)]
                colorIdx = colorIdx + 1
    return colorMap
                

if __name__ == '__main__':
    main()
