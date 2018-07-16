# coding : uft8
import time
import os
from WriteMicMacFiles import ReadXml as rxml
import cv2 as cv
import numpy as np
from pictures_process.Handle_Exif import load_date


def init_Points(folder_path, image, points=None,sample_path=""):
    """

    :param folder_path:
    :param image:
    :param points: name of MicMac xml s2D file, or number of points
    :return:
    """
    if points is None:
        xml_s2D = pick_points(0, folder_path, image_path=image)
        list_pos = pos_from_xml_s2D(xml_s2D, folder_path)
    elif type(points)==int:
        xml_s2D = pick_points(points, folder_path, image_path=image)
        list_pos = pos_from_xml_s2D(xml_s2D, folder_path)
    elif type(points) == str:
        xml_s2D = points
        try:
            list_pos = pos_from_xml_s2D(xml_s2D, folder_path)
        except OSError:
            print("The xml file don't exist or isn't valid")
            ans = input("Do you want to pick manually the points ? (y/n) :  ")
            if ans == 'y':
                xml_s2D = pick_points(0, folder_path, image_path=image)
                list_pos = pos_from_xml_s2D(xml_s2D, folder_path)
            else:
                exit(1)
    else:
        raise TypeError ("Param points must be either string or integer")

    create_samples(list_pos, image, image_path=folder_path,sample_path=sample_path)
    dist_matrix = create_dist_matrix(list_pos)
    return list_pos, dist_matrix

def pick_points(nb_points, folder_path, image_path="", xml_name="selection", orientation='NONE'):
    """
    use MicMac to write the position of points in one or many images
    :param nb_points: number of point to measure. (You can still add points within the MicMac pointing interface)
    :param folder_path: folder where the picture(s) is/are
    :param image_path:
    :param xml_name: name of the xml that will store position information. MicMac will create 2 xml for this purpose,
    xml_name-S2D.xml and xml_name-S3D.xml. Note that it will note erase an existing file but instead rename the new files
    adding 'bis'
    :param orientation Orientation of the images, just necessary to compute 3D position
    :return: name of xml file where positions are saved
    """
    # todo verifier un tas de trucs pour montrer que le fichier est valide
    real_xml_name = xml_name + "-S2D.xml"
    while os.path.exists(folder_path + real_xml_name):
        xml_name += "bis"
        real_xml_name = xml_name + "-S2D.xml"

    os.chdir(folder_path)
    file = open("points.txt", 'w')
    for i in range(nb_points):
        file.write(str(i + 1) + '\n')
    file.close()
    command = 'mm3d SaisieAppuisInitQT "{}" {} {} {}'.format(image_path, orientation, 'points.txt',
                                                             xml_name + '.xml')
    os.system(command)
    return real_xml_name


def pos_from_xml_s2D(xml_path, one_image=True):
    """
    BEWARE ! This function is not finalised at all and will crash for many reasons
    :param xmlpath:
    :param one_image True if the measures are taken from only one image
    :return: list of the measures of points
    """

    list_img_measures = rxml.read_S2D_xmlfile(xml_path)
    if one_image:
        if len(list_img_measures) != 1:
            print("ERROR More than one image in xmlfile")
            return None,list_img_measures
        else:
            pos=[]
            for point in list_img_measures[0][1]:
                meas = point[1].split(' ')
                pos.append([float(meas[0]), float(meas[1])])
            print(pos)
            print(" List of point measured : " + str(list_img_measures))
            return pos,list_img_measures
    else:
        print("didn't know if we will need it")
    print(" List of point measured : " + str(list_img_measures))
    return list_img_measures


pos = [[958, 1719], [2678, 1276], [696, 1406], [4675, 1753], [3560, 2354]]


def create_samples(list_pos, image, size_sample=10, image_path="", sample_path=""):
    """

    :param list_pos:
    :param image:
    :param taille_sample: in percentage of the image size
    :return:
    """
    img = cv.imread(image_path + image)
    img_size = img.shape
    report = "Automatic creation of samples pictures from " + image +"\n\n"
    report += "Samples are taken on " + str(load_date(image_path+image) + "\n")
    # create the file for samples
    if sample_path == "":
        sample_path = image_path + "Samples/"
    if not os.path.exists(sample_path):  # Tu remplaces chemin par le chemin complet
        os.mkdir(sample_path)
    id = 1
    for pos in list_pos:
        side = (img_size[0] * (size_sample / 100)) / 2

        minx, maxx, miny, maxy = int(pos[1] - side), int(pos[1] + side), int(pos[0] - side), int(pos[0] + side)
        sample = img[minx:maxx, miny:maxy, :]

        cv.imwrite(sample_path + 'sample_' + str(id) + '.jpg', sample)
        report+="image {} ({},{}) for point situated at  "
        id += 1

    with open("creation_samples.txt",'w') as log:
        log.write(report)


def create_dist_matrix(samples_position_ini):
    """
    Compute the distance matrix between samples (in pixels)
    :param samples_position_ini: list like [[posX_sample, posY_sample1], [posX_sample2, posY_sample2],...]
    :return: distance matrix, the index corresponds to the id of the sample
    """
    input_type = type(samples_position_ini)
    if input_type == list:
        l = len(samples_position_ini)
    elif input_type == np.ndarray:
        l = samples_position_ini.shape[0]
    else:
        raise TypeError("Input type must be list or numpy.ndarray not {}".format(input_type))
    dist = np.zeros((l, l))
    for i in range(l):
        for j in range(l):
            if j != i:
                diffX = (samples_position_ini[i][0] - samples_position_ini[j][0]) ** 2
                diffY = (samples_position_ini[i][1] - samples_position_ini[j][1]) ** 2
                dist[i, j] = np.sqrt(diffX + diffY)
            else:
                dist[i, j] = 0
    return dist


if __name__ == "__main__":
    tic = time.time()
    # name = xml_S2D = pick_points(4,
    #                             "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam1/")
    # list_pos = pos_from_xml_s2D(name, "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam1/")
    #create_samples([[1938.1980216319232, 1850.6902254411275], [1050.409617695594, 2598.9942810913385],
    #                [1336.717135650592, 3057.0991130637562], [1412.0974834166875, 1287.109263516806]],
    #               'DSC00916_11h30.JPG',
    #               image_path='C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam1/')

    pos_from_xml_s2D("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Mesures_Appuis-S2D.xml",one_image=True)
    #init_Points("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/","DSC00859.JPG",
    #            "Mesures_Appuis-S2D.xml",sample_path="C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samplesbis/")

    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
