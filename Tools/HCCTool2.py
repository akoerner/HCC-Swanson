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
import HCCPlot,HCCRootParser, HCCTool1
import operator
import os.path
import ROOT



def main():
    '''main options for program'''
    #command line options
    parser = OptionParser()
    parser.add_option('--file', '-f', help='ROOT input file',dest='file')
    parser.add_option('--tree', '-t', help='Tree to parse, Default Event', dest='treeName')
    parser.add_option('--sizeCutoff', '-s',dest='read_cutoff', help='Read size cutoff, Default 100')
    parser.add_option('--output_directory','-o', dest = 'output', help='The name of the output file')
    parser.add_option('--regex', '-r', dest='fileNameRegex', help='Regular expression to filter files')
    parser.add_option('--window_size', '-w', dest='window_size', help='Size of the displayed data graphic in mb Default:20')
    parser.add_option('--begin_read', '-b', dest='beginning', help='Beeginning read to display in the file graphic')
    parser.add_option('--raw_only', dest='raw_only', help='Create only the raw read graphics and not overlayed file usage', action='store_true')
    parser.add_option('--even_check', '-c', dest='check_fun_file', help='File to import that contains checkEvent method to validate any event')
    parser.add_option('--top_n','-n', dest = 'topN' , help='Color only the top N branches in the file')
    parser.add_option('--prefix','-p', dest = 'prefix' , help='Prefix to append to files to search for file on system')
    (options,  args)= parser.parse_args()


    #
    #   Handle command line options
    #
    #
    #If now file we have an error
    if options.file is None:
        print "File root file is required"
        parser.print_help()
        exit(0)
    if not options.file.upper().endswith('.ROOT'):
        print 'Root file required'
        exit()
    try:
        with open(options.file) as f: pass
    except IOError as e:
        print 'file does not exits'
        exit()
    
    #require the file name and tree
    if options.treeName is None:
        print "Using default tree of Events"
        treeName = 'Events'
    else:   
        treeName = options.treeName
    
    #output file name 
    if options.output != None:
        outDir = options.output + '/'
    else:
        outDir = './'
        
    #regular expression
    if options.fileNameRegex != None:
        frex = re.compile(options.fileNameRegex)
    else:
        frex = None
  
    #size expression
    if options.window_size != None:
        window_size = int(options.window_size)
    else:
        window_size = 20
        
    if options.read_cutoff != None:
        size_cutoff = int(options.read_cutoff)
    else:
        size_cutoff = 50
        
    if options.beginning:
        begin = int(options.beginning)
    else:
        begin = 0
        
    if options.raw_only:
        raw_only = True
    else:
        raw_only = False
     
    if options.check_fun_file:
        check_fun_file = __import__(options.check_fun_file)
    else:
        check_fun_file = None
        
    topN = None
    #color only top ten files
    if options.topN:
        
        topN = int(options.topN)
        if topN > 30:
            topN = 30
    else:
        topN = 30 

    #prefix for the file name
    prefix = '/mnt/hadoop/user/uscms01/pnfs/unl.edu/data4/cms'
    if options.prefix:
        prefix = options.prefix
        
     #
     #   End Command Line Stuff 
     #
     
     #Load the needed c++ classes into here  
    ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = 2500;")
    if os.path.exists("XrdFar"):
        ROOT.gSystem.Load("XrdFar/XrdFar")

    tf = ROOT.TFile(options.file)
    
    if not os.path.exists("XrdFar"):
        tf.MakeProject("XrdFar", "*", "new++")
        
    #Loop through all the events within the file
    for event in tf.XrdFar:
        if fileShouldBeRead(event, frex, size_cutoff, check_fun_file):
            print '\n\n'
            print 'Starting on File: %s' % event.F.mName
            #get a bunch of needed info now that it has passed
            offsets = list(event.I.mOffsetVec) 
            lengths = list(event.I.mLengthVec)
            name = event.F.mName
            uname = event.U.mServerUsername
            server = event.S.mHost
            readSize = event.F.mRTotalMB
            data = []
            idx = name.rfind('/')
            shortName = name[idx+1:]
            idx = name.rfind('/',0,idx)
            #Alsor removing /store from the front of them
            title = name[7:idx]
            file = prefix + name
            
            #trasform the data 
            for i in range(len(offsets)):
                val = transformData(offsets[i], lengths[i], i)
                data = data +  val
            arr = createArray(data)
            points = markPoints(data)
            usage, limits = fixFileUsage(arr,size = window_size, start = begin)
            try:
                print '\tCreating Usage Graph'
                HCCPlot.plotUsage(arr, name = title, outname = outDir + shortName+'_rawreads', points = points, subtitle = uname )
            except Exception, e:
                print "Error Plotting Layout: %s" % str(e)


            if not raw_only:
                t1 = time()
                print '\tParsing layout'
                fileLayout = HCCRootParser.parseFileTool2(file, treeName, None, False, topN)
                t2 = time();
                print '\t\tParse Time: ' + str(t2-t1)
                tenBig= HCCTool1.getTenBig(fileLayout, topN)
                fileLayout = HCCPlot.transformByteToMB(fileLayout)
                fileLayout = cutToRange(fileLayout, limits)
                colorMap = HCCTool1.createColorMap(fileLayout, False, tenBig)
                
                try:
                    print "\tPlotting layout overlay"
                    HCCPlot.plotFileLayoutTool2(fileLayout, False,outDir + shortName + '.png',  colorMap, tenBig,limits = limits, title = title, fileUsage = usage)
                except Exception, e:
                    print "Error Plotting Layout: %s" % str(e)
            

