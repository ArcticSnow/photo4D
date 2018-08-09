# coding :utf8

from lxml import etree
import os
import pandas as pd
import numpy as np


# todo finir la traduction
def extract_res(ori_folder_path, xmlfile='Residus.xml', do_txt=False, output_folder_path="",
                output_name="residuals_last_iter.txt",
                sep=',', ):
    """
    Read the residual file from MicMac and create a txt file (with separator, allows .csv) with only residuals of the
    last iteration : mean residual and residual for each picture.

    :param ori_folder_path: folder where is the xml residuals file, from MicMac, it is an orientation folder (name beginning with "Ori-)
    :param xmlfile: name of xml file, always 'Residus.xml' from MicMac
    ======
    these parameter are only usefull if do_txt==True, in this case a txt file will be writen
    :param do_txt: if False, no file will be written
    :param output_folder_path: folder where to save the txt file, by default same as ori_folder_path
    :param output_name: name of the output file, default "residuals_last_iter.txt"
    :param sep: separator of output file, default ','
    ======
    :return: 1 if failed, dictionary of residuals if no errors detected
            the dictionary have nb_inter, AverageResidual and names of the pictures as index
            the element corresponding to one picture is a tuple ('Name', 'Residual', 'PercOk', 'NbPts', 'NbPtsMul')
            (for more information about these values, see MicMac documentation)
    """

    file_content = ""
    dict = {}

    elements = ('Name', 'Residual', 'PercOk', 'NbPts', 'NbPtsMul')
    try:
        # Parsing of xml
        tree = etree.parse(ori_folder_path + xmlfile)

        # Getting number of iterations
        nb_iters = tree.xpath("/XmlSauvExportAperoGlob/Iters/NumIter")[-1].text
        file_content += 'nb_iters' + sep + nb_iters + '\n'
        dict['nb_iters'] = int(nb_iters)

        # Recuperation de la moyenne des residus de la derniere iteration
        av_resid = tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}][NumEtape=3]/\
                                    AverageResidual".format(nb_iters))[0].text
        file_content += 'AverageResidual' + sep + av_resid + '\n'
        dict['AverageResidual'] = float(av_resid)

        # Recuperation des donnees pour chaque image de la derniere iteration
        file_content += ('\nName{}Residual{}PercOk{}NbPts{}NbPtsMul\n'.format(sep, sep, sep, sep))
        for img in tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}]\
                                                                 [NumEtape=3]/OneIm".format(nb_iters)):
            obj = ''
            for e in elements:
                obj += img.find(e).text + sep
            file_content += obj + '\n'
            image_name = obj.split(sep)[0]
            dict[image_name] = obj.split(sep)[1:-1]
    except OSError:
        print("WARNING Can't open the file " + ori_folder_path + xmlfile)
        return 1
    except etree.XMLSyntaxError:
        print("WARNING The xml is not correct")
        return 1

    # write the txt file
    if do_txt:
        if output_folder_path == "":
            output_folder_path = ori_folder_path

        # Creation of the txt file
        try:
            with open(output_folder_path + output_name, "w") as file:
                file.write(file_content)
        except IOError:
            print("Cannot write file")

    return dict


def read_S2D_xmlfile(file_path):
    """
    read a file containing pixel coordinates of points in images from the SaisieAppuis MicMac commands and put data
    into a dictionary

    :param file_path: path to the s2d xml file
    ========
    :return: a dictionary, pictures names are the indexes, and for each picture the element is a dictionary with points measurments
    todo cest vraiment trop mal ecrit !!!!!!
    { picture1 : {point1: (coordX, coordY),
                 {point2: (coordX, coordY)}
      picture2 : {point1: (coordX, coordY),
                 ...}
    ...}
    """
    dic_img_measures = {}
    # read the file
    try:
        with open(file_path, 'r') as xml:
            # Parsing of xml
            tree = etree.parse(file_path)
            # loop on images
            for image in tree.xpath("/SetOfMesureAppuisFlottants/MesureAppuiFlottant1Im/NameIm"):
                dic_measures = {}
                # loop on the points
                for point in tree.xpath(
                        "/SetOfMesureAppuisFlottants/MesureAppuiFlottant1Im[NameIm='{}']/OneMesureAF1I".format(
                            image.text)):
                    point_name = point[0].text.rstrip(" ")
                    measure = point[1].text.split(" ")
                    dic_measures[point_name] = (float(measure[0]), float(measure[1]))

                dic_img_measures[image.text] = dic_measures

    except etree.XMLSyntaxError:
        print("WARNING The xml file is not valid  " + file_path)
        exit(1)
    except FileNotFoundError:
        print("WARNING Cannot find file S2D xml at  " + file_path)
        exit(1)

    return dic_img_measures


# todo faire qqchose de cette fonction qui craint...

def count_tiepoints_from_txt(main_folder_path):
    """
    generate a panda DataFrame with the tie points found by the Tapioca command of MicMac USED WITH ExpTxt=1

    :param main_folder_path: path of the folder where is situated the Homol folder, or path of the Homol folder
    :return:
    - a panda DataFrame, row and column indexes are the name of pictures used, and for cell, the number
    of Tie points found in image row compared to img colum todo rendre ca lisible
            Img1    Img2    Img3
    Img1    0       nb1,2   nb1,3
    Img2    nb2,1     0     nb2,3
    Img3    nb3,1   nb3,1     0
    """

    # path checking
    if main_folder_path[-1] != "/": main_folder_path += "/"
    if main_folder_path.split("/")[-2] != "Homol":
        main_folder_path += "Homol/"

    try:
        folder_list = os.listdir(main_folder_path)

        # collect picture names in Homol directory, each folder is for one picture
        index = []
        for folder in folder_list:
            index.append(folder[6:])  # remove Pastis, the folder name being like PastisNamePicture

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


def get_tiepoints_from_txt(path):
    point_list = []
    with open(path) as f:
        for line in f.readlines():
            point_list.append(line.split(" "))
    return np.array(point_list)


if __name__ == "__main__":
    print(read_S2D_xmlfile(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/MicMac_Initial/GCP-S2D.xml"))
