''' 
Program XXX Part I



'''

# import all function
import sys
sys.path.append('C:\Git\photo4D\python_script\micmacApp')
sys.path.append('C:\Libraries\Pyxif-master')

# import public library
import os
from os.path import join as opj
import numpy as np, pandas as pd
from typing import Union
from shutil import copyfile, rmtree, copytree

# Import project libary
import Process as proc
import Utils as utils
import Detect_Sift as ds
import XML_utils
import Image_utils as iu


class Photo4d(object):
    # Class constants
    # folders
    IMAGE_FOLDER = 'Images'
    ORI_FOLDER = "Ori-Ini"
    MASK_FOLDER = 'Masks'
    GCP_FOLDER = 'GCP'
    RESULT_FOLDER = "Results"
    # file names
    GCP_COORD_FILE = 'GCPs_coordinates.xml'
    DF_DETECT_FILE = 'df_detect.csv'
    SET_FILE = 'set_definition.txt'
    GCP_PRECISION=0.2 # GCP precision in m
    GCP_POINTING_PRECISION=10 # Pointing precision of GCPs in images (pixels)
    GCP_PICK_FILE_INI = 'GCPs_pick_Ini.xml'
    GCP_PICK_FILE_INI_2D = 'GCPs_pick_Ini-S2D.xml'
    GCP_PICK_FILE_BASC = 'GCPs_pick_Basc.xml'
    GCP_PICK_FILE_BASC_2D = 'GCPs_pick_Basc-S2D.xml'
    GCP_PICK_FILE = 'GCPs_pick.xml'
    GCP_DETECT_FILE = 'GCPs_detect-S2D.xml'
    GCP_NAME_FILE = 'GCPs_names.txt'
    shift=[410000, 6710000, 0]
    # Parameters
    distortion_model="Figee"


    def __init__(self, project_path, ext='jpg'):
        if not os.path.exists(project_path):
            print("ERROR The path " + project_path + " doesn't exists")
            exit(1)

        # add main folder
        self.project_path = os.path.abspath(project_path)
        print("Creation of object photo4d on the folder " + self.project_path)

        # add camera folders
        if os.path.exists(opj(self.project_path, Photo4d.IMAGE_FOLDER)):
            self.cam_folders = [opj(self.project_path, Photo4d.IMAGE_FOLDER, cam) for cam in
                                os.listdir(opj(self.project_path, Photo4d.IMAGE_FOLDER))]
            self.nb_folders = len(self.cam_folders)
            print("Added {} camera folders : \n  {}".format(self.nb_folders, '\n  '.join(self.cam_folders)))
        else:
            print('You must create a folder "' + Photo4d.IMAGE_FOLDER + '/" containing your camera folders')
            exit(1)

        # =========================================================================
        # add picture sets
        picture_set_def = opj(self.project_path, Photo4d.SET_FILE)
        if os.path.exists(picture_set_def):
            self.sorted_pictures = utils.pictures_array_from_file(picture_set_def)
            print("Added picture sets from " + picture_set_def)
        else:
            self.sorted_pictures = None
        # set default selected set to the last one
        self.selected_picture_set = -1

        # =========================================================================
        # add initial orientation
        if os.path.exists(opj(self.project_path, Photo4d.ORI_FOLDER)):
            print("Added initial orientation")
            self.in_ori = opj(self.project_path, Photo4d.ORI_FOLDER)
        else:
            self.in_ori = None

        # =========================================================================
        # add image masks
        if os.path.exists(opj(self.project_path, Photo4d.MASK_FOLDER)):
            self.masks = opj(self.project_path, Photo4d.MASK_FOLDER)
            print("Masks created from ")  # todo add the set of masks (and ori)
        else:
            self.masks = None

        # add GCP initial files
        # =========================================================================
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE)):
            self.gcp_coord_file = opj(self.project_path,Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE)
            print("Added gcp coordinates file")
        else:
            self.gcp_coord_file = None
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE)):
            self.gcp_names = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE)
        else:
            self.gcp_names = None
        # =========================================================================
        # add result of GCPs detection
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT_FILE)):
            self.df_detect_gcp = pd.read_csv(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT_FILE))
            print("Added gcp detection raw results")
        else:
            self.df_detect_gcp = None
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_DETECT_FILE)):
            self.dict_image_gcp = XML_utils.read_S2D_xmlfile(
                opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_DETECT_FILE))
            print("Added gcp detection final results")
        else:
            self.dict_image_gcp = None

        # extension of the images
        self.ext = ext

        # condition on picture dates, to process only a few sets
        self.cond = None

    def __str__(self):
        string = "\n=======================================================================\n" \
                 "Project Photo4d located at " + self.project_path + \
                 "\n======================================================================="
        string += "\n Contains {} camera folders : \n   {}".format(self.nb_folders, '\n   '.join(self.cam_folders))
        if self.sorted_pictures is None:
            string += "\n Pictures unsorted"
        else:
            string += "\n Pictures sorted in {} sets ".format(len(self.sorted_pictures))
            string += "\n The current selected set is {}".format(self.sorted_pictures[self.selected_picture_set][1:])

        string += "\n=======================================================================\n"
        if self.in_ori is not None:
            string += " Initial orientation computed"
            string += "\n=======================================================================\n"

        if self.masks is not None:
            string += " Masks done "
            string += "\n=======================================================================\n"

        if self.gcp_coord_file is not None:
            string += " Absolute coordinates of GCPs are given"
            if self.dict_image_gcp is not None:
                string += "\n GCPs image coordinates are computed "
            string += "\n=======================================================================\n"

        return string

    def sort_picture(self, time_interval=600):
        self.sorted_pictures = proc.sort_pictures(self.cam_folders, opj(self.project_path, Photo4d.SET_FILE),
                                                  time_interval=time_interval,
                                                  ext=self.ext)
        return self.sorted_pictures

    def check_picture(self, luminosity_thresh=1, blur_thresh=6):
        if self.sorted_pictures is None:
            print("ERROR You must launch the sort_pictures() method before check_pictures()")
            exit(1)
        self.sorted_pictures = proc.check_pictures(self.cam_folders, opj(self.project_path, Photo4d.SET_FILE),
                                                   self.sorted_pictures,
                                                   lum_inf=luminosity_thresh,
                                                   blur_inf=blur_thresh)
        return self.sorted_pictures

    def initial_orientation(self, resolution=5000, distortion_mode='Fraser', display=True, clahe=False,
                            tileGridSize_clahe=8):
        # add mkdir, and change dir
        tmp_path = opj(self.project_path, "tmp")
        if not os.path.exists(tmp_path): os.makedirs(tmp_path)
        os.chdir(tmp_path)

        # select the set of good pictures to estimate initial orientation
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(tmp_path, selected_line[i + 1])
            if clahe:
                iu.process_clahe(in_path, tileGridSize_clahe, out_path=out_path)
            else:
                copyfile(in_path, out_path)
            file_set += selected_line[i + 1] + "|"
        file_set = file_set[:-1] + ")"

        # Execute mm3d command for orientation
        success, error = utils.exec_mm3d("mm3d Tapioca All {} {}".format(file_set, resolution), display=display)
        success, error = utils.exec_mm3d(
            "mm3d Tapas {} {} Out={}".format(distortion_mode, file_set, Photo4d.ORI_FOLDER[4:]), display=display)

        ori_path = opj(self.project_path, Photo4d.ORI_FOLDER)
        if success == 0:
            # copy orientation file
            if os.path.exists(ori_path): rmtree(ori_path)
            copytree(opj(tmp_path, Photo4d.ORI_FOLDER), ori_path)
            self.in_ori = ori_path
        else:
            print("ERROR Orientation failed\nerror : " + str(error))

        os.chdir(self.project_path)
        # todo thisraise a permission error despite this chdir I don't know why
        try:
            rmtree(tmp_path)
        except PermissionError:
            print('WARNING Cannot delete temporary folder due to permission error')

    def create_mask(self, del_pictures=True):
        '''
        Note : Only the mask of the central (MASTER) image is necessary
        '''
        
        # add mkdir, and change dir
        mask_path = opj(self.project_path, Photo4d.MASK_FOLDER)
        if not os.path.exists(mask_path): os.makedirs(mask_path)
        # select the set of good pictures to estimate initial orientation
        selected_line = self.sorted_pictures[self.selected_picture_set]
        for i in range(len(self.cam_folders)):
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(mask_path, selected_line[i + 1])
            copyfile(in_path, out_path)
            ds.exec_mm3d('mm3d SaisieMasqQT {}'.format(out_path))
            if del_pictures:
                os.remove(out_path)
        self.masks = mask_path

    def prepare_gcp_files(self, gcp_coords_file, file_format='N_X_Y_Z', display=True):

        if not os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER)):
            os.makedirs(opj(self.project_path, Photo4d.GCP_FOLDER))

        # copy coordinates file into the project
        path2txt = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE)[:-4] + ".txt"
        copyfile(gcp_coords_file, path2txt)

        success, error = utils.exec_mm3d('mm3d GCPConvert #F={} {}'.format(file_format, path2txt),
                                         display=display)
        if success == 0:
            self.gcp_coord_file = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE)
            gcp_table = np.loadtxt(path2txt, dtype=str)

            try:
                gcp_name = gcp_table[:, file_format.split('_').index("N")]
                np.savetxt(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE), gcp_name, fmt='%s',
                           newline=os.linesep)
                self.gcp_names = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE)
            except ValueError:  # todo add a coherent except
                print("ERROR prepare_GCP_files(): Check file format and file delimiter. Delimiter is any space")
        else:
            print("ERROR prepare_GCP_files(): Check file format and file delimiter. Delimiter is any space")
            exit(1)

    def pick_gcp_ini(self):
        if self.gcp_coord_file is None or self.gcp_names is None:
            print("ERROR prepare_gcp_files must be applied first")
        gcp_path = opj(self.project_path, Photo4d.GCP_FOLDER)
        os.chdir(gcp_path)
        print(gcp_path)
        copytree(opj(self.project_path, Photo4d.ORI_FOLDER), opj(gcp_path, 'Ori-Ini'))
        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(gcp_path, selected_line[i + 1])
            copyfile(in_path, out_path)
        file_set = file_set[:-1] + ")"

        print('mm3d SaisieAppuisInitQt "{}" Ori-Ini {} {}'.format(file_set, self.GCP_NAME_FILE,
                                                                   self.GCP_PICK_FILE_INI))
        utils.exec_mm3d(
            'mm3d SaisieAppuisInitQt {} Ori-Ini {} {}'.format(file_set, self.GCP_NAME_FILE, self.GCP_PICK_FILE_INI))

        command = 'mm3d GCPBascule {} Ori-Ini Bascule-ini {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE,
                                                                   self.GCP_PICK_FILE_INI_2D)
        print(command)
        utils.exec_mm3d(command)
        
        try:
            for image in selected_line[1:]:
                os.remove(opj(gcp_path, image))
            for folder in ['Ori-Ini']:
                rmtree(folder)
            #os.remove(Photo4d.GCP_PICK_FILE[:-4] + '-S3D.xml')
            os.chdir(self.project_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print('WARNING Cannot delete temporary MicMac files due to permission error')

    def pick_gcp_basc(self, resolution=5000):
        if self.gcp_coord_file is None or self.gcp_names is None:
            print("ERROR prepare_gcp_files must be applied first")
        gcp_path = opj(self.project_path, Photo4d.GCP_FOLDER)
        os.chdir(gcp_path)
        print(gcp_path)
        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(gcp_path, selected_line[i + 1])
            copyfile(in_path, out_path)
        file_set = file_set[:-1] + ")"

        command='mm3d SaisieAppuisPredicQt "{}" Ori-Bascule-ini {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE,
                                                                   self.GCP_PICK_FILE_BASC)
        print(command)        
        utils.exec_mm3d(command)


        command="mm3d Tapioca All {} {}".format(file_set, resolution)
        print(command)        
        utils.exec_mm3d(command)
        
        command = 'mm3d Campari {} Bascule-ini Bascule GCP=[{},{},{},{}] AllFree=1'.format(file_set, self.GCP_COORD_FILE, self.GCP_PRECISION, self.GCP_PICK_FILE_BASC_2D, self.GCP_POINTING_PRECISION)
        print(command)
        utils.exec_mm3d(command)
        
        # copy orientation file
        copytree(os.path.join(gcp_path,'Ori-Bascule'), os.path.join(self.project_path,'Ori-Bascule'))
        self.in_ori = os.path.join(self.project_path,'Ori-Bascule')
        
        try:
            for image in selected_line[1:]:
                os.remove(opj(gcp_path, image))
            for folder in ['Ori-Bascule_ini']:
                rmtree(folder)
            #os.remove(Photo4d.GCP_PICK_FILE[:-4] + '-S3D.xml')
            os.chdir(self.project_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print('WARNING Cannot delete temporary MicMac files due to permission error')

    def pick_gcp_final(self):
        if self.gcp_coord_file is None or self.gcp_names is None:
            print("ERROR prepare_gcp_files must be applied first")
        gcp_path = opj(self.project_path, Photo4d.GCP_FOLDER)
        os.chdir(gcp_path)
        print(gcp_path)
        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(gcp_path, selected_line[i + 1])
            copyfile(in_path, out_path)
        file_set = file_set[:-1] + ")"

        command='mm3d SaisieAppuisPredicQt "{}" Ori-Bascule {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE,
                                                                   self.GCP_PICK_FILE)
        print(command)        
        utils.exec_mm3d(command)

        try:
            for image in selected_line[1:]:
                os.remove(opj(gcp_path, image))
            for folder in ['Tmp-SaisieAppuis', 'Tmp-MM-Dir','Ori-Bascule','Homol']:
                rmtree(folder)
            #os.remove(Photo4d.GCP_PICK_FILE[:-4] + '-S3D.xml')
            os.chdir(self.project_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print('WARNING Cannot delete temporary MicMac files due to permission error')

    def detect_GCPs(self, kernel_size=(200, 200), display=True, save_df_gcp=True):

        xml_file = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_PICK_FILE[:-4] + '-S2D.xml')
        self.df_detect_gcp = ds.detect_from_s2d_xml(xml_file, self.cam_folders,
                                                    self.sorted_pictures, kernel_size=kernel_size,
                                                    display_micmac=display)
        if save_df_gcp:
            print("  Saving result to .csv")
            self.df_detect_gcp.to_csv(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT_FILE), sep=",")

    def extract_GCPs(self, magnitude_max=50, nb_values=5, max_dist=50, kernel_size=(200, 200), method="Median"):

        if self.df_detect_gcp is None:
            print("ERROR detect_GCPs() must have been run before trying to extract values")
            exit(1)

        self.dict_image_gcp, self.df_gcp_abs = ds.extract_values(self.df_detect_gcp, magnitude_max=magnitude_max,
                                                                 nb_values=nb_values, max_dist=max_dist,
                                                                 kernel_size=kernel_size, method=method)

        # write xml file for the record
        XML_utils.write_S2D_xmlfile(self.dict_image_gcp,
                                    opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_DETECT_FILE ))

    def process(self, master_folder=0, clahe=False, tileGridSize_clahe=8, resol=-1,
                re_estimate=True,
                DefCor=0.0, delete_temp=True, display=True):
        if self.sorted_pictures is None:
            print("ERROR You must apply sort_pictures() before doing anything else")
            exit(1)
        print(self.in_ori, "LAAAAA")

        proc.process_from_array(self.cam_folders, self.sorted_pictures, opj(self.project_path, Photo4d.RESULT_FOLDER),
                                inori=self.in_ori,
                                gcp=self.gcp_coord_file, gcp_S2D=self.dict_image_gcp, clahe=clahe,
                                tileGridSize_clahe=tileGridSize_clahe, resol=resol, distortion_model=self.distortion_model,
                                re_estimate=re_estimate, master_folder=master_folder, masq2D=self.masks, DefCor=DefCor,
                                shift=self.shift, delete_temp=delete_temp,
                                display_micmac=display, cond=self.cond, 
                                GNSS_PRECISION=self.GCP_PRECISION, GCP_POINTING_PRECISION=self.GCP_POINTING_PRECISION)

    def set_selected_set(self, img_or_index: Union[int, str]):
        if self.sorted_pictures is None:
            print("ERROR You must apply sort_pictures before trying to chose a set")
            exit(1)
        else:
            if type(img_or_index) == int:
                self.selected_picture_set = img_or_index
                print(
                    "\n The current selected set is now {}".format(self.sorted_pictures[self.selected_picture_set][1:]))
            elif type(img_or_index) == str:
                found, i = False, 0
                while (not found) and (i < len(self.sorted_pictures)):
                    if img_or_index in self.sorted_pictures[i]:
                        found = True
                        self.selected_picture_set = i
                        print("\n The current selected set is now {}".format(
                            self.sorted_pictures[self.selected_picture_set][1:]))
                    i += 1
                if not found:
                    print('image {} not in sorted_pictures'.format(img_or_index))

    def add_cond(self, condition):
        if type(condition) != function:
            print("WARNING input condition must be a function, which return a boolean and take a date as parameter")
        else:
            print("Condition applied")
    # function to only execute program on a subseltection of images


