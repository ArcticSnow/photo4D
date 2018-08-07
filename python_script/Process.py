# coding : uft8
import numpy as np
import os
from WriteMicMacFiles import WriteXml as wxml
from WriteMicMacFiles import ReadXml as rxml
from pictures_process.Handle_Exif import load_date, load_lum
from pictures_process.Stats import blurr
from shutil import copyfile, rmtree, copytree
import time
from pictures_process import Handle_CLAHE as cl


def sort_pictures(folder_path_list, output_folder, ext="jpg", time=600):
    """
    Regroup pictures from different folders if they are taken within time seconds of interval.
    Result is stored in an array/file,
    :param folder_path_list:
    :param output_folder:
    :param ext:
    :param time: interval in seconds, with corresponds to |time1 - time2|
    :return:
    """
    print("Collecting files\n..........................................")
    ext = ext.lower()
    list = []  # containing an image_date_list for each folder
    for folder_path in folder_path_list:
        image_date_list = []
        flist = os.listdir(folder_path)
        for filename in flist:
            try:
                if filename.split(".")[-1].lower() == ext:
                    image_date_list.append((filename, load_date(folder_path + filename)))
            except IndexError:
                pass
        list.append(image_date_list)
    if len(list) < 1:
        print("WARNING not enough folder\nTwo or more folders are needed to sort files")
        return None
    elif [] in list:
        print("WARNING No image found in One or many folder(s)")
        return None

    sorted_pictures = []
    print("Checking dates\n..........................................")
    with open("linkedFiles.txt", 'w') as f:
        f.write("# Pictures taken within {} of interval\n".format(time))

    good, bad = 0, 0  # counters for correct and wrong sets
    # loop on the image of the first folder
    for image_ref in list[0]:
        date_ref = image_ref[1]
        pic_group = np.empty(len(list) + 1, dtype=object)
        pic_group[0] = False  # the pic_group[0] is a boolean, True if all a picture is found in every folder
        pic_group[1] = image_ref[0]
        # for_file = [image_ref[0]]  # list of the images taken within the interval

        # check for pictures taken whithin the interval
        for j in range(1, len(list)):
            folder = list[j]  # list of the (filename,date) of one folder
            i, found = 0, False
            while not found and i < len(folder):  # todo retirer les images ?
                date_var = folder[i][1]
                diff = abs(date_ref - date_var)
                if diff.days * 86400 + diff.seconds < time:  # if the two pictures are taken within 10 minutes
                    found = True
                    pic_group[j + 1] = folder[i][0]
                i += 1

        if None not in pic_group:
            good += 1
            pic_group[0] = True
            print("Pictures found in every folder corresponding to the time of " + pic_group[1] + "\n")
            sorted_pictures.append(pic_group)
            with open(output_folder + "linkedFiles.txt", 'a') as f:
                f.write(str(pic_group[0]) + "," + ",".join(pic_group[1:]) + "\n")
        else:
            bad += 1
            print("Missing picture(s) corresponding to the time of " + pic_group[1] + "\n")

    end_str = "{} good set of pictures found, {} uncomplete sets, with a total of {} sets".format(good, bad, good + bad)
    print(end_str)
    with open(output_folder + "linkedFiles.txt", 'a') as f:
        f.write(end_str)
    return sorted_pictures


