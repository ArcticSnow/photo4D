# coding :utf8

from lxml import etree
import os


def write_S3D_xmlfile(list_pt_measures, file_name):
    """
    Write  an xml file with 3D coordinates of points, in a way that MicMac can read it
    :param list_pt_measures: list containing 3D measures in the shape :
    [[NamePt (String), coordinates (String, like 'coord1 coord2 coord3'), incertitude (String, like 'Icoord1, Icoor2, Icoord3', optional'], ...]
    :param file_name: path or name of the output file
    """
    # Creation of the document root
    measures_set = etree.Element('DicoAppuisFlottant')
    for pt in list_pt_measures:
        pt_coord = etree.SubElement(measures_set, 'OneAppuisDAF')
        # coordinates of the point
        coord_pt = etree.SubElement(pt_coord, 'Pt')
        coord_pt.text = str(pt[1])
        # name of the point
        name_pt = etree.SubElement(pt_coord, 'NamePt')
        name_pt.text = str(pt[0])
        # incertitude of the coordinates
        coord_img_pt = etree.SubElement(pt_coord, 'Incertitude')
        try:
            coord_img_pt.text = str(pt[2])
        except IndexError:
            coord_img_pt.text = "1 1 1"

        try:
            # We open the file for writing
            with open(file_name, 'w') as file:
                # Header
                file.write('<?xml version="1.0" encoding="UTF_8"?>\n')
                # Writing all the text we created
                file.write(etree.tostring(measures_set, pretty_print=True).decode('utf-8'))
        except IOError:
            print('Error while writing file')
            exit(1)


def write_S2D_xmlfile(list_img_measures, file_name):
    """
    Write  an xml file with 2D mesures of points in different images, in a way that MicMac can read it
    :param list_img_measures: list containing 2D measures. Must looks like :
    [[NameImage1 (String), [NamePoint1 (String), measure (String, 'coordPoint1Image1 coordPoint1Image1')],
                           [NamePoint2 (String), measure (String, 'coordPoint2Image1 coordPoint2Image1')],
                           ...],
     [NameImage2 (String), [NamePoint1 (String), measure (String, 'coordPoint1Image2 coordPoint1Image2')],
                           [NamePoint2 (String), measure (String, 'coordPoint2Image1 coordPoint2Image2')],
                           ...], ...]
    :param file_name: path or name of the output file
    """
    # Creation of the document root
    measures_set = etree.Element('SetOfMesureAppuisFlottants')
    for img in list_img_measures:
        img_meas = etree.SubElement(measures_set, 'MesureAppuiFlottant1Im')
        name_img = etree.SubElement(img_meas, 'NameIm')
        name_img.text = str(img[0])
        for measure in img[1]:
            pt_mes = etree.SubElement(img_meas, 'OneMesureAF1I')
            name_pt = etree.SubElement(pt_mes, 'NamePt')
            name_pt.text = str(measure[0])
            coord_img_pt = etree.SubElement(pt_mes, 'PtIm')
            coord_img_pt.text = str(measure[1])

    try:
        # We open the file for writing
        with open(file_name, 'w') as file:
            # Header
            file.write('<?xml version="1.0" encoding="UTF_8"?>\n')
            # Writing all the text we created
            file.write(etree.tostring(measures_set, pretty_print=True).decode('utf-8'))
    except IOError:
        print('Error while writing file')
        exit(1)


