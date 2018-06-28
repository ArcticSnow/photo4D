# coding : uft8
import cv2 as cv
import matplotlib.pyplot as plt
from skimage.feature import match_template
import numpy as np
import time
import os
import pandas as pd


def diff_evol():
    df = pd.read_csv('test1_cam_east.csv')
    print(df.to_string())
    fig, ax = plt.subplots(1, 2, figsize=(8, 5))
    fig.suptitle('Evolution of template matching method in time\n(without corrections)', fontsize=16)
    plt.subplots_adjust(left=0.2, wspace=0.5, top=0.8)
    y = df.Y_calc.loc[df.Sample_name == 'sample_1.jpg']
    ax[0].plot(np.flipud(np.arange(0, y.shape[0])), (y - df.Y_ini.loc[df.Sample_name == 'sample_1.jpg'])[::-1])
    ax[0].set_title('Sample 1')
    ax[0].set_xlim(600, -10)
    ax[0].set_ylabel('difference to initial column position (px)')
    ax[1].set_ylabel('difference to initial column position (px)')
    ax[1].set_xlabel('time (hour)')
    ax[0].set_xlabel('time (hour)')
    ax[1].set_xlim(600, -10)
    y_s7 = df.Y_calc.loc[df.Sample_name == 'sample_7.jpg']
    ax[1].plot(np.arange(0, y_s7.shape[0]), y_s7 - df.Y_ini.loc[df.Sample_name == 'sample_7.jpg'])
    ax[1].set_title('Sample 7')

    plt.show()


if __name__ == "__main__":
    diff_evol()
    """
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
    plt.show()"""
