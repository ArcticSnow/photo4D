''' 
Program XXX Part I



'''

# import public library
import os
from os.path import join as opj
import numpy as np
from typing import Union
from shutil import copyfile, rmtree, copytree

# Import project libary
import photo4d.Process as proc
import photo4d.Utils as utils
import photo4d.Detect_Sift as ds
import photo4d.Image_utils as iu


class Photo4d(object):
    # Class constants
    # folders
    IMAGE_FOLDER = 'Images'
    ORI_FOLDER = "Ori-Ini"
    ORI_FINAL = "Ori-Bascule"
    MASK_FOLDER = 'Masks'
    GCP_FOLDER = 'GCP'
    RESULT_FOLDER = "Results"
    # file names
    GCP_COORD_FILE_INIT = 'GCPs_coordinates.xml'
    GCP_COORD_FILE_FINAL = 'GCPs_pick-S3D.xml'
    DF_DETECT_FILE = 'df_detect.csv'
    SET_FILE = 'set_definition.txt'
    GCP_PRECISION=0.2 # GCP precision in m
    GCP_POINTING_PRECISION=10 # Pointing precision of GCPs in images (pixels)
    GCP_PICK_FILE = 'GCPs_pick.xml'
    GCP_PICK_FILE_2D = 'GCPs_pick-S2D.xml'
    GCP_DETECT_FILE = 'GCPs_detect-S2D.xml'
    GCP_NAME_FILE = 'GCPs_names.txt'
    shift=[410000, 6710000, 0]
    # Parameters
    distortion_model="Figee"
    
    
    def __init__(self, project_path, ext='JPG'):
        if not os.path.exists(project_path):
            print("ERROR The path " + project_path + " doesn't exists")
            return
            
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
            return
            
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
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE_INIT)):
            self.gcp_coord_file = opj(self.project_path,Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE_INIT)
            print("Added gcp coordinates file")
        else:
            self.gcp_coord_file = None
        if os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE)):
            self.gcp_names = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_NAME_FILE)
        else:
            self.gcp_names = None
            
        # extension of the images
        self.ext = ext
        
        # condition on picture dates, to process only a few sets
        self.cond = None
        
        # Create temp folder
        self.tmp_path = opj(self.project_path, "tmp")
        if not os.path.exists(self.tmp_path): 
            os.makedirs(self.tmp_path)

        
        
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
        self.sorted_pictures = iu.sort_pictures(self.cam_folders, opj(self.project_path, Photo4d.SET_FILE),
                                                  time_interval=time_interval,
                                                  ext=self.ext)
        return self.sorted_pictures


    def check_picture_quality(self, luminosity_thresh=1, blur_thresh=6):
        '''
        Function to Check if pictures are not too dark and/or too blurry (e.g. fog)
        '''
        if self.sorted_pictures is None:
            print("ERROR You must launch the sort_pictures() method before check_pictures()")
            return
        self.sorted_pictures = iu.check_picture_quality(self.cam_folders, opj(self.project_path, Photo4d.SET_FILE),
                                                   self.sorted_pictures,
                                                   lum_inf=luminosity_thresh,
                                                   blur_inf=blur_thresh)
        return self.sorted_pictures

            
    def timeSIFT_orientation(self, resolution=5000, distortion_mode='Fraser', display=False, clahe=False,
                            tileGridSize_clahe=8):
        '''
        Function to initialize camera orientation of the reference set of images using the Micmac command Tapas
        '''
        # change from working dir to tmp dir
        os.chdir(self.tmp_path)
        
        # select the set of good pictures to estimate initial orientation
        
        
        for s in range(len(self.sorted_pictures)):
            if self.sorted_pictures[s, 1]:
                selected_line = self.sorted_pictures[s]
                
                for i in range(len(self.cam_folders)):
                    in_path = opj(self.cam_folders[i], selected_line[i + 2])
                    out_path = opj(self.tmp_path, selected_line[i + 2])
                    if clahe:
                        iu.process_clahe(in_path, tileGridSize_clahe, out_path=out_path)
                    else:
                        copyfile(in_path, out_path)

        # Execute mm3d command for orientation
        success, error = utils.exec_mm3d("mm3d Tapioca All {} {}".format(".*" + self.ext, resolution), display=display)
        success, error = utils.exec_mm3d(
            "mm3d Tapas {} {} Out={}".format(distortion_mode, ".*" + self.ext, Photo4d.ORI_FOLDER[4:]), display=display)

        ori_path = opj(self.project_path, Photo4d.ORI_FOLDER)
        if success == 0:
            # copy orientation file
            if os.path.exists(ori_path): rmtree(ori_path)
            copytree(opj(self.tmp_path, Photo4d.ORI_FOLDER), ori_path)
            self.in_ori = ori_path
        else:
            print("ERROR Orientation failed\nerror : " + str(error))

        os.chdir(self.project_path)

            
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
        '''
        Function to prepare GCP coordinate from a textfile to Micmac xml format. Make sure your text file format is correct
        '''

        if not os.path.exists(opj(self.project_path, Photo4d.GCP_FOLDER)):
            os.makedirs(opj(self.project_path, Photo4d.GCP_FOLDER))
            
        # copy coordinates file into the project
        path2txt = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE_INIT)[:-4] + ".txt"
        copyfile(gcp_coords_file, path2txt)
        
        success, error = utils.exec_mm3d('mm3d GCPConvert #F={} {}'.format(file_format, path2txt),
                                         display=display)
        if success == 0:
            self.gcp_coord_file = opj(self.project_path, Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE_INIT)
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
            return 0
            
    def pick_initial_gcps(self):
        '''
        Function to pick GCP locations on the reference set of images with no a priori.
        
        Pick few GCPs (3 to 5) that MicMac can do a rough estimate of the camera orientation. Then go to pick_gcp_basc() to pick all GCPs of known location
        '''        
        os.chdir(self.tmp_path)
        
        if self.gcp_coord_file is None or self.gcp_names is None:
            print("ERROR prepare_gcp_files must be applied first")
        gcp_path = opj(self.project_path, Photo4d.GCP_FOLDER)
        copytree(opj(gcp_path), opj(self.tmp_path))
        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
        file_set = file_set[:-1] + ")"
            
        commandSaisieAppuisInitQt='mm3d SaisieAppuisInitQt "{}" Ini {} {}'.format(file_set, self.GCP_NAME_FILE,
                                                                   self.GCP_PICK_FILE)
        print(commandSaisieAppuisInitQt)
        utils.exec_mm3d(commandSaisieAppuisInitQt)
        
        # Go back from tmp dir to project dir        
        os.chdir(self.project_path)
        
        
    def pick_all_gcps(self, resolution=5000):
        '''
        Function to pick GCP locations on the reference set of images, with a predicted position.
        
        Pick all GCPs of known location.
        '''

        os.chdir(self.tmp_path)

        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
        file_set = file_set[:-1] + ")"

        command='mm3d SaisieAppuisPredicQt "{}" Bascule-Ini {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE_INIT,
                                                                   self.GCP_PICK_FILE)
        print(command)        
        utils.exec_mm3d(command)

        # Go back from tmp dir to project dir        
        os.chdir(self.project_path)
        
    def compute_transform(self, doCampari=False):
        '''
        Function to apply the transformation computed from the GCPs to all images.
        
        Set doCampari=True once all points are input and you are ready to carry on.
        '''

        os.chdir(self.tmp_path)

        # select all the images
        file_set = ".*" + self.ext
        
        commandBasc = 'mm3d GCPBascule {} Ini Bascule-Ini {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE_INIT,
                                                                   self.GCP_PICK_FILE_2D)
        print(commandBasc)
        utils.exec_mm3d(commandBasc)
        
        if(doCampari):
            command = 'mm3d Campari {} Bascule-Ini Bascule GCP=[{},{},{},{}] AllFree=1'.format(file_set, self.GCP_COORD_FILE_INIT, self.GCP_PRECISION, self.GCP_PICK_FILE_2D, self.GCP_POINTING_PRECISION)
            print(command)
            utils.exec_mm3d(command)
            copytree(opj(self.tmp_path, 'Ori-Bascule'),  Photo4d.ORI_FINAL)
             
        # Go back from tmp dir to project dir        
        os.chdir(self.project_path)

            
    def pick_ManualTiePoints(self):
        '''
        Function to pick additional points that can be set as 'GCPs'. These will get coordinates estimates based on camera orientation, and will be used in other set of images for triangulation.
        This way, we artificailly increase the number of GCPs, and use the selected set of reference images as the absolute reference to which other 3D model will be orientated against. 
        
        Pick as many points as possible that are landmarks across the all set of image.
        '''

        os.chdir(self.tmp_path)

        # select the set of image on which to pick GCPs manually
        selected_line = self.sorted_pictures[self.selected_picture_set]
        file_set = "("
        for i in range(len(self.cam_folders)):
            file_set += selected_line[i + 1] + "|"
        file_set = file_set[:-1] + ")"
            
        command='mm3d SaisieAppuisPredicQt "{}" Ori-Bascule {} {}'.format(file_set,
                                                                   self.GCP_COORD_FILE_INIT,
                                                                   self.GCP_PICK_FILE)
        print(command)        
        utils.exec_mm3d(command)
        self.gcp_coord_file = opj(self.project_path,Photo4d.GCP_FOLDER, Photo4d.GCP_COORD_FILE_FINAL)
        
        # Go back from tmp dir to project dir        
        os.chdir(self.project_path)


    def process_all_timesteps(self, master_folder_id=0, clahe=False, tileGridSize_clahe=8, 
                              zoomF=1, Ori='Bascule', DefCor=0.0, shift=None, keep_rasters=True, display=False):
        if self.sorted_pictures is None:
            print("ERROR You must apply sort_pictures() before doing anything else")
            return

        proc.process_all_timesteps(self.tmp_path, self.sorted_pictures, opj(self.project_path, Photo4d.RESULT_FOLDER),
                          clahe=clahe, tileGridSize_clahe=tileGridSize_clahe, zoomF=zoomF,
                          master_folder_id=master_folder_id, Ori=Ori, DefCor=DefCor,
                          shift=shift, keep_rasters=keep_rasters, display_micmac=display)


    
    def set_selected_set(self, img_or_index: Union[int, str]):
        if self.sorted_pictures is None:
            print("ERROR You must apply sort_pictures before trying to chose a set")
            return
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

        

    def clean_up_tmp(self):
        '''
        Function to delete the working folder.
        '''
        try:
            rmtree(self.tmp_path)  
        except FileNotFoundError:
            pass
        except PermissionError:
            print("Permission Denied, cannot delete " + self.tmp_path)
        except OSError:
            pass      
                
                
                
