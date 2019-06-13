# coding : uft8
# Generic imports
import os
from shutil import rmtree, move
# Photo4D imports
from photo4d.Utils import exec_mm3d
import re


def process_one_timestep(work_folder, pictures_array, timestep, output_folder,
                          clahe=False, tileGridSize_clahe=8, zoomF=1,
                          master_folder_id=0, Ori='Bascule', DefCor=0.0,
                          shift=None, keep_rasters=True, display_micmac=False):
    os.chdir(work_folder)
    I, J = pictures_array.shape
    
    if pictures_array[timestep, 1]: #just skip if the set is invalid somehow
            # Setup parameters
            selected_line=pictures_array[timestep]
            img_set="("
            for j in range(2,J):
                img_set += selected_line[j] + "|"
            img_set = img_set[:-1] + ")"
                
            master_img=selected_line[master_folder_id + 2]
            date_str=selected_line[0]
            ply_name= date_str + '.ply'
            
            # Don't run again if already existing
            if os.path.exists(os.path.join(work_folder,ply_name)):
                move(os.path.join(work_folder,ply_name), os.path.join(output_folder,ply_name))
            if not os.path.exists(os.path.join(output_folder,ply_name)):                      
                # Define Malt command and run it
                command='mm3d Malt GeomImage {} {} Master={} DefCor={} ZoomF={}'.format(img_set, Ori,
                                                                                     master_img, DefCor, zoomF)
                print(command)
                success, error = exec_mm3d(command, display_micmac)
                
    
                # Find the last depth map and correlation file 
                    # Get a list of all the files in the Malt output folder
                files=[]
                for f in os.walk(os.path.join(work_folder,'MM-Malt-Img-'+ master_img[:-4])):
                    for file in f:
                        files=file
                nuage_re = re.compile(r'NuageImProf_STD-MALT_Etape_\d{1}.xml')
                correlation_re = re.compile(r'Correl_STD-MALT_Num_\d{1}.tif')
                depth_re = re.compile(r'Z_Num\d{1}_DeZoom' + str(zoomF) +'_STD-MALT.tif')
                nuage_files = [ x for x in files if nuage_re.match(x)]
                correlation_files = [ x for x in files if correlation_re.match(x)]
                depth_files = [ x for x in files if depth_re.match(x)]
                sorted_nuage_files = sorted(nuage_files,reverse=True)
                sorted_correlation_files = sorted(correlation_files,reverse=True)
                sorted_depth_files = sorted(depth_files,reverse=True)
                last_nuage=sorted_nuage_files[0]
                last_cor=sorted_correlation_files[0]
                last_depth=sorted_depth_files[0]
                
                # Create the point cloud            
                if shift is None:
                    command = 'mm3d Nuage2Ply MM-Malt-Img-{}/{} Attr={} Out={}'.format(
                        '.'.join(master_img.split('.')[:-1]), last_nuage, master_img, ply_name)
                else:
                    command = 'mm3d Nuage2Ply MM-Malt-Img-{}/{} Attr={} Out={} Offs={}'.format(
                        '.'.join(master_img.split('.')[:-1]), last_nuage, master_img, ply_name, str(shift).replace(" ", ""))
            
                print(command)
                success, error = exec_mm3d(command, True)
                
                # Copy result to result folder
                # .ply point cloud
                move(os.path.join(work_folder,ply_name), os.path.join(output_folder,ply_name))
                # If we want to keep the correlation map and the depth map
                if(keep_rasters):
                    move(os.path.join(work_folder,'MM-Malt-Img-' + master_img,last_cor), os.path.join(output_folder,date_str + '_Correlation.tif'))
                    move(os.path.join(work_folder,'MM-Malt-Img-' + master_img,last_depth), os.path.join(output_folder,date_str + '_DepthMap.tif'))
                
                # Clean-up
                
                try:
                    rmtree(os.path.join(work_folder,'MM-Malt-Img-' + master_img[:-4]))
                except FileNotFoundError:
                    pass
                except PermissionError:
                    print("Permission Denied, cannot delete " + os.path.join(work_folder,'MM-Malt-Img-' + master_img))
                except OSError:
                    pass
                try:
                    rmtree(os.path.join(work_folder,"Pyram"))
                except PermissionError:
                    print("Permission Denied, cannot delete Pyram folder")
                except OSError:
                    pass
    # Go back to project folder    
    os.chdir('../') 
                

def process_all_timesteps(work_folder, pictures_array, output_folder,
                          clahe=False, tileGridSize_clahe=8, zoomF=1,
                          master_folder_id=0, Ori='Bascule', DefCor=0.0,
                          shift=None, keep_rasters=True, display_micmac=False):
    """
    Run MicMac (mm3d Malt) on all valid picture sets
    It is advised to give only absolute path in parameters


    :param work_folder: folder where the images and orientations are
    :param pictures_array: array with set definitions (also, validity of sets and timestamp)
    :param output_folder: directory for saving results
    :param clahe: if True, apply a "contrast limited adaptive histogram equalization" on the pictures before processing
    
    MicMac parameters: (see more documentation on official github and wiki (hopefully))
    :param zoomF: final zoom in the pyramidal correlation scheme
    :param master_folder_id: id of the folder containing the master images (central image of sets)
    :param Ori: Orientation to use for the correlation (Def='Bascule', the output of 'Class_photo4D.compute_transform(True)')
    :param DefCor: correlation threshold to reject area in the correlation process ([0-1] def=0)
    :param shift: shift for saving ply (if numbers are too big for 32 bit ply) [shiftE, shiftN, shiftZ]
    :param keep_rasters: keep the depth map and last correlation map
    :param display_micmac: show MicMac consol output, only usefull to follow individual set correlation status
    :return:
    """
    # ==================================================================================================================
    # checking path and parameters :
    nb_folders = len(pictures_array)

    if type(master_folder_id) != int or not (0 <= master_folder_id < nb_folders):
        print("Invalid value {} for parameter master folder, value set to 0".format(master_folder_id))
        print("must be one index of the array secondary_folder_list")
        master_folder_id = 0
        
    # make output folder if not already present
    if not os.path.exists(output_folder): os.makedirs(output_folder)
    
    # Go through set for each set
    I, J = pictures_array.shape
    for timestep in range(I):
        process_one_timestep(work_folder, pictures_array, timestep, output_folder,
                          clahe=clahe, tileGridSize_clahe=tileGridSize_clahe, zoomF=zoomF,
                          master_folder_id=master_folder_id, Ori=Ori, DefCor=DefCor,
                          shift=shift, keep_rasters=keep_rasters, display_micmac=display_micmac)

