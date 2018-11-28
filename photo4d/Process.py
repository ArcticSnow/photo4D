# coding : uft8
import numpy as np
import os, time
from shutil import copyfile, rmtree, copytree
import photo4d.Image_utils as iu
import photo4d.XML_utils



from photo4d.Image_utils import load_date, load_lum, blurr, lum, process_clahe
from photo4d.Utils import exec_mm3d, pictures_array_from_file


def sort_pictures(folder_path_list, output_path, ext="jpg", time_interval=600):
    """
    Regroup pictures from different folders if they are taken within timeInterval seconds of interval.
    Result is stored in an array/file,
    :param folder_path_list: list of the path to folders containing pictures, each folder is for one camera
    :param output_path: path of the output .txt file containing picture sets
    :param ext: extension of the pictures
    :param time_interval: interval in seconds, with corresponds to the maximum time elapsed between the shooting of pics
    :return: array with the sorted pictures. For each set a boolean is added, always True, but can be modified later
    """
    print("\n Collecting files\n..........................................")
    # create a list containing image names and dates for each folder
    list = []
    for folder_path in folder_path_list:
        image_date_list = []
        flist = os.listdir(folder_path)
        for filename in flist:
            try:
                if filename.split(".")[-1].lower() == ext.lower():
                    image_date_list.append((filename, load_date(os.path.join(folder_path,filename))))
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
    print(" Checking dates\n..........................................")
    with open(output_path, 'w') as f:
        f.write("# Pictures taken within {} of interval\n".format(time_interval))

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
            while not found and i < len(folder):
                date_var = folder[i][1]
                diff = abs(date_ref - date_var)
                if diff.days * 86400 + diff.seconds < time_interval:  # if the two pictures are taken within 10 minutes
                    found = True
                    pic_group[j + 1] = folder[i][0]
                i += 1

        if None not in pic_group:
            good += 1
            pic_group[0] = True
            print(" Pictures found in every folder corresponding to the timeInterval of " + pic_group[1] + "\n")
            sorted_pictures.append(pic_group)
            with open(output_path, 'a') as f:
                f.write(str(pic_group[0]) + "," + ",".join(pic_group[1:]) + "\n")
        else:
            bad += 1
            print(" Missing picture(s) corresponding to the timeInterval of " + pic_group[1] + "\n")

    end_str = "# {} good set of pictures found, {} uncomplete sets, on a total of {} sets".format(good, bad, good + bad)
    print(end_str)
    with open(output_path, 'a') as f:
        f.write(end_str)
    return np.array(sorted_pictures)


def check_pictures(folder_list, output_path, pictures_array, lum_inf, blur_inf):
    """
    This function is supposed to be called after sort_pictures, as it uses the kind of array created by sort_pictures,
    which could be either collected from the return value of the function, or the file "linked_files.txt" created in
    the main folder
    It will filter pictures in which brightness is inferior to lum_inf and the "blur" (variance of Laplacian) is
    inferior to blur_min
    :param folder_list:
    :param output_path:
    :param pictures_array:
    :param lum_inf:
    :param blur_min:
    :return: same array, but some booleans will be set to False
    """
    print("\n Checking pictures\n..........................................")

    with open(output_path, 'w') as f:
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
                path = os.path.join(folder_list[j - 1],pictures_array[i, j])
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

    with open(output_path, 'a') as f:
        for line in pictures_array:
            f.write(str(line[0]) + "," + ",".join(line[1:]) + "\n")
        end_line = " {} good set of pictures found, {} rejected sets, on a total of {} sets".format(good, bad, good + bad)
        f.write("#" + end_line)
        print(end_line)
    return pictures_array


