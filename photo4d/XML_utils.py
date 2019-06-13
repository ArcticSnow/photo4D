# coding :utf8

from lxml import etree
import os
import pandas as pd
import numpy as np
import cv2 as cv


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
        with open(file_path, 'r'):
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
        return
    except FileNotFoundError:
        print("WARNING Cannot find file S2D xml at  " + file_path)
        return

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
    return np.array(point_list).astype(np.float)


def write_S2D_xmlfile(dico_img_measures, file_name):
    """
    Write  an xml file with 2D mesures of points in different images, in a way that MicMac can read it
    :param dico_img_measures: dictionnary containing 2D measures. Must looks like :
    {NameImage1 (String) : {NamePoint1 (String) : (measureX, measureY) (tuple of float),
                           NamePoint2 (String) :  (measureX, measureY) (tuple of float), todo la doc est a continuer
                           ...},
     NameImage2 (String) : {NamePoint1 (String) : measure (String, 'coordPoint1Image2 coordPoint1Image2'),
                           NamePoint2 (String) : measure (String, 'coordPoint2Image2 coordPoint2Image2'),
                           ...}, ...}
    :param file_name: path or name of the output file
    """
    # Creation of the document root
    measures_set = etree.Element('SetOfMesureAppuisFlottants')

    #  iterate over pictures
    for image, dico_measures in dico_img_measures.items():

        img_meas = etree.SubElement(measures_set, 'MesureAppuiFlottant1Im')
        name_img = etree.SubElement(img_meas, 'NameIm')
        name_img.text = image

        # iterate over measures for each picture
        for point, measure in dico_measures.items():

            pt_mes = etree.SubElement(img_meas, 'OneMesureAF1I')
            etree.SubElement(pt_mes, 'NamePt').text = point
            coord_img_pt = etree.SubElement(pt_mes, 'PtIm')
            coord_img_pt.text = "{} {}".format(measure[0], measure[1])

    # open the file for writing
    try:
        with open(file_name, 'w') as file:
            # Header
            file.write('<?xml version="1.0"?>\n')
            # Writing all the text we created
            file.write(etree.tostring(measures_set, pretty_print=True).decode('utf-8'))
    except IOError:
        print('Error while writing file')
        return


def write_masq_xml(tif_mask, output=""):
    """
    write  default xml file describing the mask from MicMac
    Even if this file seems useless, MicMac can throw an error without this file associated to the mask (in Malt)

    :param tif_mask: path to the MicMac mask, in .tif format
    :param output: path for output xml file
    """
    # do some checks
    if tif_mask.split('.')[-1] not in ["tif", "tiff"]:
        print("Wrong input path " + tif_mask + "\n Must be a .tif file")
        return
    if output == "":
        output = '.'.join(tif_mask.split('.')[:-1]) + ".xml"
    elif output.split('.')[-1] != "xml":
        print("Wrong output path " + output + "\n Must be a .xml file")
        return

    file_ori = etree.Element('FileOriMnt')
    name = etree.SubElement(file_ori, 'NameFileMnt')
    name.text = tif_mask

    nb_pix = etree.SubElement(file_ori, 'NombrePixels')
    shape = cv.imread(
        tif_mask).shape  # todo find a easier way
    nb_pix.text = "{} {}".format(shape[1], shape[0])
    # write some default values
    etree.SubElement(file_ori, 'OriginePlani').text = "0 0"
    etree.SubElement(file_ori, 'ResolutionPlani').text = "1 1"
    etree.SubElement(file_ori, 'OrigineAlti').text = "0"
    etree.SubElement(file_ori, 'ResolutionAlti').text = "1"
    etree.SubElement(file_ori, 'Geometrie').text = "eGeomMNTFaisceauIm1PrCh_Px1D"

    # write the xml file
    try:
        with open(output, 'w') as file:
            file.write('<?xml version="1.0"?>\n')
            file.write(etree.tostring(file_ori, pretty_print=True).decode('utf-8'))
    except IOError:
        print('Error while writing file')
        return


def change_Ori(initial_pictures, final_pictures, ori_folder_path):
    """
    Changes all the files of an Ori- folder from MicMac, in the way that every reference to initial pictures
    is replaced by reference to final_pictures
    WARNING this will totally modify the folder without backup of the initial one, think about make a copy first
    :param initial_pictures: list of initial pictures to be replaced, in the same order as the final one
    :param final_pictures: list of initial pictures to be replaced, in the same order as the final one
    :param ori_folder_path: path of the orientation folder (name beginning with Ori- )
    """
    # some checks
    print( os.path.basename(ori_folder_path)[:4])
    if os.path.basename(ori_folder_path)[:4] != "Ori-":
        print("Ori path is not valid : {}\nYou need to enter the path to the Ori-folder ".format(ori_folder_path))
        return
    elif len(initial_pictures) != len(final_pictures):
        print("List of input and output pictures must have the same size")
        return
    nb_pictures = len(initial_pictures)

    # change orientation files
    for j in range(nb_pictures):
        # rename Orientation files
        if os.path.exists(os.path.join(ori_folder_path, 'Orientation-{}.xml'.format(initial_pictures[j]))):
            os.rename(os.path.join(ori_folder_path, 'Orientation-{}.xml'.format(initial_pictures[j])),
                      os.path.join(ori_folder_path, 'Orientation-{}.xml'.format(final_pictures[j])))

    # write a short summary
    with open(os.path.join(ori_folder_path,"log.txt"), 'w') as log:
        log.write("This orientation was not calculated by MicMac with these pictures\n\n")
        log.write("The names of pictures were just changed \n\n")
        for i in range(nb_pictures):
            log.write("{} was replaced by {}\n".format(initial_pictures[i], final_pictures[i]))


def change_xml(initial_pictures, final_pictures, xml_path):
    """
    Replace all occurrences of initial pictures with final pictures in a xml/txt file
    initial pictures[i] will be replaced by final_pictures[i]

    :param initial_pictures: list of pictures to be replaced
    :param final_pictures: list of replacement pictures, in the same order as initial pictures
    :param xml_path: path to the file to process
    """
    # checking length
    if len(initial_pictures) != len(final_pictures):
        print("List of input and output pictures must have the same size")
        return
    nb_pictures = len(initial_pictures)

    # Read the xml file
    with open(xml_path, 'r') as file:
        file_data = file.read()
    for i in range(nb_pictures):
        # Replace the target string
        file_data = file_data.replace(initial_pictures[i], final_pictures[i])
    # Write the file out again
    with open(xml_path, 'w') as file:
        file.write(file_data)


def write_couples_file(file_path, master_image, pictures_list):
    """
    write an xml file for micmac command Tapioca, for pictures linked to one image

    :param file_path: path to xml file, if it already exists, it will be replaced
    :param master_image: image to compare with all the others
    :param pictures_list:
    """
    root = etree.Element('SauvegardeNamedRel')
    for img in pictures_list:
        couple = etree.SubElement(root, 'Cple')
        couple.text = str(master_image) + " " + str(img)
    with open(file_path, 'w') as xml:
        xml.write('<?xml version="1.0" encoding="UTF_8"?>\n')
        xml.write(etree.tostring(root, pretty_print=True).decode('utf-8'))


if __name__ == "__main__":
    print(read_S2D_xmlfile(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/all_points-S2D_dist_max.xml"))
