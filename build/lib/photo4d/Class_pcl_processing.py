'''
Class and functions to process the point clouds



'''

import pdal, json, glob


class pcl_process(object):


	def __init__(self, project_path, ext='ply'):

		if not os.path.exists(project_path):
            print("ERROR The path " + project_path + " doesn't exists")
            return
        else:
        	self.project_path = project_path
        	os.chdir(self.project_path)

        # parameters for point cloud filtering 
        self.x_offset = 410000      # these values are default for Finse, NORWAY
		self.y_offset = 6710000     # these values are default for Finse, NORWAY

		# Cropping area
		self.crop_xmin = 416100
		self.crop_xmax = 416900
		self.crop_ymin = 6715900
		self.crop_ymax = 6716700

		# Raster bounding box, default is same as cropping box.
		self.raster_xmin = self.crop_xmin
		self.raster_xmax = self.crop_xmax
		self.raster_ymin = self.crop_ymin
		self.raster_ymax = self.crop_ymax

        # parameters for conversion to GeoTiff
        self.resolution = 1
        self.radius = self.resolution * 1.4
        self.nodata = -9999
        self.gdaldriver = "GTiff"
        self.output_type = ["min", "max", "mean", "idw", "count", "stdev"]


    def add_ply_pcl(self)
        os.chdir(self.project_path)
        self.ply_pcl_flist = glob.glob("*.ply")
        print("=======================\n PLY point clouds added: ")
        for file in self.ply_pcl_flist:
        	print(file)
        print(".......................")
        print(str(self.ply_pcl_flist.__len__()) + " point clouds added")
        print("=======================")


    def add_las_pcl(self)
        os.chdir(self.project_path)
        self.las_pcl_flist = glob.glob("*.las")
        print("=======================\n LAS point clouds added: ")
        for file in self.las_pcl_flist:
        	print(file)
        print(".......................")
        print(str(self.las_pcl_flist.__len__()) + " point clouds added")
        print("=======================")


	def pipeline_realization(pip_json, print_result):
	    try:
	        # ===============================================
	        # Pipeline execution
	        pipeline = pdal.Pipeline(pip_json)
	        pipeline.validate()  # check if our JSON and options were good

	        pipeline.execute()

	        if print_result:
	            arrays = pipeline.arrays
	            metadata = pipeline.metadata
	            log = pipeline.log
	            print("\n================")
	            print("Arrays:")
	            print(arrays)
	            print("\n================")
	            print("Metadata:")
	            print(metadata)
	            print("\n================")
	            print("Log:")
	            print(log)

	        print("pdal pipeline finished")
	        return True
	    except:
	        print(" Error !!")
	        return False


    def filter_pcl(self, file_input, file_output, print_result=True):
    	'''
    	Function to filter a point cloud: cropping to ROI, removing statistically outliers, saving output to .las format
    	'''
		pip_filter_json = json.dumps(
			{
			  	"pipeline": 
			  	[
				    file_input,
				    {
					    "type":"filters.python",
						"script":"pdal_python_filter.py",
						"function":"add_XY_UTM",
						"pdalargs":{"x_offset":self.x_offset,"y_offset":self.y_offset}
				    },
				    {
				        "type":"filters.crop",
				        "bounds":str(([self.crop_xmin, self.crop_xmax], [self.crop_ymin, self.crop_ymax]))
				    },
				    {
		                "type": "filters.range",
		                "limits": "Z[" + str(zmin) + ":" + str(zmax) + "]"
            		},
            		{
		              "type":"filters.lof",
		              "minpts":20
		            },
		            {
		              "type":"filters.range",
		              "limits":"LocalOutlierFactor[:1.2]"
		            },
					{
					    "type": "filters.range",
					    "limits": "Classification![7:12]"
					},
					{
						"type":"writers.las",
						"filename":file_ouput,
						"scale_x":1,
						"scale_y":1,
						"scale_z":1

					}
			  	]
			}
		)
		pipeline_realization(pip_filter_json, print_result=print_result)


	def filter_all_pcl(self, print_result=True):
		'''
		Function to process all pcl with filter_pcl() function
		'''
		print("=======================")
		for file in self.ply_pcl_flist:
			filter_pcl(self, file, file[:-4] + '_clean.las', print_result=print_result)
		print(".......................")
		print("All PLY files filtered")
		print("=======================")


    def convert_pcl2dem(self, input_file, output_file, print_result=True):
    	'''
    	Function to convert .las point cloud to a raster (.tif)
    	'''
    	pip_dem = json.dumps(
	    {
	        "pipeline":[
	            {"type": "readers.las",
	             "filename": file_input
	            },
	            {
	                "filename": file_ouput # file.split('.')[0] + '_' + str(resolution) + 'm.tif',
	                "gdaldriver":"GTiff",
	                "output_type":"all",
	                "resolution":self.resolution,
	                "radius": self.radius,
	                "bounds": str(([self.raster_xmin, self.raster_xmax], [self.raster_ymin, self.raster_ymax])),
	                "type": "writers.gdal",
	                "nodata":self.nodata
	            }
	        ]
	    })
	    pipeline_realization(pip_dem, print_result=print_result)


	def convert_all_pcl2dem(self, print_result=True):
		'''
		Function to process all pcl with filter_pcl() function
		'''
		print("=======================")
		for file in self.las_pcl_flist:
			convert_pcl2dem(self, file, file[:-4] + '_' + str(self.resolution) + 'm.tif', print_result=print_result)
		print(".......................")
		print("All LAS converted to DEMs")
		print("=======================")

	def extract_ortho_value(self, input_file, output_file, print_result=True):
    	'''
    	Function to convert .las point cloud to a raster (.tif)
    	'''
    	pip_ortho = json.dumps(
	    {
	        "pipeline":[
	            {"type": "readers.las",
	             "filename": input_file
	            },
	            {
	                "type": "filters.python",
	                "script": "pdal_python_filter.py",
	                "function": "rgb2value",
	                "add_dimension": "Value",
	                "module": "anything"
	            },
	            {
	                "filename": output_file#file.split('.')[0] + '_' + str(resolution) + 'm_value.tif',
	                "gdaldriver":"GTiff",
	                "output_type":"mean",
	                "dimension" : "Value",
	                "resolution":self.resolution,
	                "radius": self.radius,
	                "bounds": str(([self.raster_xmin, self.raster_xmax], [self.raster_ymin, self.raster_ymax])),
	                "type": "writers.gdal",
	                "nodata":self.nodata
	            }
	        ]
	    })
	    pipeline_realization(pip_dem, print_result=print_result)

	def extract_all_ortho_value(self, print_result=True):
		'''
		Function to process all pcl and derive an orthophoto containing the Value (computed from RGB to HSV)
		'''

		print("=======================")
		for file in self.las_pcl_flist:
			extract_ortho_value(self, file, file[:-4] + '_' + str(self.resolution) + 'm_value.tif', print_result=print_result)
		print(".......................")
		print("All LAS converted to Value orthophoto (monochrome)")
		print("=======================")


	def custom_pipeline(self, json_pipeline):
		'''
		Function to enter a custom made pdal pipeline. Input should be a Json format pipeline following the format compatible with PDAL instructions
		'''
		return json.dumps(json_pipeline)


	def apply_custom_pipeline(self, pipeline, file_list=self.las_pcl_flist,  print_result=True):
		"""
		Function to apply a custom pipeline to 
		"""
		print("=======================")
		for file in file_list:
			pipeline_realization(pipeline, print_result)
		print(".......................")
		print("Custom pipeline applied to all files")
		print("=======================")



if __name__ == "__main__":

	# Create a pcl_class object, indication the path to the photo4d project
	my_pcl = pcl_process(project_path="path_to_project_folder")

	my_pcl.resolution = 1  # set the resolution of the final DEMs

	# Set the bounding box the Region of Interest (ROI)
	my_pcl.crop_xmin = 416100
	my_pcl.crop_xmax = 416900
	my_pcl.crop_ymin = 6715900
	my_pcl.crop_ymax = 6716700
	my_pcl.nodata = -9999

	# add path og the .ply point cloud files to the python class
	my_pcl.add_ply_pcl()

	# filter the point clouds with pdal routine, and save resulting point clouds as .las file
	my_pcl.filter_all_pcl()

	# add path of the .las files
	my_pcl.add_las_pcl()

	# conver the .las point clouds to DEMs (geotiff)
	my_pcl.convert_all_pcl2dem()

	# Extract Value orthophoto from RGB 
	my_pcl.extract_all_ortho_value()

	###########
	# Custom processing pdal pipeline



