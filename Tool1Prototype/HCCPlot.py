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
from time import clock, time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from  matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.collections import PatchCollection
from matplotlib.collections import PathCollection

def transformByteToMB(data):
    '''transform the data that is obtained parsing the root file into the
        data that can be plotted using the two methods in this class'''
    scale = pow(2,20)
    newData = []
    for i in data:
        mb = i[0] / scale
        offset = i[0] % scale
        end = offset + i[1]
        name = i[3]
        basket = (mb,offset,end,name)
        #need to add for baskets that go off of the end and rescale
        if end > scale:
            basket = (mb,offset, scale,name)
            carryover = (mb +1, 0,end - scale, name)
            newData.append(basket)
            newData.append(carryover)
        else:
           newData.append(basket)

    return newData

def getColor(branch ,colorMap):
    '''Get the color from the color map'''
    if branch in colorMap:
        return colorMap[branch] 
    else:
        return 'black'


def plotFileLayout(data, display, outName, colorMap, legendBranches):
    '''plot the file layout data given a a list of MB transformed by the method
        in this file'''

    #keep track of maximum x and y for bounds
    maxy = 0
    maxx = 10
    height = 1024
    arts =[]
    labels = []

    #keep track of branch and color
    curBranch = ''
    #Plot the data
    branchPaths = []
    #movment same every time
    codes =[Path.MOVETO,
         Path.LINETO,
         Path.LINETO,
         Path.LINETO,
         Path.CLOSEPOLY,
         ] 
    #get axis
    ax = plt.gca()
    for point in data:
        #get the color if it is a differnet branch add it to the collection
        if point[3] != curBranch:
            if len(branchPaths) != 0:
                color = getColor(curBranch, colorMap)
                #stuff for the legend
                if legendBranches != None and curBranch in legendBranches: 
                    arts.append(mpatches.Rectangle((0,0),1,1,fc=color))
                    labels.append(curBranch)
                #add it to the collection and 
                ax.add_collection(PathCollection(branchPaths,facecolor=color,edgecolor=color, linewidth=.0))
                curBranch = point[3]
                branchPaths = []
                #take care of color map stuff

        #get x and y
        y = point[0] * height
        x = point[1]
        w = point[2] - point[1]
        verts = [ (x,y), 
            (x,y+height),
            (x+w,y+height), 
            (x+w,y), 
            (x,y),
            ]
        branchPaths.append(Path(verts, codes))
        
        #update maximums
        if maxy < y + height:
            maxy = y+height
        if (x+w) > maxx:
            maxx = (x+w)
    
    #must do one last update of the color
    if len(branchPaths) != 0:
        color = getColor(curBranch, colorMap)
        #stuff for the legend
        if legendBranches != None and curBranch in legendBranches: 
            arts.append(mpatches.Rectangle((0,0),1,1,fc=color))
            labels.append(curBranch)
            #add it to the collection and 
        ax.add_collection(PathCollection(branchPaths,facecolor=color,edgecolor=color, linewidth=.0))

    path = PathCollection(branchPaths,facecolor=color,edgecolor=color)

    #add the collection to the graphic
    ax.add_collection(path)

    plt.xlim((0,maxx))
    plt.ylim((0,maxy))
    
    #set up axis tics etc
    plt.xlabel('Offset within Mb (kb)')
    plt.ylabel('Mb Offset in File')
    plt.title('File Layout Graph')

    #fix the labels
    plt.draw()

    #fix the y labels
    spacing = int(maxy/10)
    locs = [y for y in range(0, maxy,spacing)]
	
    labs = [str(y/1024) for y in locs]
    plt.yticks(locs,labs)

    locs = [256, 512, 789, 1024]
    locs = [x * 1024 for x in locs]
    print locs
    labs = [str(x/1024) for x in locs]
    plt.xticks(locs,labs)
    #display or save it
    if(display):
        plt.show()
    else:
        plt.savefig(outName)
        if legendBranches != None:
            fp = FontProperties()
            fp.set_size('small')
            fig = plt.figure()
            fig.legend(arts, labels, loc='upper left', mode='expand', prop = fp)
            plt.savefig(outName[:-4] + '_legend' + '.png')

def getName(file):
    '''get the name from a file name
            this is simply the .root removed and .png appened'''
    idx = file.rfind('.')
    return file[:idx] + '.png'