def change_Ori(initial_pictures, final_pictures, ori_folder_path):
    """
    Changes all the files of an Ori- folder from MicMac, in the way that every reference to initial pictures
    is replaced by reference to final_pictures
    WARNING this will totally modify the folder without backup of the initial one, think about make a copy first
    :param initial_pictures: list of initial pictures to be replaced, in the same order as the final one
    :param final_pictures: list of initial pictures to be replaced, in the same order as the final one
    :param ori_folder_path: path of the orientation folder (name beginning with Ori- )
    """
    if ori_folder_path[-1] != '/': ori_folder_path += "/"
    if ori_folder_path.split('/')[-2][0:4] != "Ori-":
        print("Ori path is not valid : {}\nYou need to enter the path to the Ori-folder ".format(ori_folder_path))
        exit(1)
    elif len(initial_pictures) != len(final_pictures):
        print("List of input and output pictures must have the same size")
        exit(1)
    nb_pictures = len(initial_pictures)


    write_SEL_Xml(ori_folder_path + "FileImSel.xml", final_pictures)
    with open(ori_folder_path + 'Residus.xml', 'r') as file:
        filedata = file.read()
    for i in range(nb_pictures):
        # Replace the target string
        filedata = filedata.replace(initial_pictures[i], final_pictures[i])
    # Write the file out again
    with open(ori_folder_path + 'Residus.xml', 'w') as file:
        file.write(filedata)


    for j in range(nb_pictures):
        if os.path.exists(ori_folder_path + 'ImSec-{}.xml'.format(initial_pictures[j])):
            # Read in the file ImSec
            with open(ori_folder_path + 'ImSec-{}.xml'.format(initial_pictures[j]), 'r') as file:
                filedata = file.read()
            os.remove(ori_folder_path + 'ImSec-{}.xml'.format(initial_pictures[j]))
            for i in range(nb_pictures):
                # Replace the target string
                filedata = filedata.replace(initial_pictures[i], final_pictures[i])
            # Write the file out again
            with open(ori_folder_path + 'ImSec-{}.xml'.format(final_pictures[j]), 'w') as file:
                file.write(filedata)

        # rename Orientation files
        if os.path.exists(ori_folder_path + 'Orientation-{}.xml'.format(initial_pictures[j])):
            os.rename(ori_folder_path + 'Orientation-{}.xml'.format(initial_pictures[j]),
                      ori_folder_path + 'Orientation-{}.xml'.format(final_pictures[j]))

    with open(ori_folder_path + "log.txt",'w') as log:
        log.write("This orientation was not calculated by MicMac with these pictures\n\n")
        log.write("The names of pictures were just changed \n\n")
        for i in range(nb_pictures):
            log.write("{} was replaced by {}\n".format(initial_pictures[i], final_pictures[i]))

def write_SEL_Xml(Xml_path, picture_list):
    root = etree.Element('ListOfName')
    for img in picture_list:
        name = etree.SubElement(root, 'Name')
        name.text = str(img)
    try:
        # We open the file for writing
        with open(Xml_path, 'w') as file:
            # Header
            file.write('<?xml version="1.0" encoding="UTF_8"?>\n')
            # Writing all the text we created
            file.write(etree.tostring(root, pretty_print=True).decode('utf-8'))
    except IOError:
        print('Error while writing file')
        exit(1)
def change_xml(initial_pictures, final_pictures, xml_path):
    nb_pictures = len(initial_pictures)
    # Read in the file ImSec
    with open(xml_path, 'r') as file:
        filedata = file.read()
        print("ici")
    for i in range(nb_pictures):
        # Replace the target string
        print("remplacement de " + initial_pictures[i]  + " par " + final_pictures[i])
        filedata = filedata.replace(initial_pictures[i], final_pictures[i])
    # Write the file out again
    with open(xml_path, 'w') as file:
        file.write(filedata)


if __name__ == "__main__":
    liste_mesures = [['DSC00047.JPG', [['1', '5155.32345161082321 1709.62885559043229']]],
                     ['DSC00048.JPG', [['1', '5223.24245336298645 1654.30485908846413']]],
                     ['DSC00049.JPG', [['1', '5225.28907384436934 1935.98648985141676']]],
                     ['DSC00050.JPG', []]]

    # write_S2D_xmlfile(liste_mesures, 'Appuis_fictifs-S2D.xml')

    liste_points3D = [['1', "-23.4605861800590318 1.71111440194407338 26.4778679705422384", "1 1 1"],
                      ['1', "15.9331147514487199 -5.33682558320814415 102.277413480224084"]]

    # write_S3D_xmlfile(liste_points3D, 'Appuis_fictifs-S3D.xml')
    change_xml(["DSC00859.JPG", "DSC01960.JPG", "DSC03475.JPG"], ["pattate", "frite", "etc"],
               "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/TMP_MicMac_2018-6-11_17-16/Mesures_Appuis-S2D.xml")