def fileShouldBeRead(event, frex, min_size, check_fun_file):
    '''Functions to check if the file should be read and parsed by the program'''
    its_a_go = True
    #If they have a module with desired import and stuff then run the check_event method
    if check_fun_file != None:
        its_a_go = its_a_go and check_fun_file.check_event(event)
    
    #check regex
    if frex != None:
        res = frex.search(event.F.mName)
        val = res !=  None
        its_a_go = its_a_go and val

    #check min size
    its_a_go = its_a_go and event.F.mRTotalMB > min_size
  
    #check the size
    its_a_go = its_a_go and len(list(event.I.mLengthVec)) > 0
        
    return its_a_go


def cutToRange(fileLayout, limits):
    '''Cut the file usage data array to the given range '''
    newData = []
    for p in fileLayout:
        if limits[0]/2 <= p[0] <= limits[1]/2:
            newData.append(p)
    return newData 
    

def fixFileUsage(data, size = 20, start = 0):
    '''Fix up the file usage by cutting info to a certain size and start read # within the file '''
    count = -1
    found = False
    reached = False
    idx = 0
    prevEnc = []
    #loop through until we have found enough points and reached a certain count
    while not found or not reached:
        if idx == len(data):
            print 'Index out of bounds. Will reset to 0'
            idx = 0
            prevEnc = []
            count = 0
            start = 0
            break
                
        for j in range(len(data[idx])):
            if data[idx][j] != 0:
                found = True
                if data[idx][j] not in prevEnc:
                    count += 1
                    prevEnc.append(data[idx][j])
                
                if count == start:
                    reached = True
                    break
                
        #need to insure we don't accidnetly increment the index
        if not found or not reached :
            idx = idx + 1

    #now cut the data down to size but leave whole array intact for drawing purposes
    start =idx 
    offset = size * 2
    end = start + offset
    if end > len(data):
        end = len(data)
        start = end - offset
    newData = np.zeros(( len(data), len(data[0])) ) 
    for i in range(start,end):
        for j in range(len(data[i])):
            newData[i][j] =data[i][j] 
    return [ma.masked_equal(newData,0) ,[start,end]]
    
    
            
def markPoints(data):
    '''Mark all points where a back track was made in the file read data'''
    maxEncountered = 0
    sortedData = sorted(data, key=lambda point: point[3])
    points = []
    for i in sortedData:
        if i[0] < maxEncountered:
            points.append([i[1],i[0]*2])
        maxEncountered = i[0]
            
    if len(points) < 1:
        return None
    else:
        return points 
           
def createArray(data):
    '''Create the data array out of what is there now'''
    sortedData = sorted(data, key=lambda tup: tup[0]) 
    arr = np.zeros(((sortedData[-1][0]+1)*2,pow(2,10)))
    for p in sortedData:
        arr[p[0]*2][p[1]:p[2]] = p[3]
    return arr
   
    


def transformData(offset, length, index, scale=None):
    '''transform the data that is obtained parsing the root file into the
        data that can be plotted using the two methods in this class'''
    if scale == None:
        scale = pow(2,20) 
    line = offset / scale
    loc = offset % scale 
    end = loc + length
    if end > scale:
        values = []
        values.append([line, loc/1024, scale/1024,index])
        length = length - offset
        while length > 0:
            line = line + 1
            loc = 0
            end = 0
            if(length < scale):
                end = length
            else:
                end = scale
            length = length - scale
            values.append([line,loc/1024,end/1024, index])
        return values
    else:
        return [[line,loc/1024,end/1024,index]]     

if __name__ == '__main__':
    main()