def copy_and_process(filepath_list, output_folder, tmp_folder_name="TMP_MicMac", ply_name="", clahe=False, tileGridSize_clahe=8, resol=-1,
    distortion_model="RadialStd", incal=None, inori=None, abs_coord_gcp=None,
    img_coord_gcp=None, pictures_ini=None, re_estimate=False,
    master_img=None, masqpath_list=None, DefCor=0.0, shift=None, delete_temp=True,
    display_micmac=True, GNSS_PRECISION=0.2, GCP_POINTING_PRECISION=5):
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
    :param incal: path to initial calibration folder (from MicMac), None if no initial calibration used
    :param inori: path to initial orientation folder (from MicMac), None if no initial orientation used
    :param pictures_ini: pictures of initial calibration, in the same order as secondary folder list
    :param re_estimate: -only if there is an initial orientation- if True, re estimate the orientation
    :param abs_coord_gcp: xml file containing absolute coordinates of GCPs, file from the MicMac command GCPConvert
    :param img_coord_gcp: xml file containing image coordinates of the GCPs, result one of the SaisieAppuis command in MicMac

    :param master_img:
    :param masqpath_list: list of mask, each mask file in this list correspond to the picture of the same indice in filepath list
            list of path to .tif files from MicMac
    :param DefCor:
    :param shift: shift for saving ply (if numbers are too big for 32 bit ply) [shiftE, shiftN, shiftZ]
    :param delete_temp: if False the temporary folder will not be deleted, but beware, MicMac files are quite heavy
    :param display_micmac: if False MicMac log will be hidden, may be useful as this may ba a bit messy sometimes
    :return:
    """
    # ==================================================================================================================
    # checking path and parameters :

    # check output folder
    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # check processing folder, name it according to the date of the first picture
    date = load_date(filepath_list[0])
    if date is not None:
        date_str = date.strftime("%Y_%m_%d-%H_%M")
        folder_path = os.path.join (output_folder,tmp_folder_name + "_" + date_str)
    else:
        folder_path = os.path.join(output_folder,tmp_folder_name + filepath_list[0].split('/')[-1])
        date_str = filepath_list[0].split('/')[-1]  # if we can't find a date, put the name of the first picture...
    if not os.path.exists(folder_path): os.mkdir(folder_path)

    # check masks
    if masqpath_list is not None:
        if type(masqpath_list) != list or len(masqpath_list) != len(filepath_list):
            print("Invalid value {} for parameter masqpath_list".format(masqpath_list))
            print("Mask ignored")
            masqpath_list = None

    # ==================================================================================================================
    # copy pictures into the temporary folder
    pictures_pattern = "("  # pattern of pictures telling MicMac which one to process
    for i in range(len(filepath_list)):

        filepath = filepath_list[i]
        filename = os.path.basename(filepath)
        pictures_pattern += filename + "|"

        if not clahe:
            copyfile(filepath, os.path.join(folder_path, filename))

        else:
            # apply the CLAHE method, used for the orientation
            process_clahe(filepath,
                tileGridSize_clahe, out_path=os.path.join(folder_path, filename), grey=True)

        # copy mask corresponding to the picture
        if masqpath_list is not None:
            # copy the mask and gave it the default name of a mask created by MicMac
            copyfile(masqpath_list[i], os.path.join(folder_path, '.'.join(filename.split('.')[:-1]) + "_Masq.tif"))
            # MicMac needs a xml file with the tiff file, if it doesn't exist, it is created
            if os.path.exists('.'.join(masqpath_list[i].split('.')[:-1]) + '.xml'):
                copyfile('.'.join(masqpath_list[i].split('.')[:-1]) + '.xml',
                         os.path.join(folder_path, '.'.join(filename.split('.')[:-1]) + "_Masq.xml"))
            else:
                XML_utils.write_masq_xml(masqpath_list[i], folder_path + '.'.join(filename.split('.')[:-1]) + "_Masq.xml")

    pictures_pattern = pictures_pattern[:-1] + ")"

    # launching MicMac reconstruction
    # ==================================================================================================================

    # detection of Tie points
    # ===================================================
    os.chdir(folder_path)
    print(folder_path)
    # first detection of Tie points with the option ExpTxt=1 to make a report with txt
    command = 'mm3d Tapioca All {} {} ExpTxt=1'.format(pictures_pattern, resol)
    print("\033[0;33" + command + "\033[0m")
    exec_mm3d(command, display_micmac)
    # second detection of Tie points at a lower resolution, without ExpTxt=1, just to avoid a stupid MicMac bug in C3DC
    # MicMac will just convert txt to binary
    command = 'mm3d Tapioca All {} {}'.format(pictures_pattern, resol)
    print("\033[0;33" + command + "\033[0m")
    exec_mm3d(command, display_micmac)

    # Orientation of cameras
    # ===================================================

    # list picture names, used to transform orientation and calibration
    final_pictures = []
    for filepath in filepath_list:
        final_pictures.append(filepath.split("/")[-1])

    ori = distortion_model  # name of orientation, it is the distortion model by default
    # if there is an initial orientation
    print("ICIIII", inori)
    if inori is not None:

        print(os.path.basename(inori))
        # copy the initial orientation file
        new_Ori_path = os.path.join(folder_path, os.path.basename(inori))
        print("OIRIIIII", new_Ori_path)
        if not os.path.exists(new_Ori_path):
            print("COPYTREE",inori,new_Ori_path)
            copytree(inori, new_Ori_path)  # We assume that the path is correctly written ( "/Root/folder/Ori-Truc/")
        # swap pictures names to mock MicMac computed orientation files
        print(pictures_ini)
        print(final_pictures)
        XML_utils.change_Ori(pictures_ini, final_pictures, new_Ori_path)

        # if re_estimate, MicMac recompute the orientation
        if re_estimate:
            ori += "_R"
            command = 'mm3d Tapas {} {} InOri={} Out={}'.format(distortion_model, pictures_pattern,
                                                                os.path.basename(inori), ori)
            print("\033[0;33" + command + "\033[0m")
            success, error = exec_mm3d(command, display_micmac)
        else:
            ori = os.path.basename(inori)  # name of the new ori is the same as the initial one
            success, error = 0, None
    # if there is no initial orientation but an initial calibration
    # it assumed that the calibration is the same for every picture
    elif incal is not None:
        if incal[-1] != "/": incal += "/"
        new_Cal_path = folder_path + incal.split('/')[-2] + "/"
        if not os.path.exists(new_Cal_path):
            copytree(incal, new_Cal_path)  # We assume that the path is correctly written ( "/fgg/Ori-Truc/")
        command = 'mm3d Tapas {} {} InCal={}'.format(distortion_model, pictures_pattern,
                                                     incal.split('/')[-2])
        print("\033[0;33" + command + "\033[0m")
        success, error = exec_mm3d(command, display_micmac)

    # if no initial parameters, classic orientation computation
    else:
        command = 'mm3d Tapas {} {}'.format(distortion_model, pictures_pattern)
        print("\033[0;33" + command + "\033[0m")
        success, error = exec_mm3d(command, display_micmac)

    # if GCP are provided for Bascule (Absolute orientation)
    if abs_coord_gcp is not None and img_coord_gcp is not None:
        # copy GCP absolute coordinates
        gcp_name = os.path.basename(abs_coord_gcp)
        if abs_coord_gcp != os.path.join(folder_path, gcp_name):
            copyfile(abs_coord_gcp, os.path.join(folder_path, gcp_name))
        # create S2D xml file with images positions of gcp
        XML_utils.write_S2D_xmlfile(img_coord_gcp,os.path.join(folder_path, "GCP-S2D.xml"))

        command = 'mm3d GCPBascule {} {} Bascule_ini {} {}'.format(pictures_pattern,
                                                                   ori,
                                                                   gcp_name,
                                                                   "GCP-S2D.xml")
        print(command)
        exec_mm3d(command, display_micmac)
        
        command = 'mm3d Campari {} Bascule_ini Bascule GCP=[{},{},{},{}] AllFree=1'.format(pictures_pattern, gcp_name,GNSS_PRECISION,"GCP-S2D.xml",GCP_POINTING_PRECISION)
        success, error = exec_mm3d(command, display_micmac)

        ori = 'Bascule'

    # dense correlation
    # ===================================================
    if clahe:
        # clahe images were used for orientation, but we need JPG for dense correlation
        for i in range(len(filepath_list)):
            filepath = filepath_list[i]
            filename = os.path.basename(filepath)
            copyfile(filepath, os.path.join(folder_path, filename))

    ply_name += date_str + ".ply"
    command = 'mm3d Malt GeomImage {} {} Master={} DefCor={} MasqIm=Masq'.format(pictures_pattern, ori,
                                                                                 master_img, DefCor)
    print("\033[0;33" + command + "\033[0m")
    success, error = exec_mm3d(command, display_micmac)

    # creation of the final point cloud file
    # ===================================================

    # create the point cloud
    if shift is None:
        command = 'mm3d Nuage2Ply MM-Malt-Img-{}/NuageImProf_STD-MALT_Etape_8.xml Attr={} Out={}'.format(
            '.'.join(master_img.split('.')[:-1]), master_img, ply_name)
    else:
        command = 'mm3d Nuage2Ply MM-Malt-Img-{}/NuageImProf_STD-MALT_Etape_8.xml Attr={} Out={} Offs={}'.format(
            '.'.join(master_img.split('.')[:-1]), master_img, ply_name, str(shift).replace(" ", ""))

    print("\033[0;33" + command + "\033[0m")
    success, error = exec_mm3d(command, display_micmac)

    # ==================================================================================================================
    # Make stats about the reconstruction
    with open(date_str + '_recap.txt', 'w') as recap:
        recap.write("Summary of MicMac 3D reconstruction for " + date_str + "\n")
        string = "\nNumber of Tie Points : "
        df, tot = XML_utils.count_tiepoints_from_txt(folder_path)
        string += str(tot) + "\n\nFiles used :\n"
        for i in df.index.values:
            string += "  - {} taken on {} : {} tie points\n".format(i, load_date(folder_path + i), df.loc())
        recap.write(string)

        if os.path.exists(os.path.join(folder_path,ply_name)):
            copyfile(os.path.join(folder_path,ply_name), os.path.join(output_folder,ply_name))
            recap.write("\nStatus  : Success\n")
        else:
            recap.write("\nStatus  : Failure\n")

        if inori is not None:
            recap.write("\n Initial orientation used  : " + inori + "\n")
        elif incal is not None:
            recap.write("\n Initial calibration used  : " + incal + "\n")

        # write a .txt with residuals
        if ori[:4] == "Ori-":
            ori_path = folder_path + ori + "/"
        else:
            ori_path = folder_path + "Ori-" + ori + "/"
        if os.path.exists(ori_path):  # if Tapas command worked
            dict = XML_utils.extract_res(ori_path)
            recap.write("\nNumber of iterations : {}   Average Residual : {}\n".format(dict['nb_iters'], "%.4f" % dict[
                'AverageResidual']))
            recap.write("\nName           Residual     PercOk        Number of Tie Points\n")
            for i in df.index.values:
                recap.write(
                    "{} : {}       {}       {}\n".format(i, "%.4f" % float(dict[i][0]), "%.4f" % float(dict[i][1]),
                                                         dict[i][2]))
    copyfile(os.path.join(folder_path, date_str + '_recap.txt'), os.path.join(output_folder, date_str + '_recap.txt'))

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
        except PermissionError:
            print("Permission Denied, cannot delete some MicMac files")


def process_from_array(folders_list, pictures_array, output_folder, incal=None, inori=None,
    pictures_ini=None, gcp=None, gcp_S2D=None, clahe=False, tileGridSize_clahe=8, resol=-1,distortion_model="Fraser",
    re_estimate=False, master_folder=0, masq2D=None, DefCor=0.0, shift=None, delete_temp=True,
    display_micmac=True, cond=None, GNSS_PRECISION=0.2, GCP_POINTING_PRECISION=5):
    """
    Do the 3D reconstruction of pictures using MicMac

    Mandatory arguments :
    :param folders_list: list of path to picture folders
            pictures are stored in a folder per camera
    :param pictures_array: array containing names of pictures to process
            each row is considered as a set, and pictures names must be in the same order as secondary_folder_list
    :param output_folder: where output file will be saved as well as where the temporary files will be created
    Reconstruction argument :
    :param resol: resolution for the research of TiePoints
            -1 stands for full resolution
    :param distortion_model: distortion model used in Tapas
            can be "Fraser", "FraserBasic", "RadialStd", "RadialBasic" and more
    :param incal: path to initial calibration folder (from MicMac), None if no initial calibration used
    :param inori: path to initial orientation folder (from MicMac), None if no initial orientation used
    :param pictures_ini: pictures of initial calibration, in the same order as secondary folder list
             None if the pictures are in pictures_array, they will be automatically detected
    :param re_estimate: -only if there is an initial orientation- if True, re estimate the orientation
    :param gcp: .xml file containing coordinates of GCPs, file from the MicMac command "GCPConvert"
    :param gcp_S2D: xml file containing image coordinates of the GCPs, result one of the "SaisieAppuis" command in MicMac

    :param master_folder: list index of the folder where "master images" for Malt reconstruction are stored
            by default it is the first folder
    :param masq2D:
    :param shift: shift for saving ply (if numbers are too big for 32 bit ply) [shiftE, shiftN, shiftZ]
    :param delete_temp: if False the temporary folder will not be deleted, but beware, MicMac files are quite heavy
    :param display_micmac: if False MicMac log will be hidden, may be useful as this may ba a bit messy sometimes
    :return:
    """
    # checking parameters :

    # it is assumed that all pictures have the same extension
    ext = pictures_array[0, 1].split('.')[-1].lower()

    nb_folders = len(folders_list)

    for i in range(nb_folders):
        if folders_list[i][-1] != "/": folders_list[i] += "/"
        if not os.path.exists(folders_list[i]):
            print("WARNING the folder {} in folders_list does not exist".format(folders_list[i]))

    if cond is None:
        def cond(datetime): return True

    if type(master_folder) != int or not (0 <= master_folder < nb_folders):
        print("Invalid value {} for parameter master folder, value set to 0".format(master_folder))
        print("must be one index of the array secondary_folder_list")
        master_folder = 0

    # if pictures_ini is not provided but there is an initial orientation, retrieve it from pictures array
    if inori is not None and pictures_ini is None:
        # find the name of one picture used in inori, using Orientation files
        flist = os.listdir(inori)
        image = ""
        for file in flist:
            if len(file) > 12 and file[:12] == "Orientation-":
                image = file[12:-4]  # todo qu'est ce que c'est moche
                break
        # find the row of this picture in pictures_array and use it as pictures_ini
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
                             "Please fill parameter pictures_ini")
        pictures_ini = pictures_array[i - 1, 1:]

    if gcp is not None and gcp_S2D is not None:
        if type(gcp_S2D) == str:
            if gcp[-4:] != ".xml" or not os.path.exists(gcp_S2D):
                print("WARNING Param gcp must be an xml file from the micmac function GCPConvert")
                exit(1)
            else:
                # retrieve gcp measures for all image in a dictionary
                all_gcp = XML_utils.read_S2D_xmlfile(gcp_S2D)
        elif type(gcp_S2D) == dict:
            # retrieve gcp measures for all image in a dictionary
            all_gcp = gcp_S2D
        else:
            print('ERROR Param gcp_s2d must be either path to the xml or a dictionary')
            exit(1)
        if not os.path.exists(gcp):
            print("WARNING Cannot open gcp file at " + gcp)
            exit(1)

    else:
        all_gcp = None

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
                            masqpath_list[j - 1] = os.path.join(masq2D, file)
                            found = True
                        j += 1
                    i += 1
        if '' in masqpath_list:
            print("Cannot find pictures corresponding to mask in pictures array")
            exit(1)
    else:
        masqpath_list = None

    # launch the process
    for line in pictures_array:

        if line[0]:  # line[0] is a boolean, True if the set is correct
            list_path = []
            for i in range(1, len(folders_list) + 1):
                list_path.append(folders_list[i - 1] + str(line[i]))
            # determining which of the pictures is the master image for dense correlation (Malt)
            master_img = line[master_folder + 1]
            date = load_date(list_path[0])

            if cond(date):
                info = "Processing pictures taken on " + str(date) + ":\n  "
                for img in line[1:]:
                    info += img + "  "

                print(info)

                if all_gcp is not None:
                    # create a dictionary with gcp image coordinates of this picture set
                    try:
                        set_gcp = dict([(k, all_gcp.get(k)) for k in line[1:]])
                    except AttributeError:
                        print("Couldn't find gcp measures for this set of pictures in S2D xml\nSet ignored")
                        continue
                else:
                    set_gcp = None

                copy_and_process(
                    list_path,
                    output_folder=output_folder, incal=incal, inori=inori, pictures_ini=pictures_ini, abs_coord_gcp=gcp,
                    img_coord_gcp=set_gcp, re_estimate=re_estimate,
                    master_img=master_img, masqpath_list=masqpath_list,
                    resol=resol, distortion_model=distortion_model,
                    DefCor=DefCor, clahe=clahe, tileGridSize_clahe=tileGridSize_clahe,
                    shift=shift, delete_temp=delete_temp, display_micmac=display_micmac,
                    GNSS_PRECISION=GNSS_PRECISION, GCP_POINTING_PRECISION=GCP_POINTING_PRECISION)


if __name__ == "__main__":
    tic = time.time()
    print("process launched")

    # main_GCP_estim("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/","DSC00918_11h30.JPG",points = 'selection-S2D.xml')
    # sort_pictures(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_ouest/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_mid/"])

    array = pictures_array_from_file(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/linked_files.txt")
    main_folder = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/"
    folders = [main_folder + "cam_est/",
               main_folder + "cam_ouest/",
               main_folder + "cam_mid/"]
    output_folder = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Results/"
    masq2D = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Mask/"
    inori = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Ori-Fraser/"
    S2D = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/All_points-S2D.xml"
    truc = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/GCP/Pt_gps_gcp.xml"

    process_from_array(folders, array,
                       output_folder=output_folder, resol=2000, master_folder=2,
                       masq2D=masq2D, DefCor=0.4, inori=inori, re_estimate=True,
                       clahe=True, delete_temp=False, gcp_S2D=S2D, gcp=truc,
                       distortion_model="Fraser", display_micmac=True, GNSS_PRECISION=0.2, GCP_POINTING_PRECISION=5)
    # [410000, 6710000, 0]
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