def check_pictures(main_folder_path, secondary_folder_list, output_folder, pictures_array, lum_inf, blur_inf,
                   replace_log=True):
    """
    This function is supposed to be called after sort_pictures, as it uses the kind of array created by sort_pictures,
    which could be either collected from the return value of the function, or the file "linkedFiles.txt" created in
    the main folder
    It will filter pictures in which brightness is inferior to lum_inf and the "blur" (variance of Laplacian) is
    inferior to blur_min
    :param main_folder_path:
    :param secondary_folder_list:
    :param pictures_array:
    :param lum_inf:
    :param blur_min:
    :return: same array, but some booleans will be set to False
    """
    print("Checking pictures\n..........................................")

    if replace_log:
        log_name = "linkedFiles.txt"
    else:
        log_name = "linkedFiles_checked.txt"
    with open(output_folder + log_name, 'w') as f:
        f.write(
            "# Pictures filtered with a minimum value of {} for brightness, {} for the variance of Laplacian\n".format(
                lum_inf, blur_inf))

    good, bad = 0, 0
    I, J = pictures_array.shape
    for i in range(I):
        if pictures_array[i, 0]:
            min_lum = 9999
            min_blur = 9999
            for j in range(1, J):
                path = main_folder_path + secondary_folder_list[j - 1] + pictures_array[i, j]
                lum = load_lum(path)

                if lum < min_lum:
                    min_lum = lum
                blur = blurr(path, 3)
                if blur < min_blur:
                    min_blur = blur

            if min_lum < lum_inf or min_blur < blur_inf:
                pictures_array[i, 0] = False
                bad += 1
            else:
                good += 1

    with open(output_folder + log_name, 'a') as f:
        for line in pictures_array:
            f.write(str(line[0]) + "," + ",".join(line[1:]) + "\n")
        f.write(
            "# {} good set of pictures found, {} rejected sets, with a total of {} sets".format(good, bad, good + bad))
    return pictures_array


def pictures_array_from_file(filepath):
    """
    Could be way more efficient ! And does not handle any error for the moment
    :param filepath:
    :return:
    """
    print("Retrieving data from file " + filepath + "\n.......................................")
    all_lines = []
    with open(filepath, 'r') as file:
        for line in file.readlines():
            if line[0] != "#":
                list_temp = line.split(',')
                length = len(list_temp)
                array_line = np.empty(length, dtype=object)
                if list_temp[0].rstrip(" ").lower() == "true":
                    array_line[0] = True
                else:
                    array_line[0] = False
                for i in range(1, length):
                    array_line[i] = list_temp[i].rstrip('\n')
                all_lines.append(array_line)
        print("Done")
        return np.array(all_lines)


