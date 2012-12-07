import random
from time import clock, time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

colors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white', 'yellow']
colorKey = {}
colorCount = 0

def getColor(branch):
    global colors
    global colorKey
    global colorCount
    try:
        return colorKey[branch]
    except KeyError:
        idx = colorCount % len(colors)
        color = colors[idx]
        colorCount = colorCount + 1
        colorKey[branch] = color
        return color

def genData():
    BRANCHES = ['A','B','C','D','E']
    vals = []
    for mb in range(100):
        i = 0
        while i < 1000:
            gap = random.randint(10,100)
            idx = random.randint(0,4)
            branch = BRANCHES[idx]
            val = (mb, i, i+gap, branch)
            vals.append(val)
            i = i+gap
    return vals

def transformByteToMB(data):
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
    '''plot the file layout data given a a list of MB'''
    #keep track of maximum x and y for bounds
    maxy = 0
    maxx = 10
    height = 1024

    start = time()
    #Plot the data
    for point in data:
        #Bottom y cornder is the height in mb
        y = point[0] * height
        if maxy < y + height:
            maxy = y+height
        #x is the offset
        x = point[1]
        xy = x,y
        w = point[2] - point[1]
        if (x+w) > maxx:
            maxx = (x+w)
        #get the color
        color = getColor(point[3])
        p = mpatches.Rectangle(xy,w,height,facecolor=color, edgecolor=color)
        plt.gca().add_patch(p)
    end = time()
    print "Adding Rect Time %f"%(end-start)
    plt.xlim((0,maxx))
    plt.ylim((0,maxy))

    
    xtic= [x for x in range(maxx) if x % 1024==0]
    #print(xtic)
    ytic= [y for y in range(maxy) if (y % pow(2,20)) ==0]
    xlab = [str(i/1024) for i in xtic]
    ylab = [str(i/(pow(2,20))) for i in ytic]
    
    #set up axis tics etc
    plt.xlabel('Offset in Mb')
    plt.ylabel('Mb in File')
    plt.xticks(xtic,xlab)
    plt.yticks(ytic,ylab)

    

    start = time()
    plt.draw()
    end = time()

    print "Render Chart %f"%(end-start)
    
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
