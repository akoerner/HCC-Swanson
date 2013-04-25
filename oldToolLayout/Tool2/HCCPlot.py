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
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from  matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.collections import PatchCollection
from matplotlib.collections import PathCollection
import numpy 
import matplotlib.colors

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

def plotUsage(data, name='File Usage' ,outname = 'filestuff', limits = None, points=None, subtitle = None):
    '''plot the file layout data given a a list of MB transformed by the method
        in this file'''
    plt.figure()
    
    newData = []
    row = 0
    for i in data:
        if row % 2 == 0:
            newData.append(i)
        row = row + 1
    data = numpy.array(newData)
    # define the colormap
    clrMap = plt.cm.jet
    # extract all colors from the .jet map
    cmaplist = [clrMap(i) for i in xrange(clrMap.N)]
    # force the first color entry to be grey
    cmaplist[0] = (1.0,1.0,1.0,1.0)
# create the new map
    clrMap = clrMap.from_list('custommap', cmaplist, clrMap.N)
    cm.register_cmap(name='custommap', cmap=clrMap)
    #get axis
    maxy = len(data)
    maxx = pow(1,20) 
    plt.pcolormesh(data,vmin = 1, cmap='custommap')#, cmap = mcolor.colormap('gist_ncar'))
    plt.xlabel('Offset within Mb (kb)')
    plt.ylabel('Mb Offset in File')

    if len(name) > 100:
        plt.title(name, fontsize=8)
    else:
        plt.title(name, fontsize=10)
    plt.colorbar()

    if points != None:
        px = [i[0] for i in points]
        py = [i[1]/2 for i in points]
        plt.scatter(px,py, marker=(5,1), c='goldenrod')


    #fix the y labels
    spacing = int(maxy/10)
    locs = [y for y in xrange(0, maxy,spacing)]
    labs = [str(y) for y in locs]
    plt.yticks(locs,labs)
    plt.xlim(0,maxx)
    plt.ylim(0,maxy)

    
    locs = [256, 512, 789, 1024]
    labs = [str(x) for x in locs]
    plt.xticks(locs,labs)
    plt.savefig(outname+ '.png')



def plotFileLayout(data, display, outName, colorMap, legendBranches,limits = None, title = 'File Layout Graph' , fileUsage = None):
    '''plot the file layout data given a a list of MB transformed by the method
        in this file'''

    plt.figure()  

 #keep track of maximum x and y for bounds
    stime = time()
    maxy = 0
    maxx = 10
    height = 2 
    halfway = height
    if fileUsage != None:
        halfway = height * 1/2.
    arts =[]
    labels = []

    if(fileUsage != None):
    
        
        # define the colormap
        cmap = plt.cm.jet
        cmap.set_bad('white')
        #get min and max
        mini = fileUsage.min()
        maxi = fileUsage.max()
        
        plt.pcolormesh(fileUsage,vmin = mini,vmax = maxi,  cmap=cmap)
        plt.colorbar()
        len1 = len(fileUsage)
        len2 = len(fileUsage[0])
        #clean it up
        del fileUsage
        
        #make the background black sort of hackish but color every other row black
        arr = numpy.zeros((len1,len2) )
        for i in xrange(1,len1,2):
            for j in xrange(len2):
                arr[i][j] = 1
        
       
        cmap =matplotlib.colors.LinearSegmentedColormap.from_list('map1', ['black', 'black'])
        plt.pcolormesh(numpy.ma.masked_equal(arr,0), cmap=cmap)
        del arr


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

    print "LENGHT: " , len(data)
        
    #fixes annoying bug
    if len(data) == 0:
        color = 'black'
        
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
        x = point[1] / 1024
        w = point[2] /1024- point[1] / 1024
        verts = [ (x,y+halfway), 
            (x,y+height),
            (x+w,y+height), 
            (x+w,y+halfway), 
            (x,y+halfway),
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

    starty = 0
    
    if(limits == None):
        plt.xlim((0,maxx))
        plt.ylim((0,maxy))
    else:
        plt.xlim((0,maxx))
        plt.ylim((limits[0] , limits[1]) )
        starty = limits[0]  
        maxy = limits[1] 
    
    #set up axis tics etc
    plt.xlabel('Offset within Mb (kb)')
    plt.ylabel('Mb Offset in File')
    if len(title) > 100:
        plt.title(title, fontsize=8)
    else:
        plt.title(title, fontsize=10)

    #fix the labels
    plt.draw()

    #fix the y labels
    spacing = int((maxy-starty)/10)
    if(spacing > 0):
        locs = [y for y in xrange(starty, maxy,spacing)]
	
        labs = [str(y/2) for y in locs]
        plt.yticks(locs,labs)

    locs = [256, 512, 789, 1024]
    locs = [x for x in locs]
    labs = [str(x) for x in locs]
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
    etime = time()
    print 'time: ' + str(etime - stime)
  

def getName(file):
    '''get the name from a file name
            this is simply the .root removed and .png appened'''
    idx = file.rfind('.')
    return file[:idx] + '.png'
