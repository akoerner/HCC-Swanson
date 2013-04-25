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

from ROOT import *

#Recursivly get the sub branches
def getSubBranches(branches, branchRegex=None):
    '''This subroutine will recursivly gather all of the branches that are
        children of the list of branches passed into it.  Also optional
        is the ability to filter the branches by a python regular expression'''
    if len(branches) == 0:
        return []
    else:
        vals =  []
        if branchRegex != None:
            branches = [branch for branch in branches if branchRegex.match(branch.GetName())]
        for b in branches:
            vals.append(b)
            subBranches = b.GetListOfBranches()
            retVal = getSubBranches(subBranches, branchRegex)
            for i in retVal:
                vals.append(i)
        return vals




def parseFile(fName, tName, branchRegex=None, byMother=False):
    '''Parse the passed in file for all of buckets contained in the given tree
        Also available is the filtering of the branches by a regular expression'''
    gROOT.ProcessLine("gErrorIgnoreLevel = 2500;")
    rootfile = TFile.Open(fName)
    tree = rootfile.Get(tName)
    #get branches
    branches = tree.GetListOfBranches() 
    a = getSubBranches(branches, branchRegex)
    buckets = []
    #gather layout information
    for i in a:
        idx = 0
        basket = i.GetBasket(idx)
        while basket != None:
            start = basket.GetSeekKey()
            length = basket.GetNbytes()
            end = start + length-1
            if byMother:
                t = (start, length, end, i.GetMother().GetName(), basket.GetNevBuf())
            else:
                t = (start, length, end, i.GetName(), basket.GetNevBuf())
            buckets.append(t)
            idx = idx + 1
            basket = i.GetBasket(idx)
    sortBucket = sorted(buckets, key=lambda tup: tup[3])
    return sortBucket



def parseFileTool2(fName, tName, branchRegex=None, byMother=False, topN = 30, filterByTop = False):
    '''Parse the passed in file for all of buckets contained in the given tree
        Also available is the filtering of the branches by a regular expression
        
        This method uses a slightly different method than that of the first method in order to
        try and speed up the process
        
                Instead of parsing all buckets i only parses the top ones that are desired by the user
                so it will parse the top 20 or top 10 or top however many branches within the file
                This does offer some speedup'''
    gROOT.ProcessLine("gErrorIgnoreLevel = 2500;")
    rootfile = TFile.Open(fName)
    tree = rootfile.Get(tName)
    #get branches
    branches = tree.GetListOfBranches() 
    allBranches = getSubBranches(branches, branchRegex)
    #parse only the top branches.
    topBranches = filterTopBranches(allBranches, topN)
    buckets = []
    #gather layout information
    for i in topBranches:
        idx = 0
        basket = i.GetBasket(idx)
        mother = i.GetMother().GetName()
        name = i.GetName()
        while basket != None:
            start = basket.GetSeekKey()
            length = basket.GetNbytes()
            end = start + length-1
            if byMother:
                t = (start, length, end, mother, basket.GetNevBuf())
            else:
                t = (start, length, end, name, basket.GetNevBuf())
            buckets.append(t)
            idx = idx + 1
            basket = i.GetBasket(idx)
    sortBucket = sorted(buckets, key=lambda tup: tup[3])
    return sortBucket

def filterTopBranches(allBranches, topN):
    '''Filter the branches so we can ignore small ones'''
    l1 = sorted(allBranches, key=totalSize, reverse=True)
    return l1[:topN]


def totalSize(branch):
    return branch.GetTotalSize()

def totBytes(branch):
    return branch.GetTotBytes()
    
def zippedBytes(branch):
    return branch.GetZipBytes()

def listFileTrees(file):
    '''Get the list of trees in a file'''
    rootfile = TFile.Open(file)
    print '\n\nThe following trees are in the file: '
    for i in rootfile.GetListOfKeys():
        print i.GetName()

def main():
    '''main routine used for testing.....not needed anymore'''
    data = parseFile('eventdata.root', 'EventTree')
    transformedData = transformByteToMB(data)
    plotFileLayout(transformedData, true, 'out.png')

if __name__ == '__main__':
    main()
