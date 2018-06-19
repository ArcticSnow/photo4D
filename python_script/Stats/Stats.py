# coding : uft8
import cv2 as cv
import matplotlib.pyplot as plt
from skimage.feature import match_template
import numpy as np
import time
import os
import pandas as pd

if __name__ == "__main__":
    df=pd.read_csv('data_for_stat.csv')
    print(df.to_string())

    df['XPt_diff'] = df.XPti - df.XRefPti
    df['Dist_diff'] = df.Distij - df.DistRefij


    fig,ax = plt.subplots(3,2)
    ax[0,0].hist(df.XPt_diff.loc[(df.Pti == 0) & (df.XPt_diff<100) & (df.XPt_diff>-100)], bins=100)
    ax[0,0].set_title('point 0')
    ax[0,1].hist(df.XPti.loc[df.Pti == 1] - df.XRefPti.loc[df.Pti == 1])
    ax[0, 1].set_title('point 1')
    ax[1,0].hist(df.XPti.loc[df.Pti == 2] - df.XRefPti.loc[df.Pti == 2])
    ax[1, 0].set_title('point 2')
    ax[1, 1].hist(df.XPti.loc[df.Pti == 3] - df.XRefPti.loc[df.Pti == 3])
    ax[1, 1].set_title('point 3')
    ax[2, 0].hist(df.XPti.loc[(df.Pti == 4)] - df.XRefPti.loc[df.Pti == 4])
    ax[2, 0].set_title('point 4')

    #plt.hist(df.XPti.loc[df.Pti == 4] - df.XRefPti.loc[df.Pti == 4])
    #plt.plot(es.sd.loc[(es.prof == 'E') & (es.m_r=='observation')]
    plt.show()