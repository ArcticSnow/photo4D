# coding :utf8

from lxml import etree
import os
import cv2 as cv


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
        exit(1)


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
        exit(1)
    if output == "":
        output = '.'.join(tif_mask.split('.')[:-1]) + ".xml"
    elif output.split('.')[-1] != "xml":
        print("Wrong output path " + output + "\n Must be a .xml file")
        exit(1)

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
    # some checks
    if ori_folder_path[-1] != '/': ori_folder_path += "/"
    if ori_folder_path.split('/')[-2][0:4] != "Ori-":
        print("Ori path is not valid : {}\nYou need to enter the path to the Ori-folder ".format(ori_folder_path))
        exit(1)
    elif len(initial_pictures) != len(final_pictures):
        print("List of input and output pictures must have the same size")
        exit(1)
    nb_pictures = len(initial_pictures)

    # change orientation files
    for j in range(nb_pictures):
        # rename Orientation files
        if os.path.exists(ori_folder_path + 'Orientation-{}.xml'.format(initial_pictures[j])):
            os.rename(ori_folder_path + 'Orientation-{}.xml'.format(initial_pictures[j]),
                      ori_folder_path + 'Orientation-{}.xml'.format(final_pictures[j]))

    # write a short summary
    with open(ori_folder_path + "log.txt", 'w') as log:
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
        exit(1)
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
    dico = {
        'DSC02701.JPG': {'B1': (2559.8758959104671, 1950.4846272277919), 'B2': (867.56902578766653, 1147.3817668754982),
                         'GCP13': (1678.8519974712274, 1275.676695894357),
                         'GCP17': (907.82667677805, 1195.7559666697266),
                         'GCP18': (2539.4998868108223, 1312.4937349209911),
                         'GCP21': (2951.9539767813317, 1285.130536156822),
                         'GCP28': (4298.8434223717013, 1295.4885053562984),
                         'GCP30': (3751.6863206530279, 1341.7791227136113),
                         'GCP34': (3778.9629789089176, 1437.1090449994822),
                         'GCP4': (4952.0214442997867, 1383.5322719261758),
                         'GCP6': (3101.4399888875259, 1678.1009608833151),
                         'GCP7bis': (2784.6166419621541, 1720.5198165031647)},
        'DSC02749.JPG': {'B1': (2560.1488959104672, 1948.2676272277922), 'B2': (871.67167578766657, 1144.0923668754981),
                         'GCP13': (1678.8709974712274, 1272.117695894357),
                         'GCP17': (887.84417677805004, 1198.1620666697265),
                         'GCP18': (2539.5868868108223, 1309.0787349209911),
                         'GCP21': (2952.1569767813317, 1281.804536156822),
                         'GCP28': (4342.5644223717018, 1310.8564053562984),
                         'GCP30': (3751.5394206530277, 1338.3911227136111),
                         'GCP34': (3778.9059289089173, 1433.7035949994822),
                         'GCP4': (4952.0549442997872, 1380.8317719261759),
                         'GCP6': (3101.3619888875264, 1674.854960883315),
                         'GCP7bis': (2798.9626419621541, 1699.7008165031646),
                         'GCP8': (2550.0774843272447, 1623.6907382928448)}}

    write_S2D_xmlfile(dico, 'mocked_gcp-S2D.xml')

    liste_points3D = [['1', "-23.4605861800590318 1.71111440194407338 26.4778679705422384", "1 1 1"],
                      ['1', "15.9331147514487199 -5.33682558320814415 102.277413480224084"]]
