# coding : uft8
import cv2 as cv
import matplotlib.pyplot as plt
import os
from skimage.feature import match_template
import numpy as np
import WriteMicMacFiles.WriteXml as wxml
import WriteMicMacFiles.ReadXml as rxml
import pandas as pd
import plotly.offline as py
from DetectPoints.Temp import draw_cross
import plotly.graph_objs as go


def diff_evol():
    df = pd.read_csv('test_all_cam_adapt4.csv')
    print(df.to_string())
    fig, ax = plt.subplots(1, 2, figsize=(8, 5))
    fig.suptitle('Evolution of template matching method in time\n(without corrections)', fontsize=16)
    plt.subplots_adjust(left=0.2, wspace=0.5, top=0.8)
    x = df.Xpos.loc[(df.folder_index == 0) & (df.GCP == 'GCP4')]
    ax[0].plot(np.arange(0, x.shape[0]), x - 4754.0, 'r')
    y = df.Ypos.loc[(df.folder_index == 0) & (df.GCP == 'GCP4')]
    ax[0].plot(np.flipud(np.arange(0, y.shape[0])), y - 1356.0)
    ax[0].set_title('GCP 4, cam_east')
    # ax[0].set_xlim(600, -10)
    # ax[0].set_ylabel('difference to initial column position (px)')
    # ax[1].set_ylabel('difference to initial column position (px)')
    ax[1].set_xlabel('time (hour)')
    ax[0].set_xlabel('time (hour)')
    # ax[1].set_xlim(600, -10)

    x = df.Xpos.loc[(df.folder_index == 0) & (df.GCP == 'GCP4')]
    ax[1].plot(np.arange(0, x.shape[0]), x - 4384.0, 'r')
    y = df.Ypos.loc[(df.folder_index == 0) & (df.GCP == 'GCP4')]
    ax[1].plot(np.flipud(np.arange(0, y.shape[0])), y - 1999.0)
    ax[1].set_title('GCP 4, cam_middle ?')

    plt.show()

def extract_values(df, threshold=50, nb_values=5, max_dist=50, window_size=(200, 200), method="Median"):
    """
    extract detected positions from the DataFrame containing tie points coordinates
    feel free to add new methods
    :param df: DataFrame like the one from detect_from_s2d()
    :param threshold: max value in pixels for the magnitude of the vector (from ini to detect)
    :param nb_values: max values to be used for the method
            the values used are the closest from the GCP initial position
    :param max_dist: max value in pixel for the distance from the GCP to the vector origin
    :param window_size: size of the extracts used for detection (to determine coordinates of gcp in the extracts)
    :param method: method to use for computing positions
    :return: tuple with 2 elements:
    - a dictionary containing the computed position of GCPs in each picture, readable for the others functions,
    indexed first by picture names and then by GCP names
    - a panda DataFrame containing the computed position of GCPs in each picture
    columns :
    ['Image', 'GCP', 'Xpos', 'Ypos', 'nb_tiepoints', 'date','nb_close_tiepoints']
    """

    # compute new positions of GCP according to the shift of each tie point
    df['Xshift'] = df.Xgcp_ini + df.Xdetect - df.Xini
    df['Yshift'] = df.Ygcp_ini + df.Ydetect - df.Yini

    # compute vector module
    df['module'] = np.sqrt((df.Xini - df.Xdetect) ** 2 + (df.Yini - df.Ydetect) ** 2)

    # compute vector direction
    df['direction'] = np.arctan2((df.Xini - df.Xdetect), (df.Yini - df.Ydetect)) * 180 / np.pi + 180

    # compute from gcp and tie point in the initial image (gcp is in the center of the extracts)
    pos_center = window_size[0] / 2, window_size[1] / 2
    print(pos_center)
    df['dist'] = np.sqrt((df.Xini - pos_center[0]) ** 2 + (df.Yini - pos_center[1]) ** 2)

    # filter outliers having a incoherent module
    df_filtered = df.loc[df.module <= threshold]

    dic_image_gcp = {}
    result = []
    # iterate over images
    for image, group in df_filtered.groupby(['Image']):
        dic_gcp = {}
        for gcp, group_gcp in group.groupby(['GCP']):
            nb_tiepoints = group_gcp.shape[0]
            group_gcp_filtered = group_gcp.loc[group_gcp.dist <= max_dist]
            nb_close_tiepoints = group_gcp_filtered.shape[0]
            group2 = group_gcp_filtered.nsmallest(nb_values, 'dist')
            print(group_gcp_filtered.shape)
            if group_gcp_filtered.shape[0] != 0: # if there is no values left in DataFrame, the point is ignored
                if method == "Median":
                    measure = group2.Xshift.median(), group2.Yshift.median()
                elif method == "Mean":
                    measure = group2.Xshift.mean(), group2.Yshift.mean()
                elif method == 'Min':
                    measure = group2.Xshift.min(), group2.Yshift.min()
                else:
                    print('Method must be one of these values:\n"Median"\n"Min"\n"Mean"')
                    exit(1)
                date = group2.date.min()
                dic_gcp[gcp] = measure


                result.append([image, gcp, measure[0], measure[1], nb_tiepoints, date, nb_close_tiepoints])
        if dic_gcp != {}: dic_image_gcp[image] = dic_gcp

    return dic_image_gcp, pd.DataFrame(result, columns=['Image', 'GCP', 'Xpos', 'Ypos', 'nb_tiepoints', 'date',
                                                        'nb_close_tiepoints'])

