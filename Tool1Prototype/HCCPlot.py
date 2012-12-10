import random
from time import clock, time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

def plotFileLayout(data, display, outName):
    '''plot the file layout data given a a list of MB transformed by the method
        in this file'''
    #Keep track of colors
    colors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white', 'yellow']
    colorIdx = 0
    color = colors[colorIdx]
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
                ax.add_collection(PathCollection(branchPaths,facecolor=color,edgecolor=color, linewidth=.01))
                branchPaths = []
                color = colors[colorIdx % len(colors)]
                colorIdx = colorIdx + 1
                curBranch = point[3]
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
    plt.ylabel('Mb Offset in File')
    plt.title('File Layout Graph')

    

    start = time()
    #fix the labels
    plt.draw()
    end = time()
    loc, labels = plt.yticks()
    loc[-1] = maxy
    newloc = ['%.1f'%(i/1024) for i in loc]
    plt.yticks(loc, newloc) 
    
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
    loc, labels = plt.yticks()
    print loc
    loc[-1] = maxy
    print loc 
    newloc = ['%.1f'%(i/1024) for i in loc]
    plt.yticks(loc, newloc) 
    
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
