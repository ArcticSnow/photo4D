''' 
Program XXX Part I



'''

# import all function

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
    IMAGE_FOLDER = "Images"
    MASK_FOLDER = "Masks"
    GCP_FOLDER = "GCP"
    DF_DETECT = "df_detect.csv"
    GCP_xml = 'GCPs_pick'

    def __init__(self, project_path):
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

        # add picture sets
        self.picture_set_def = opj(self.project_path, 'set_definition.txt')
        if os.path.exists(self.picture_set_def):
            self.sorted_pictures = utils.pictures_array_from_file(self.picture_set_def)
            print("Added picture sets from " + self.picture_set_def)
        else:
            self.sorted_pictures = None
        # set default selected set to the last one
        self.selected_picture_set = -1

        if os.path.exists(opj(self.project_path, Photo4d.MASK_FOLDER)):
            self.masks = opj(self.project_path, Photo4d.MASK_FOLDER)
            print("Masks created from ")
        else:
            self.masks = None

        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT)):
            self.df_detect_gcp = pd.read_csv(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT))
            print("Added gcp detection raw results")
        else:
            self.df_detect_gcp = None

        self.result_folder = opj(self.project_path, 'Results')

        self.GCP_coords_file = None

        self.ext = "jpg"

        self.cond = None

    def __str__(self):
        string = "Project Photo4d located at " + self.project_path
        string += "\n Contains {} camera folders : \n   {}".format(self.nb_folders, '\n   '.join(self.cam_folders))
        if self.sorted_pictures is None:
            string += "\n Pictures unsorted"
        else:
            string += "\n Pictures sorted in {} sets ".format(len(self.sorted_pictures))
            string += "\n The current selected set is {}".format(self.sorted_pictures[self.selected_picture_set][1:])
        return string

    def sort_picture(self, time_interval=600):
        self.sorted_pictures = proc.sort_pictures(self.cam_folders, self.picture_set_def, time_interval=time_interval,
                                                  ext=self.ext)
        return self.sorted_pictures

    def check_picture(self, luminosity_thresh=1, blur_thresh=6):
        if self.sorted_pictures is None:
            print("ERROR You must launch the sort_pictures() method before check_pictures()")
            exit(1)
        self.sorted_pictures = proc.check_pictures(self.cam_folders, self.picture_set_def, self.sorted_pictures,
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
        print(file_set)

        # Execute mm3d command for orientation
        success, error = utils.exec_mm3d("mm3d Tapioca All {} {}".format(file_set, resolution), display=display)
        success, error = utils.exec_mm3d("mm3d Tapas {} {} Out=ini".format(distortion_mode, file_set), display=display)

        if success == 0:
            # copy orientaion file and delete tmp folder
            copytree(opj(tmp_path, "Ori-ini"), opj(self.project_path, "Ori-ini"))
        else:
            print("ERROR Orientation failed\nerror : " + str(error))

        os.chdir(self.project_path)
        # todo je sais pas pk si micmac plante je peux pas supprimer le dossier, alors que ca marche sur un autre test
        rmtree(tmp_path)

    def create_mask(self, del_pictures=True):
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

    def prepare_GCP_files(self, GCP_coords_file, file_format='N_X_Y_Z', display=True):

        if not os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER)):
            os.makedirs(opj(self.project_path, Photo4d.GCP_FOLDER))

        self.GCP_coords_file = opj(self.project_path, Photo4d.GCP_FOLDER, os.path.basename(GCP_coords_file))
        copyfile(GCP_coords_file, self.GCP_coords_file)

        success, error = utils.exec_mm3d('mm3d GCPConvert #F={} {}'.format(file_format, self.GCP_coords_file),
                                         display=display)

        GCP_table = np.loadtxt(self.GCP_coords_file, dtype=str)

        try:
            GCP_name = GCP_table[:, file_format.split('_').index("N")]
            print(GCP_name)
            np.savetxt(opj(self.project_path, Photo4d.GCP_FOLDER, "GCPs_name.txt"), GCP_name, fmt='%s',
                       newline=os.linesep)

        except ValueError:  # todo add a coherent except
            print("ERROR prepare_GCP_files(): Check file format and file delimiter. Delimiter is any space")

    # Prepare

    def pick_GCP(self):
        gcp_path = opj(self.project_path, Photo4d.GCP_FOLDER)
        os.chdir(gcp_path)

        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
            in_path = opj(self.cam_folders[i], selected_line[i + 1])
            out_path = opj(gcp_path, selected_line[i + 1])
            copyfile(in_path, out_path)
        file_set = file_set[:-1] + ")"

        gcp_name_file = "GCPs_name.txt"
        print('mm3d SaisieAppuisInitQt "{}" NONE {} {}.xml'.format(file_set, gcp_name_file, self.GCP_xml))
        utils.exec_mm3d('mm3d SaisieAppuisInitQt {} NONE {} {}.xml'.format(file_set, gcp_name_file, self.GCP_xml))

        try:
            for image in selected_line[1:]:
                os.remove(opj(gcp_path, image))
            for folder in ['Tmp-SaisieAppuis', 'Tmp-MM-Dir']:
                rmtree(folder)
            os.remove(self.GCP_xml + '-S3D.xml')
            os.chdir(self.project_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print('WARNING Cannot delete temporary MicMac files due to permission error')

    def detect_GCPs(self, kernel_size=(200, 200), display=True, save_df_gcp=True):

        xml_file = opj(self.project_path, Photo4d.GCP_FOLDER, self.GCP_xml + '-S2D.xml')
        self.df_detect_gcp = ds.detect_from_s2d_xml(xml_file, self.cam_folders,
                                                    self.sorted_pictures, kernel_size=kernel_size,
                                                    display_micmac=display)
        if save_df_gcp:
            print("  Saving result to .csv")
            print(self.df_detect_gcp)
            self.df_detect_gcp.to_csv(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.DF_DETECT), sep=",")

    def extract_GCPs(self, magnitude_max=50, nb_values=5, max_dist=50, kernel_size=(200, 200), method="Median"):

        if self.df_detect_gcp is None:
            print("ERROR detect_GCPs() must have been run before trying to extract values")
            exit(1)

        self.dict_image_gcp, self.df_gcp_abs = ds.extract_values(self.df_detect_gcp, magnitude_max=magnitude_max,
                                                                 nb_values=nb_values, max_dist=max_dist,
                                                                 kernel_size=kernel_size, method=method)

        # write xml file for the record. not necessary
        XML_utils.write_S2D_xmlfile(self.dict_image_gcp,
                                    opj(self.project_path, Photo4d.GCP_FOLDER, 'GCPs_detect-S2D.xml'))

    def process(self, clahe=False, tileGridSize_clahe=8, resol=-1, distortion_model="Fraser", re_estimate=True,
                master_folder=0,
                DefCor=0.0, shift=None, delete_temp=True, display=True):

        proc.process_from_array(self.cam_folders, self.sorted_pictures, self.result_folder,
                                inori=opj(self.project_path, "Ori-ini"),
                                gcp=self.GCP_coords_file, gcp_S2D=self.dict_image_gcp, clahe=clahe,
                                tileGridSize_clahe=tileGridSize_clahe, resol=resol, distortion_model=distortion_model,
                                re_estimate=re_estimate, master_folder=master_folder, masq2D=None, DefCor=DefCor,
                                shift=shift, delete_temp=delete_temp,
                                display_micmac=display, cond=self.cond)

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
    myproj = Photo4d(project_path="C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet")
    # myproj.sort_picture()
    # myproj.check_picture()
    myproj.set_selected_set("DSC00857.JPG")
    print(myproj)

    # myproj.initial_orientation()
    # myproj.create_mask()
    # myproj.prepare_GCP_files("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/GCP/Pt_gps_gcp.txt")
    # myproj.pick_GCP()
    myproj.detect_GCPs()
    myproj.extract_GCPs()
    print(myproj.dict_image_gcp)
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