if __name__ == "__main__":

    csv = 'test_sift_camtot_new_gcp.csv'
    df = pd.read_csv(csv)
    print(df.loc[(df.Image=="DSC03469.JPG") & (df.GCP == "GCP8")].to_string())

    resultt = extract_values(df,max_dist=100)
    result = resultt[1]
    print(resultt[0])
    wxml.write_S2D_xmlfile(resultt[0],"C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/all_points-S2D.xml" )

    # dico = rxml.read_S2D_xmlfile("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/all_points-S2D.xml")
    # print(dico)
    # mini_dico = {**rxml.read_S2D_xmlfile("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/first_set-S2D.xml"),
    #     **rxml.read_S2D_xmlfile("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/last_set-S2D.xml")}
    # l = []
    # for file in os.listdir("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/"):
    #     if file.split(".")[-1] == "JPG":
    #         try:
    #             frite = dico[file]
    #             img = cv.imread("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/" + file)
    #             s = 0
    #             i=0
    #
    #             for gcp,mes in frite.items():
    #                 mes = int(mes[0]), int(mes[1])
    #                 draw_cross(img,mes,100,255,2)
    #                 cv.putText(img,gcp,mes,cv.FONT_HERSHEY_SIMPLEX,
    #                    2,
    #                    255)
    #                 if gcp in mini_dico[file].keys():
    #                     mes2=mini_dico[file][gcp]
    #                     d = np.sqrt((mes[0] - mes2[0])**2 + (mes[1] - mes2[1])**2)
    #                     l.append([file, gcp , mes[0], mes[1], mes2[0], mes2[1], d])
    #                     s += d
    #                     i +=1
    #             print(s/i)
    #             cv.imwrite("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/" + file + "_cross.JPG",img)
    #         except KeyError:
    #             print("L'image " + file + " n'est pas contenue dans le dictionnaire")
    # df = pd.DataFrame(l,columns=['Image', 'gcp', 'Xdetect', 'Ydetect', 'Xini', 'Yini', 'dist'])
    # print(df)
    # img1 = cv.imread('DSC00801.JPG')
    # pos_ini = df.Xpos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00877.JPG')].values[0], df.Ypos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00877.JPG')].values[0]
    # pos_807 =df.Xpos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00807.JPG')].values[0], df.Ypos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00807.JPG')].values[0]
    # pos_373 = df.Xpos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00373.JPG')].values[0], df.Ypos.loc[(df.GCP == "GCP4") & (df.Image == 'DSC00373.JPG')].values[0]
    # print(pos_ini)
    # draw_cross(img1, pos_ini, 8, 255, 4)
    # draw_cross(img1, pos_807, 8, 0, 4)
    # cv.imwrite('DSC00801_cross.JPG', img1)
    #
    # img2 = cv.imread('DSC00354.JPG')
    # draw_cross(img2, pos_ini, 8, 255, 4)
    # draw_cross(img2, pos_373 , 8, 0, 4)
    # cv.imwrite('DSC00354_cross.JPG', img2)
    """
    # diff_evol()
    
    print(df.to_string())
    inter = df.loc[(df.folder_index == 0) & (df.GCP == 'GCP4')]
    grp = inter.groupby('GCP')
    print(grp.Xdetect.median())

    py.plot({
        "data": [go.Scatter(x=inter.date,
                            y=(grp.Xdetect.median() - grp.Xini.median()), name="x",
                            text=inter.Image),
                 go.Scatter(x=inter.date, y=(inter.Ydetect - inter.Yini), name="y")],
        "layout": go.Layout(title="Evolution of template-matching detected position of GCP4\n" + csv)
    }, auto_open=True)"""

