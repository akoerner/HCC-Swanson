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

def plotFileLayout(data, display, outName, tenBig):
    '''plot the file layout data given a a list of MB transformed by the method
        in this file'''
    #Keep track of colors
    colors = ['blue', 'darkgreen', 'darkgoldenrod', 'cyan', 'darkorange', 'darkmagenta', 'yellow', 'deeppink', 'greenyellow', 'red']
    colorIdx = 0
    color = colors[colorIdx]

    if tenBig != None:  
        colorMap = {}
    arts = []
    labels = []

    #keep track of maximum x and y for bounds
    maxy = 0
    maxx = 10
    height = 1024
    curBranch = ''
    start = time()
    #Plot the data
    branchPaths = []
    #movment same every time
    codes =[Path.MOVETO,
         Path.LINETO,
         Path.LINETO,
         Path.LINETO,
         Path.CLOSEPOLY,
         ] 
    ax = plt.gca()
    for point in data:
        #get the color if it is a differnet branch add it to the collection
        if point[3] != curBranch:
            if len(branchPaths) != 0:
                if tenBig != None:
                    if curBranch in colorMap:
                        color = colorMap[curBranch]
                    else:
                        if curBranch in tenBig:
                            color = colors[colorIdx % len(colors)]
                            colorMap[curBranch] = color 
                            colorIdx = colorIdx + 1
                            print curBranch, colorMap[curBranch]
                        else:
                            color = 'black' 
                else:
                    color = colors[colorIdx % len(colors)]
                    colorIdx = colorIdx + 1
                path = PathCollection(branchPaths,facecolor=color,edgecolor=color)
                if tenBig != None and curBranch in tenBig:
                    arts.append(mpatches.Rectangle((0,0),1,1,fc=color))
                    labels.append(curBranch)
                curBranch = point[3]
                ax.add_collection(PathCollection(branchPaths,facecolor=color,edgecolor=color, linewidth=.0))
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
    path = PathCollection(branchPaths,facecolor=color,edgecolor=color)
    ax.add_collection(path)
    end = time()
    print "Adding Rect Time %f"%(end-start)
    plt.xlim((0,maxx))
    plt.ylim((0,maxy))
    
    #set up axis tics etc
    plt.xlabel('Offset within Mb (kb)')
    plt.ylabel('Mb Offset in File')
    plt.title('File Layout Graph')

    

    start = time()
    #fix the labels
    plt.draw()
    end = time()


    #loc, labels = plt.yticks()
    #loc[-1] = maxy
    #newloc = ['%.1f'%(i/1024) for i in loc]
    #plt.yticks(loc, newloc) 

    spacing = int(maxy/10)
    locs = [y for y in range(0, maxy,spacing)]
	
    labs = [str(y/1024) for y in locs]
    plt.yticks(locs,labs)

    
    locs = [x for x in range(0,pow(2,20),209715)]
    labs = [str(x/1024) for x in locs]
    plt.xticks(locs,labs)
    print "Render Chart %f"%(end-start)
    print "Number of colors %f"%colorIdx
    #display or save it
    if(display):
        plt.show()
    else:
        start = time()
        plt.savefig(outName)
        end = time()
        print "Saving %f"%(end-start)
        if tenBig != None:
            fp = FontProperties()
            fp.set_size('small')
            fig = plt.figure()
            fig.legend(arts, labels, loc='upper left', mode='expand', prop = fp)
            plt.savefig(outName[:-4] + '_legend' + '.png')

def plotFileLayoutOneColor(data, display, outName):
    '''plot the file layout data given a a list of MB'''
    '''only one branch color when it has been filtered'''
    color = 'black'
    #keep track of maximum x and y for bounds
    maxy = 0
    maxx = 10
    height = 1024
    start = time()
    #Plot the data
    branchPaths = []
    #movment same every time
    codes =[Path.MOVETO,
         Path.LINETO,
         Path.LINETO,
         Path.LINETO,
         Path.CLOSEPOLY,
         ] 
    ax = plt.gca()
    for point in data:
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

    ax.add_collection(PathCollection(branchPaths,facecolor=color,edgecolor=color))
    end = time()
    print "Adding Rect Time %f"%(end-start)
    plt.xlim((0,maxx))
    plt.ylim((0,maxy))

    
    #set up axis tics etc
    plt.xlabel('Offset within Mb (kb)')
    plt.ylabel('Mb offset in File')
    plt.title('File Layout Graph')
    

    start = time()
    plt.draw()
    end = time()
    print "Render Chart %f"%(end-start)

    #fix the labels
    plt.draw()
    end = time()

    spacing = int(maxy/10)
    locs = [y for y in range(0, maxy,spacing)]
    labs = [str(y/1024) for y in locs]
    if len(locs) != 11:
        locs.append(maxy)
        labs.append(str(maxy/1024))

    plt.yticks(locs,labs)
    
    locs = [x for x in range(0,pow(2,20),209715)]
    labs = [str(x/1024) for x in locs]
    plt.xticks(locs,labs)

    if(display):
        plt.show()
    else:
        start = time()
        plt.savefig(outName)
        end = time()
        print "Saving %f"%(end-start)

def getName(file):
    idx = file.rfind('.')
    return file[:idx] + '.png'