if __name__ == "__main__":
    myproj = Photo4d(project_path=r"C:\Users\lucg\Documents\Finse\2018-midseason")
   # myproj.sort_picture()
    #myproj.check_picture()
    #myproj.set_selected_set("DSC03493.JPG")

    #myproj.initial_orientation()
    #myproj.create_mask()
    #myproj.prepare_gcp_files(r"I:\icemass-users\lucg\Finse\Photo4D\2018-first_last\GCPs_coordinates_manual.txt",file_format="N_X_Y_Z")
    #myproj.pick_gcp_ini()
    #myproj.pick_gcp_basc()
    #myproj.pick_gcp_final()
    #myproj.detect_GCPs()
    #myproj.extract_GCPs()
    #myproj.process(resol=4000)
    # Part 1, sort and flag good picture set
    # myproj.sort_picture()
    # myproj.check_picture()

    # Part 2: Manual
    # choose either:
    # 		- Calibration, calibration of camera (TODO)
    # 		- Orientation, estimate camera position

    # myproj.selected_picture_set = -1  # by default get the last set of image. Change to the correct index where there are good quality images
    # myproj.oriententation_intitial()

    # myproj.selected_picture_set = -1
    # myproj.create_mask()

    # Part 3: Derive GCPS in image stack

    # myproj.prepare_GCP_files("GCPs.txt")  # format the text file to

    # myproj.selected_picture_set = -1
    # myproj.pick_GCP()

    # myproj.detect_GCPs()

    # point GCP (manual)
    # estimate on stack

    # Part 4: Process images to point cloud
    # myproj.process()
