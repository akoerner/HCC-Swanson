from ROOT import *
from HCCPlot import *


#Recursivly get the sub branches
def getSubBranches(branches):
    if len(branches) == 0:
        return []
    else:
        vals =  []
        for b in branches:
            vals.append(b)
            subBranches = b.GetListOfBranches()
            retVal = getSubBranches(subBranches)
            for i in retVal:
                vals.append(i)
        return vals




def parseFile(fName, tName):
    rootfile = TFile.Open(fName)
    tree = rootfile.Get(tName)
    branches = tree.GetListOfBranches()
    a = getSubBranches(branches)
    buckets = []
    for i in a:
        idx = 0
        basket = i.GetBasket(idx)
        while basket != None:
            start = basket.GetSeekKey()
            length = basket.GetNbytes()
            end = start + length-1
            t = (start, length, end, i.GetName())
            buckets.append(t)
            idx = idx + 1
            basket = i.GetBasket(idx)
    sortBucket = sorted(buckets, key=lambda tup: tup[0])
    return sortBucket

def listFileTrees(file):
    rootfile = TFile.Open(file)
    for i in rootfile.GetListOfKeys():
        print i.GetName()

def main():
    data = parseFile('eventdata.root', 'EventTree')
    transformedData = transformByteToMB(data)
    plotFileLayout(transformedData, true, 'out.png')

if __name__ == '__main__':
    main()