if __name__ == "__main__":
    
    # myproj = p4d.Photo4d(project_path=r"C:\Users\lucg\Desktop\Test_V1_2019")
    # myproj.sort_picture()
    # myproj.check_picture_quality()
    # myproj.timeSIFT_orientation()
    ## TODO : mask tie points
    # myproj.prepare_gcp_files(r"C:\Users\lucg\Desktop\Test_V1_2019\GCPs_coordinates_manual.txt",file_format="N_X_Y_Z")
    ## Select a set to input GCPs
    # myproj.set_selected_set("DSC02728.JPG")
    ## Input GCPs in 3 steps
    # myproj.pick_initial_gcps()
    # myproj.compute_transform()
    # myproj.pick_all_gcps()
    ## Eventually, change selected set to add GCP imput to more image (n times):
        #myproj.compute_transform()
        #myproj.set_selected_set("DSC02871.JPG")
        #myproj.pick_all_gcps()        
    #myproj.compute_transform(doCampari=True)
    
    ## FUNCTION TO CHANGE FOR TIMESIFT
    # myproj.create_mask()
    # myproj.process_all_timesteps()
    # myproj.clean_up_tmp()
    
    
    
    
    
    
    #OLD STUFF
    
    
    myproj = Photo4d(project_path=r"L:\Finse\Photo4D\Test_V1_2019")
   # myproj = Photo4d(project_path=r"~/icemassME/Finse/Photo4D/2018-1pm")
   # myproj.sort_picture()
    #myproj.check_picture_quality()
    
    #myproj.set_selected_set("DSC02728.JPG")
    #myproj.initial_orientation()
    #myproj.create_mask()
    #myproj.prepare_gcp_files(r"I:\icemass-users\lucg\Finse\Photo4D\2018-1pm\GCPs_coordinates_GNSS_Only.txt",file_format="N_X_Y_Z")
    #myproj.pick_initial_gcps()
    #myproj.compute_transform()
    #myproj.pick_all_gcps()
    #myproj.pick_gcp_final()
    #myproj.compute_transform(doCampari=True)
    

    
    
    #TODO: function to clean micmac diurectory (if needed)
    
    #myproj.detect_GCPs()
    #myproj.extract_GCPs()
    #myproj.graph_detected_gcps(50)
    #myproj.process(resol=4000)
    # Part 1, sort and flag good picture set
    # myproj.sort_picture()
    # myproj.check_picture_quality()

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