def copy_and_process(filepath_list, output_folder, tmp_folder_name="TMP_MicMac", ply_name="", clahe=False, resol=-1,
                     distortion_model="RadialStd", InCal=None, InOri=None, abs_coord_gcp=None,
                     img_coord_gcp =None, pictures_Ori=None, re_estimate=False,
                     master_img=None, masqpath_list=None, DefCor=0.0, shift=None, delete_temp=True):
    """
    copy needed files and process micmac for a set of given pictures (filepath_list)
    It is advised to give only absolute path in parameters


    :param filepath_list: list of absolute path of pictures to process
    :param output_folder: directory for saving results and process pictures
    :param tmp_folder_name: name of the temporary folder where processing pictures
            date is automatically added to the name
    :param ply_name: first part of the name of the output point-cloud, date and extension will be added automatically
    :param clahe: if True, apply a "contrast limited adaptive histogram equalization" on the pictures before processing

    MicMac parameters: (see more documentation on official github and wiki (hopefully))
    :param resol: resolution for the research of TiePoints todo demander à luc pour les racourcis
            -1 stands for full resolution
    :param distortion_model: distortion model used in Tapas
            can be "Fraser", "FraserBasic", "RadialStd", "RadialBasic" and more
    :param InCal: path to initial calibration folder (from MicMac), None if no initial calibration used
    :param InOri: path to initial orientation folder (from MicMac), None if no initial orientation used
    :param pictures_Ori: pictures of initial calibration, in the same order as secondary folder list
    :param re_estimate: -only if there is an initial orientation- if True, re estimate the orientation
    :param abs_coord_gcp: xml file containing absolute coordinates of GCPs, file from the MicMac command GCPConvert
    :param img_coord_gcp: xml file containing image coordinates of the GCPs, result one of the SaisieAppuis command in MicMac

    :param master_img:
    :param masqpath_list: list of mask, each mask file in this list correspond to the picture of the same indice in filepath list
            list of path to .tif files from MicMac
    :param DefCor:
    :param shift: shift for saving ply (if numbers are too big for 32 bit ply) [shiftE, shiftN, shiftZ]
    :param delete_temp: if False the temporary folder will not be deleted, but beware, MicMac files are quite heavy
    :return:
    """
    ####################################################################################################################
    # checking path and parameters :

    # check output folder
    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # check processing folder, name it according to the date of the first picture
    date = load_date(filepath_list[0])
    if date is not None:
        date_str = date.strftime("%Y_%m_%d-%H_%M")
        folder_path = output_folder + tmp_folder_name + "_" + date_str + "/"
    else:
        folder_path = output_folder + tmp_folder_name + filepath_list[0].split('/')[-1]
        date_str = filepath_list[0].split('/')[-1]  # if we can't find a date, put the name of the first picture...
    if not os.path.exists(folder_path): os.mkdir(folder_path)

    # check masks
    if masqpath_list is not None:
        if type(masqpath_list) != list or len(masqpath_list) != len(filepath_list):
            print("Invalid value {} for parameter masqpath_list".format(masqpath_list))
            print("Mask ignored")
            masqpath_list = None

    ####################################################################################################################
    # copy pictures into the temporary folder
    pictures_pattern = "("  # pattern of pictures telling MicMac which one to process
    for i in range(len(filepath_list)):

        filepath = filepath_list[i]
        filename = filepath.split("/")[-1]
        pictures_pattern += filename + "|"

        if not clahe:
            copyfile(filepath, folder_path + filename)
        else:
            # apply the CLAHE method, used for the orientation
            cl.process_clahe(filepath
                                  , 8, out_path=folder_path + filename, grey=True)


        # copy mask corresponding to the picture
        if masqpath_list is not None:
            # copy the mask and gave it the default name of a mask created by MicMac
            copyfile(masqpath_list[i], folder_path + '.'.join(filename.split('.')[:-1]) + "_Masq.tif")
            # MicMac needs a xml file with the tiff file, if it doesn't exist, it is created
            if os.path.exists('.'.join(masqpath_list[i].split('.')[:-1]) + '.xml'):
                copyfile('.'.join(masqpath_list[i].split('.')[:-1]) + '.xml',
                         folder_path + '.'.join(filename.split('.')[:-1]) + "_Masq.xml")
            else:
                wxml.write_masq_xml(masqpath_list[i], folder_path + '.'.join(filename.split('.')[:-1]) + "_Masq.xml")
    pictures_pattern = pictures_pattern[:-1] + ")"

    ####################################################################################################################
    # detection of Tie points
    os.chdir(folder_path)
    # first detection of Tie points with the option ExpTxt=1 to make a report with txt
    command = 'mm3d Tapioca All "{}" {} ExpTxt=1'.format(pictures_pattern, resol)
    print("\033[0;33" + command + "\033[0m")
    os.system(command)
    # second detection of Tie points at a lower resolution, without ExpTxt=1, just to avoid a stupid MicMac bug in C3DC
    # MicMac will just convert txt to binary
    command = 'mm3d Tapioca All "{}" {}'.format(pictures_pattern, resol)
    print("\033[0;33" + command + "\033[0m")
    os.system(command)

    # Orientation of cameras

    # list picture names, used to transform orientation and calibration
    final_pictures = []
    for filepath in filepath_list:
        final_pictures.append(filepath.split("/")[-1])

    ori = distortion_model  # name of orientation, it is the distortion model by default
    # if there is an initial orientation
    if InOri is not None:

        if InOri[-1] != "/": InOri += "/"
        # copy the initial orientation file
        new_Ori_path = folder_path + InOri.split('/')[-2] + "/"
        if not os.path.exists(new_Ori_path):
            copytree(InOri, new_Ori_path)  # We assume that the path is correctly written ( "/Root/folder/Ori-Truc/")
        # swap pictures names to mock MicMac computed orientation files
        wxml.change_Ori(pictures_Ori, final_pictures, new_Ori_path)
        # if re_estimate, MicMac recompute the orientation todo verifier l'utilite

        if re_estimate:
            ori += "_R"
            command = 'echo | mm3d Tapas {} "{}" InOri={} Out={}'.format(distortion_model, pictures_pattern,
                                                                  InOri.split('/')[-2], ori)
            print("\033[0;33" + command + "\033[0m")
            os.system(command)
        else:
            ori = InOri.split('/')[-2]  # name of the new ori is the same as the initial one

    # if there is no initial orientation but an initial calibration
    # it assumed that the calibration is the same for every picture
    elif InCal is not None:
        if InCal[-1] != "/": InCal += "/"
        new_Cal_path = folder_path + InCal.split('/')[-2] + "/"
        if not os.path.exists(new_Cal_path):
            copytree(InCal, new_Cal_path)  # We assume that the path is correctly written ( "/fgg/Ori-Truc/")
        command = 'echo | mm3d Tapas {} "{}" InCal={}'.format(distortion_model, pictures_pattern,
                                                              InCal.split('/')[-2])
        print("\033[0;33" + command + "\033[0m")
        os.system(command)

    # if no initial parameters, classic orientation computation
    else:
        command = 'echo | mm3d Tapas {} "{}"'.format(distortion_model, pictures_pattern)
        print("\033[0;33" + command + "\033[0m")
        os.system(command)


    # if GCP are provided for Bascule (Absolute orientation)
    if abs_coord_gcp is not None and img_coord_gcp is not None:
        # copy GCP absolute coordinates
        gcp_name = abs_coord_gcp.split('/')[-1]
        if abs_coord_gcp != folder_path + gcp_name:
            copyfile(abs_coord_gcp, folder_path + gcp_name)
        # create S2D xml file with images positions of gcp
        wxml.write_S2D_xmlfile(img_coord_gcp, folder_path + "GCP-S2D.xml")

        command = 'echo | mm3d GCPBascule "{}" {} Bascule {} {}'.format(pictures_pattern,
                                                                      ori,
                                                                      gcp_name,
                                                                      "GCP-S2D.xml")
        print(command)
        os.system(command)
        ori = 'Bascule'


    # dense correlation

    if clahe:
        # clahe images were used for orientation, but we need JPG for dense correlation
        for i in range(len(filepath_list)):
            filepath = filepath_list[i]
            filename = filepath.split("/")[-1]
            copyfile(filepath, folder_path + filename)

    ply_name += date_str + ".ply"
    command = 'echo | mm3d Malt GeomImage "{}" {} Master={} DefCor={} MasqIm=Masq'.format(pictures_pattern, ori,
                                                                                          master_img, DefCor)
    print("\033[0;33" + command + "\033[0m")
    os.system(command)

    # creation of the final point cloud file todo la derniere etape est tjrs 8 ?

    # create the point cloud
    if shift is None:
        command = 'echo | mm3d Nuage2Ply MM-Malt-Img-{}/NuageImProf_STD-MALT_Etape_8.xml Attr={} Out={}'.format(
            '.'.join(master_img.split('.')[:-1]), master_img, ply_name)
    else:
        command = 'echo | mm3d Nuage2Ply MM-Malt-Img-{}/NuageImProf_STD-MALT_Etape_8.xml Attr={} Out={} Offs={}'.format(
            '.'.join(master_img.split('.')[:-1]), master_img, ply_name, shift)

    print("\033[0;33" + command + "\033[0m")
    os.system(command)

    os.system('exit')

    ####################################################################################################################
    # Make stats about the reconstruction
    with open(date_str + '_recap.txt', 'w') as recap:
        recap.write("Summary of MicMac 3D reconstruction for " + date_str + "\n")
        string = "\nNumber of Tie Points : "
        df, tot = rxml.count_tiepoints_from_txt(folder_path)
        string += str(tot) + "\n\nFiles used :\n"
        for i in df.index.values:
            string += "  - {} taken on {} : {} tie points\n".format(i, load_date(folder_path + i), df.loc())
        recap.write(string)

        if os.path.exists(folder_path + ply_name):
            copyfile(folder_path + ply_name, output_folder + ply_name)
            recap.write("\nStatus  : Success\n")
        else:
            recap.write("\nStatus  : Failure\n")

        if InOri is not None:
            recap.write("\n Initial orientation used  : " + InOri + "\n")
        elif InCal is not None:
            recap.write("\n Initial calibration used  : " + InCal + "\n")

        # write a .txt with residuals
        if ori[:4] == "Ori-":
            ori_path = folder_path + ori + "/"
        else:
            ori_path = folder_path + "Ori-" + ori + "/"
        if os.path.exists(ori_path):  # if Tapas command worked
            dict = rxml.residual2txt(ori_path)
            recap.write("\nNumber of iterations : {}   Average Residual : {}\n".format(dict['nb_iters'], "%.4f" % dict[
                'AverageResidual']))
            recap.write("\nName           Residual     PercOk        Number of Tie Points\n")
            for i in df.index.values:
                recap.write(
                    "{} : {}       {}       {}\n".format(i, "%.4f" % float(dict[i][0]), "%.4f" % float(dict[i][1]),
                                                         dict[i][2]))
    copyfile(folder_path + date_str + '_recap.txt', output_folder + date_str + '_recap.txt')

    # try to delete temporary folder
    if delete_temp:
        try:
            rmtree(folder_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print("Permission Denied, cannot delete " + folder_path)
        except OSError:
            pass
    else:
        # only delete some heavy micmac files
        try:
            rmtree(folder_path + "Pastis")
            rmtree(folder_path + "Tmp-MM-Dir")
            rmtree(folder_path + "Pyram")
        except:
            pass


def process_from_array(main_folder_path, secondary_folder_list, pictures_array, InCal=None, InOri=None,
                       pictures_ori=None, gcp=None, gcp_S2D=None, pictures_gps=None, output_folder="",
                       clahe=False, resol=-1,
                       distortion_model="RadialStd",
                       re_estimate=False, master_folder=0, masq2D=None, DefCor=0.0, shift=None, delete_temp=True):
    """
    Do the 3D reconstruction of pictures using MicMac

    Mandatory arguments :
    :param main_folder_path: path of the folder containing the camera folders, results are saved here by default
    :param secondary_folder_list: list of path to picture folders
            pictures are stored in a folder per camera
    :param pictures_array: array containing names of pictures to process
            each row is considered as a set, and pictures names must be in the same order as secondary_folder_list
    Reconstruction argument :
    :param resol: resolution for the research of TiePoints todo demander à luc pour les racourcis
            -1 stands for full resolution
    :param distortion_model: distortion model used in Tapas
            can be "Fraser", "FraserBasic", "RadialStd", "RadialBasic" and more
    :param InCal: path to initial calibration folder (from MicMac), None if no initial calibration used
    :param InOri: path to initial orientation folder (from MicMac), None if no initial orientation used
    :param pictures_Ori: pictures of initial calibration, in the same order as secondary folder list
             None if the pictures are in pictures_array, they will be automatically detected
    :param re_estimate: -only if there is an initial orientation- if True, re estimate the orientation
    :param gcp: .xml file containing coordinates of GCPs, file from the MicMac command GCPConvert
    :param gcp_S2D: xml file containing image coordinates of the GCPs, result one of the SaisieAppuis command in MicMac
    :param pictures_gps: pictures used in GCP_S2D, in the same order as secondary folder list
    :param output_folder:
    :param master_folder: list indice of the folder where "master images" for Malt reconstruction are stored
            by defaut it is the first folder
    :param masq2D:
    :param shift: shift for saving ply (if numbers are too big for 32 bit ply) [shiftE, shiftN, shiftZ]
    :param delete_temp: if False the temporary folder will not be deleted, but beware, MicMac files are quite heavy
    :return:
    """
    # checking parameters :

    # it is assumed that all pictures have the same extension
    ext = pictures_array[0, 1].split('.')[-1].lower()

    if type(master_folder) != int or not (0 <= master_folder < len(secondary_folder_list)):
        print("Invalid value {} for parameter master folder, value set to 0".format(master_folder))
        print("must be one indice of the array secondary_folder_list")
        master_folder = 0

    # if pictures_Ori is not provided but there is an initial orientation, retrieve it from pictures array
    if InOri is not None and pictures_ori is None:
        # find the name of one picture used in InOri, using Orientation files
        flist = os.listdir(InOri)
        image = ""
        for file in flist:
            if len(file) > 12 and file[:12] == "Orientation-":
                image = file[12:-4]  # todo qu'est ce que c'est moche
                break
        # find the row of this picture in pictures_array and use it as pictures_ori
        nb_sets, nb_pics = pictures_array.shape
        i = 0
        found = False
        while i < nb_sets and not found:
            j = 1
            while j < nb_pics and not found:
                if pictures_array[i, j] == image:
                    found = True
                j += 1
            i += 1
        if i == nb_sets - 1 and not found:
            raise ValueError("Cannot find initial orientation pictures in pictures array\n"
                             "Please fill parameter pictures_ori")
        pictures_ori = pictures_array[i - 1, 1:]

    if gcp is not None and gcp_S2D is not None:
        if gcp[-4:] != ".xml":
            print("WARNING Param gcp must be an xml file from the micmac function GCPConvert")
            exit(1)
        if not os.path.exists(gcp):
            print("WARNING Cannot open gcp file at " + gcp)
            exit(1)
        # retrieve gcp measures for all image in a dictionary
        all_gcp = rxml.read_S2D_xmlfile(gcp_S2D)



    if masq2D is not None:
        print("Collecting mask path")
        masqpath_list = ['' for i in range(pictures_array.shape[1] - 1)]
        flist = os.listdir(masq2D)
        for file in flist:
            if file[-9:] == "_Masq.tif":
                I, J = pictures_array.shape
                i = 0
                found = False
                while i < I and not found:
                    j = 1
                    while j < J and not found:

                        if pictures_array[i, j].lower() == file[:-9].lower() + '.' + ext:
                            masqpath_list[j - 1] = masq2D + file
                            found = True
                        j += 1
                    i += 1
        print(masqpath_list)
        if '' in masqpath_list:
            print("Cannot find pictures corresponding to mask in pictures array")
            exit(1)
    else:
        masqpath_list = None

    # launch the process
    for line in pictures_array:

        if line[0]:  # line[0] is a boolean, True if the set is correct
            list_path = []
            for i in range(1, len(secondary_folder_list) + 1):
                list_path.append(main_folder_path + secondary_folder_list[i - 1] + str(line[i]))
            # determining which of the pictures is the master image for dense correlation (Malt)
            master_img = line[master_folder + 1]
            date = load_date(list_path[0])
            h = date.hour

            if h == 11:

                info = "Processing pictures taken on " + str(date) + ":\n  "
                for img in line[1:]:
                    info += img + "  "

                print(info)

                if gcp_S2D is not None and gcp is not None:
                    # create a dictionary with gcp image coordinates of this picture set
                    try:
                        print(line[1:])
                        print(all_gcp)
                        set_gcp = dict([(k, all_gcp.get(k)) for k in line[1:]])
                        print(set_gcp)
                    except AttributeError:
                        print("Couldn't find gcp measures for this set of pictures in S2D xml\nSet ignored")
                        continue
                else:
                    set_gcp = None

                copy_and_process(
                    list_path,
                    output_folder=output_folder, InCal=InCal, InOri=InOri, pictures_Ori=pictures_ori, abs_coord_gcp=gcp,
                    img_coord_gcp=set_gcp, re_estimate=re_estimate,
                    master_img=master_img, masqpath_list=masqpath_list,
                    resol=resol, distortion_model=distortion_model,
                    DefCor=DefCor, clahe=clahe, shift=shift, delete_temp=delete_temp)


if __name__ == "__main__":
    tic = time.time()
    print("process launched")

    # main_GCP_estim("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/","DSC00918_11h30.JPG",points = 'selection-S2D.xml')
    # sort_pictures(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_ouest/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_mid/"])

    array = pictures_array_from_file(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/linkedFiles.txt")
    folders = ["cam_est/", "cam_ouest/", "cam_mid/"]
    main_folder_path = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/"
    output_folder = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Results/"
    masq2D = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Mask/"
    inori = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Ori-Fraser/"
    S2D = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/All_points-S2D.xml"
    truc = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/GCP/Pt_gps_gcp.xml"

    process_from_array(main_folder_path, folders, array,
                       output_folder=output_folder, resol=2000, master_folder=2,
                       masq2D=masq2D, DefCor=0.4, InOri=inori, re_estimate=True,
                       clahe=True, delete_temp=False, gcp_S2D= S2D, gcp=truc,
                       distortion_model="Fraser")
    # [410000, 6710000, 0]
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
