#!/usr/bin/env python
import os
import ROOT

prefix = '/mnt/hadoop/user/uscms01/pnfs/unl.edu/data4/cms'

def main():
    fileName = '/home/bockelman/ataylor/xmxxx-2013-03-05-0.root'
    ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = 2500;")
    if os.path.exists("XrdFar"):
        ROOT.gSystem.Load("XrdFar/XrdFar")

    tf = ROOT.TFile(fileName)

    if not os.path.exists("XrdFar"):
        tf.MakeProject("XrdFar", "*", "new++")

    for event in tf.XrdFar:
        print event.F.mName,
        print event.F.mOpenTime,
        print event.F.mCloseTime,
        print event.F.mRTotalMB,
        print event.U.mFromHost,
        print event.U.mFromDomain,
        print event.S.mHost,
        print event.S.mDomain
     

                
            
def markPoints(data):
    maxEncountered = 0
    sortedData = sorted(data, key=lambda point: point[3])
    points = []
    for i in sortedData:
        if i[0] < maxEncountered:
            points.append([i[0]*2,i[1]])
        else:
            print maxEncountered
            maxEncountered = i[0]
            
    if len(points) < 1:
        return None
    else:
        return points 
           
def createArray(data):
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
