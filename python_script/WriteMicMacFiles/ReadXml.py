# coding :utf8

from lxml import etree
import os
import pandas as pd
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import warnings


# todo finir la traduction
def residual2txt(ori_folder_path, xmlfile='Residus.xml', output_folder_path="", output_name="residuals_last_iter.txt",
                 sep=',', do_txt=True):
    """
    Read the residual file from MicMac and create a txt file (with separator, allows .csv) with only residuals of the
    last iteration : mean residual and residual for each picture.

    :param ori_folder_path: folder where is the xml residuals file, from MicMac, it is an orientation folder (name beginning with "Ori-)
    :param xmlfile: name of xml file, always 'Residus.xml' from MicMac
    :param output_folder_path: folder where to save the txt file, by default same as ori_folder_path
    :param output_name: name of the output file, default "residuals_last_iter.txt"
    :param sep: separator of output file, default ','
    :param do_txt: if False, no file will be written
    :return: 1 if failed, dictionary of residuals if no errors detected
    """

    if output_folder_path == "":
        output_folder_path = ori_folder_path

    # Creation of the txt file
    file = open(output_folder_path + output_name, "w")

    dict = {}

    elements = ('Name', 'Residual', 'PercOk', 'NbPts', 'NbPtsMul')
    try:
        # Parsing of xml
        tree = etree.parse(ori_folder_path + xmlfile)

        # Getting number of iterations
        nb_iters = tree.xpath("/XmlSauvExportAperoGlob/Iters/NumIter")[-1].text
        file.write('nb_iters' + sep + nb_iters + '\n')
        dict['nb_iters'] = int(nb_iters)
        # Recuperation de la moyenne des residus de la derniere iteration
        av_resid = tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}][NumEtape=3]/\
                                    AverageResidual".format(nb_iters))[0].text
        file.write('AverageResidual' + sep + av_resid + '\n')
        dict['AverageResidual'] = float(av_resid)
        # Recuperation des donnees pour chaque image de la derniere iteration
        file.write('\nName{}Residual{}PercOk{}NbPts{}NbPtsMul\n'.format(sep, sep, sep, sep))
        for img in tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}]\
                                                                 [NumEtape=3]/OneIm".format(nb_iters)):
            obj = ''
            for e in elements:
                obj += img.find(e).text + sep
            file.write(obj + '\n')
            image_name = obj.split(sep)[0]
            dict[image_name] = obj.split(sep)[1:-1]
    except OSError:
        print("WARNING Can't open the file " + ori_folder_path + xmlfile)
        return 1
    except etree.XMLSyntaxError:
        print("WARNING The xml is not readable")

    file.close()
    return dict


def read_S2D_xmlfile(filepath, disp=False, img_path=None):
    list_img_measures = []
    with open(filepath, 'r') as xml:
        # Parsing of xml
        tree = etree.parse(filepath)

        for image in tree.xpath("/SetOfMesureAppuisFlottants/MesureAppuiFlottant1Im/NameIm"):
            list_measures = []
            for measure in tree.xpath(
                    "/SetOfMesureAppuisFlottants/MesureAppuiFlottant1Im[NameIm='DSC00859.JPG']/OneMesureAF1I"):
                list_measures.append((measure[0].text, measure[1].text))
            list_img_measures.append([image.text, list_measures])

    if disp:

        img = cv.imread(img_path)

        found = False
        for image in list_img_measures:
            if image[0] == img_path.split('/')[-1]:
                for mes in image[1]:
                    point_name = mes[0]
                    x, y = mes[1].split(' ')
                    pos = (int(float(x)), int(float(y)))
                    pos_up = pos[0] + 500, pos[1] + 500
                    cv.arrowedLine(img, pos_up, pos, 255, 4)
                    cv.putText(img, point_name, pos, cv.FONT_HERSHEY_SIMPLEX,
                               5, (0, 255, 255), thickness=10)
                found = True
        if not found:
            print("Cannot find measure for image " + img_path)
        else:
            plt.imshow(img)
            plt.show()
    return list_img_measures


def count_tiepoints_from_txt(main_folder_path):
    """
    Count Tie Points found by the Tapioca command of MicMac USED WITH ExpTxt=1

    :param main_folder_path: path of the folder where is situated the Homol folder, or path of the Homol folder
    :return: tuple containing
    - a panda DataFrame, row and column indexes are the name of pictures used, and for cell, the number
    of Tie points found in image row compared to img colum todo rendre ca lisible
    - the total number of tie points
    """

    # path checking
    if main_folder_path[-1] != "/": main_folder_path += "/"
    if main_folder_path.split("/")[-2] != "Homol":
        main_folder_path += "Homol/"

    try:
        folder_list = os.listdir(main_folder_path)

        # collect picture names, each folder matches one picture
        index = []
        for folder in folder_list:
            index.append(folder[6:])  # remove Pastis...
        df = pd.DataFrame(np.zeros((len(folder_list), len(folder_list))), index=index, columns=index)

        # count tie points
        s = 0  # total tie points
        for folder in folder_list:
            file_list = os.listdir(main_folder_path + folder)
            for filename in file_list:
                if filename.split('.')[-1] == 'txt':
                    file = open(main_folder_path + folder + "/" + filename, 'r')

                    # basically just counting the number of row in each file
                    i = 0
                    for line in file.readlines():
                        i += 1
                        s += 1
                    df.loc[folder[6:], filename.rstrip('.txt')] = i
        if s == 0:
            print('\033[0;31m WARNING, 0 Tie Points found, please check that ExptTxt=1 in Tapioca \033[0m')
        return df, s
    except IOError:
        print('\033[0;31m' + "Cannot open " + main_folder_path + '\033[0m')


if __name__ == "__main__":
    df =count_tiepoints_from_txt(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Result_guillaume/20170612")[0]
    print(df)
    print(df.ix("DSC00711.JPG"))