''' 
Program XXX Part I



'''


# import all function

# import public library
import os
import os.path.join as opj
import numpy as np
from shutil import copyfile, rmtree, copytree

# Import project libary
import Process as proc
import Utils as utils
import DetectSift as ds
import XML_utils

class photo4d(object):
	
	def __init__(self,project_path):
		self.project_path = os.path.abspath(project_path)
		self.picture_set_def = opj(self.project_path,'set_definition.txt')
		self.cam_folders = [opj(self.project_path, cam) for cam in os.listdir(self.project_path + 'Image')]
		self.result_folder = opj(self.project_path, 'Results')
		self.selected_picture_set = -1

		self.GCP_coords_file = None
		self.GCP_xml = 'GCPs_pick'

		self.ext = "jpg"
		self.cond = None


	def sort_picture(self, timeInterval=600):
		self.sorted_pictures = proc.sort_pictures(self.cam_folders, self.picture_set_def, timeInterval=timeInterval,ext=self.ext)
		return self.sorted_pictures


	def check_picture(self, luminosity_thresh=1, blur_thresh=5):
		self.sorted_pictures = check_picture(self.cam_folders, self.picture_set_def, lum_inf=luminosity_thresh, blur_inf=blur_thresh)
		return self.sorted_pictures


	def orientation_initial(self, resolution=5000, distortion_mode='Fraser', initial_calibration=None, display=True):

		# select the set of good pictures to estimate initial orientation
		selected_line = self.sorted_pictures[self.selected_picture_set]
		file_set = "("
		for i in range(len(cam_folders)):
			file_set += opj(cam_folders[i], selected_line[ i + 1]) + "|"
		file_set = file_set[:-1] + ")"

		# add mkdir, and change dir
		tmp_path = opj(self.project_path,"tmp")
		os.makedirs(tmp_path)
		os.chdir(tmp_path)

		# Execute mm3d command for orientation
		success, error = utils.exec_mm3d("mm3d Tapioca All {} {}".format(file_set, resolution), display=display)
		success, error = utils.exec_mm3d("mm3d Tapas {} {} Out=ini".format(distortion_mode, file_set), display=display)

		os.chdir(self.project_path)
		# copy orientaion file and delete tmp folder
		copytree(opj(tmp_path, "Ori-ini"), opj(self.project_path,"Ori-ini"))
		rmtree(tmp_path)

	def create_mask(self):
		# add mkdir, and change dir
		masq_path = opj(self.project_path,"Masks")
		os.makedirs(masq_path)
		os.chdir(mask_path)
		# select the set of good pictures to estimate initial orientation
		selected_line = self.sorted_pictures[self.selected_picture_set]
		for i in range(len(cam_folders)):
			ds.exec_mm3d('mm3d SaisieMasqQT {}'.format(opj(cam_folders[i], selected_line[ i + 1])))
		os.chdir(self.project_path)
		

	def prepare_GCP_files(self, GCP_coords_file, file_format='N_X_Y_Z' display=True):

		os.makedirs(opj(self.project_path,"GCP"))
		os.chdir(opj(self.project_path,"GCP"))
		self.GCP_coords_file = opj(self.project_path, GCP_coords_file)

		success, error = utils.exec_mm3d('mm3d GCPCoonvert "#F{}" {}'.format(file_format, self.GCP_coords_file), display=display)
		
		try:
			GCP_table = np.loadtxt(self.GCP_coords_file, delimiter=' ')
			GCP_name = GCP_table[:,file_format.split('_').index("N")]
			np.savetxt(opj(self.project_path,"GCPs_name.txt"),GCP_name)

		except:
			print("ERROR prepare_GCP_files(): Check file format and file delimiter. Must be a single space delimiter")


		os.chdir(self.project_path)

		# Prepare 


	def pick_GCP(self):

		os.chdir(opj(self.project_path,"GCP"))

		# select the set of image on which to pick GCPs manually
		selected_line = self.sorted_pictures[self.selected_picture_set]
		file_set = "("
		for i in range(len(cam_folders)):
			file_set += opj(cam_folders[i], selected_line[ i + 1]) + "|"
		file_set = file_set[:-1] + ")"

		gcp_name_file = opj(self.project_path,"GCPs_name.txt")
		utils.exec_mm3d("mm3d SaisieAppuisInitQt {} NONE {} {}.xml".format(file_set, gcp_name_file, self.GCP_xml))

		for folder in ['Tmp-SaisieAppuis','Tmp-MM-Dir']:
			rmtree(folder)
		os.remove(self.GCP_xml + '-S3D.xml')
		os.chdir(self.project_path)



	def detect_GCPs(self, kernel_size=(200,200), display=True):

		xml_file = opj(self.project_path, 'GCP', self.GCP_xml+'-S2D.xml')
		self.df_detect_gcp = ds.detect_from_s2d_xml(xml_file, self.cam_folders, 
				self.sorted_pictures, samples_folder=None, kernel_size=kernel_size, dipslay_micmac=display)


	def extract_GCPs(self, magnitude_max=50, nb_values=5, max_dist=50, kernel_size=(200, 200), method="Median"):

		self.dict_image_gcp, self.df_gcp_abs= ds.extract_values(self.df_detect_gcp, magnitude_max=magnitude_max, 
			nb_values=nb_values, max_dist=max_dist, kernel_size=kernel_size, method=method)

		# write xml file for the record. not necessary
		XML_utils.write_S2D_xmlfile(self.dict_image_gcp, opj(self.project_path,'GCP','GCPs_detect-S2D.xml'))



	def process(self, clahe=False, tileGridSize_clahe=8, resol=-1, distortion_model,re_estimate=True,master_folder=0,
		DefCor=0.0,shift=None,delete_temp=True,display=True):

		proc.process_from_array(self.cam_folders, self.sorted_pictures, self.result_folder, inori=opj(self.project_path,"Ori-ini"),
			gcp=self.GCP_coords_file, gcp_S2D=self.dict_image_gcp,clahe=clahe, tileGridSize_clahe=tileGridSize_clahe, resol=resol,distortion_model,
			re_estimate=re_estimate, master_folder=master_folder, masq2D=None, DefCor=DefCor, shift=shift, delete_temp=delete_temp,
			display_micmac=display, cond=self.cond):


	def add_cond(self):
		# function to only execute program on a subseltection of images






if __name__ == "__main__":
	myproj = photo4d(project_path = "mypath/")

	# Part 1, sort and flag good picture set
	myproj.sort_picture()
	myproj.check_picture()

	# Part 2: Manual
		# choose either:
		# 		- Calibration, calibration of camera (TODO)
		# 		- Orientation, estimate camera position 

	myproj.selected_picture_set = -1   # by default get the last set of image. Change to the correct index where there are good quality images
	myproj.oriententation_intitial()

	myproj.selected_picture_set = -1
	myproj.create_mask()


	# Part 3: Derive GCPS in image stack
	
	myproj.prepare_GCP_files("GCPs.txt")   # format the text file to 
	
	myproj.selected_picture_set = -1
	myproj.pick_GCP()

	myproj.detect_GCPs()


		# point GCP (manual)
		# estimate on stack


	# Part 4: Process images to point cloud
	myproj.process()