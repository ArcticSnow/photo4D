# coding : utf8
import cv2 as cv
from matplotlib import pyplot as plt
import shutil
import pandas as pd
import numpy as np
from laspy.file import File

def loadLAS2XYZAIR(filepath):
    '''
    Function to load in console the pointcloud of a LAS file with points attributes
    :param filepath: filepath of the LAS file
    :return: xyz array containing coordinate of the points
    '''
    print('Start loading...')
    inFile = File(filepath, mode='r')
    coords = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()#, inFile.amplitude, inFile.Intensity, inFile.reflectance, inFile.num_returns)).transpose()
    print('Data loaded')
    return coords


def read_txt_gps(path):
    keep = True
    while keep:
        i_min = int(input("indice minimum : "))
        i_max = int(input("indice maximum : "))
        file=open(path,'r')
        list_lines = file.readlines()
        file.close()
        print("file read")
        i = 1
        s_n,s_e,s_h =0,0,0
        compt = 0
        lenght = len(list_lines)
        while i<lenght and i<=i_max:
            if i>= i_min:
                compt +=1
                line = list_lines[i-1].split(',')
                s_n += float(line[2])
                s_e += float(line[3])
                s_h+= float(line[4].rstrip('\n'))
            i+=1
        n = s_n/compt
        e = s_e/compt
        h = s_h/compt
        print(n,e,h)

        ans = input("Continue ?  (y/n)")
        if ans != 'y':
            keep = False

def binData2D(myXYZ, xstart, xend, ystart, yend, nx, ny):
    '''
    Fucntion to bin a scatter point cloud (xyz) into a 2d array
    :param myXYZ: xyz array containings the point cloud coordiantes
    :param xstart:
    :param xend:
    :param ystart:
    :param yend:
    :param nx: number of cells along the x-axis
    :param ny: number of cells along hte y-axis
    :return: a group object (pandas library) with all points classified into bins
    '''
    x = myXYZ[:,0].ravel()
    y = myXYZ[:,1].ravel()
    z = myXYZ[:,2].ravel()
    df = pd.DataFrame({'X' : x , 'Y' : y , 'Z' : z})
    bins_x = np.linspace(xstart, xend, nx+1)
    x_cuts = pd.cut(df.X,bins_x, labels=False)
    bins_y = np.linspace(ystart,yend, ny+1)
    y_cuts = pd.cut(df.Y,bins_y, labels=False)
    bin_xmin, bin_ymin = x_cuts.min(), y_cuts.min()
    print('Data cut in a ' + str(bins_x.__len__()) + ' by ' + str(bins_y.__len__()) + ' matrix')
    dx = (xend - xstart)/nx
    dy = (yend - ystart)/ny
    print('dx = ' + str(dx) + ' ; dy = ' + str (dy))
    grouped = df.groupby([x_cuts,y_cuts])
    print('Data grouped, \nReady to go!!')
    return grouped, bins_x, bins_y, int(bin_xmin), int(bin_ymin)


def xyz2binarray(xyz, xstart, xend, ystart, yend, nx=1000, ny=1000, method='min'):
    '''
    Function to extract projected grid on the XY-plane of point cloud statistics
    :param xyz: a 3 column vector containing the point location in cartesian coordinate system
    :param xstart: x-minimum of the grid
    :param xend: x-maximum of the grid
    :param ystart: y-minimm of the grid
    :param yend: y-maximum of the grid
    :param nx: number of grid cell in the x directions
    :param ny: number of grid cell in the y directions
    :param method: statistics to extract from each gridcell
    :return: returns a 2D array, xmin, and ymax
    TO IMPLEMENT:
        - being able to choose to input dx dy instead of nx ny
    '''
    binned, bins_x, bins_y, bin_xmin, bin_ymin = binData2D(xyz, xstart, xend, ystart, yend, nx, ny)

    if method == 'min':
        ret = binned.Z.min().unstack().T  # .iloc[::-1]
    elif method == 'max':
        ret = binned.Z.max().unstack().T  # .iloc[::-1]
    elif method == 'mean':
        ret = binned.Z.mean().unstack().T  # .iloc[::-1]
    elif method == 'median':
        ret = binned.Z.median().unstack().T  # .iloc[::-1]
    elif method == 'count':
        ret = binned.Z.count().unstack().T  # .iloc[::-1]
    else:
        print("Method not in enum")
        ret = None
        exit(1)

    xmin = bins_x[ret.columns.min().astype(int)]
    ymax = bins_y[ret.index.get_values().max().astype(int)]

    newIndy = np.arange(ret.index.get_values().min(), ret.index.get_values().max() + 1)
    newIndx = np.arange(ret.columns.min(), ret.columns.max() + 1)
    a = ret.reindex(newIndy, newIndx)
    mat = np.zeros((ny, nx)) * np.nan
    mat[bin_ymin:bin_ymin + a.shape[0], bin_xmin:bin_xmin + a.shape[1]] = a

    return mat[::-1], xmin, ymax

def load_ascii_ply(filepath):
    with open(filepath,
              'r') as ply:
        i = 0
        found = 0
        data = ply.readlines()
        while i < len(data) and not found:
            if "end_header" in data[i]:
                found = True
            i += 1
        if found:
            point_list = []
            for j in range(i, len(data)):
                line = data[j].split(' ')
                point_list.append([ float(line[0]), float(line[1]), float(line[2])])
            return np.array(point_list)
        else:
            return None

if __name__ == "__main__":
    #print(loadLAS2XYZAIR("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Midday/2018-6-9_12-16_BigMac.las"))
    array = load_ascii_ply("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Initial/C3DC_BigMac.ply")
    rast, xmin, ymax = xyz2binarray(array, -1, 3 , -0.1, 19, nx=1000, ny=1000, method='mean')
    plt.figure()
    plt.imshow(rast)
    plt.show()